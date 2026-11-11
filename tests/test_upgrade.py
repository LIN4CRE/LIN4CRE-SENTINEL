import asyncio
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

TEMP = tempfile.TemporaryDirectory()
os.environ['SENTINEL_DATA_DIR'] = TEMP.name
os.environ['SENTINEL_DB_PATH'] = str(Path(TEMP.name) / 'test.db')
os.environ['SENTINEL_BACKUP_DIR'] = str(Path(TEMP.name) / 'backups')
os.environ['SENTINEL_DISABLE_MONITOR'] = '1'

from fastapi.testclient import TestClient
from backend.main import app
from backend.mobile_main import app as mobile_app
from backend import mobile_auth, operations, recovery
from backend.db import connect, settings, transaction, utcnow
from backend.operation_security import authorisation, plan_hash, verify_authorisation
from host_companion import server
from host_companion.executor import ActionRejected, execute_action, execute_plan, patch_paths, validate_plan


def host_report(component='python', status='missing'):
    name = {'python': 'Python', 'ollama': 'Ollama', 'docker_engine': 'Docker Engine'}[component]
    return {
        'generated_at': utcnow(), 'host_role': 'test_environment',
        'components': [{'component': component, 'name': name, 'required': True, 'status': status, 'functional': False, 'installed_version': None if status == 'missing' else '1.0.0', 'install_method': 'winget' if component == 'python' else 'deferred'}],
        'models': [],
    }


class UpgradeAcceptanceTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.project = Path(TEMP.name) / 'project'
        cls.project.mkdir(exist_ok=True)
        recovery.ROOT = cls.project
        server.HOST_DATA = Path(TEMP.name) / 'host-data'
        server.NONCE_FILE = server.HOST_DATA / 'used-operations.json'
        server.HOST_DATA.mkdir(exist_ok=True)
        os.environ['SENTINEL_HOST_TOKEN'] = 'test-only-secret-that-is-long-enough-123456789'
        server.TOKEN_FILE = server.HOST_DATA / 'host-token'
        server.TOKEN_FILE.write_text(os.environ['SENTINEL_HOST_TOKEN'])

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        os.environ.pop('SENTINEL_HOST_TOKEN', None)

    def setUp(self):
        with transaction() as conn:
            conn.execute("INSERT INTO settings(key,value_json) VALUES('session_role','\"owner\"') ON CONFLICT(key) DO UPDATE SET value_json='\"owner\"'")
            conn.execute("INSERT INTO settings(key,value_json) VALUES('kill_switch','false') ON CONFLICT(key) DO UPDATE SET value_json='false'")

    def test_01_signed_envelope_tamper_expiry_and_permission_enforcement(self):
        plan = {'actions': [{'action': 'stop_research'}]}
        envelope = authorisation(os.environ['SENTINEL_HOST_TOKEN'], 'security-fixture', plan, lifetime_seconds=60)
        self.assertEqual(verify_authorisation(os.environ['SENTINEL_HOST_TOKEN'], envelope), (True, 'Authorised'))
        changed = {**envelope, 'plan': {'actions': [{'action': 'pull_model', 'model': 'fixture/model'}]}}
        self.assertFalse(verify_authorisation(os.environ['SENTINEL_HOST_TOKEN'], changed)[0])
        expired = authorisation(os.environ['SENTINEL_HOST_TOKEN'], 'security-fixture', plan, lifetime_seconds=-5)
        self.assertIn('expired', verify_authorisation(os.environ['SENTINEL_HOST_TOKEN'], expired)[1])
        role_changed = {**envelope, 'role': 'researcher'}
        self.assertFalse(verify_authorisation(os.environ['SENTINEL_HOST_TOKEN'], role_changed)[0])
        with self.assertRaises(ActionRejected):
            validate_plan({'actions': [{'action': 'shell', 'command': 'arbitrary'}]})
        with self.assertRaises(ActionRejected):
            validate_plan({'actions': [{'action': 'pull_model', 'model': 'model;unexpected-argument'}]})

    def test_02_host_replay_protection_and_successful_safe_action(self):
        client = TestClient(server.app)
        plan = {'actions': [{'action': 'stop_research'}]}
        envelope = authorisation(os.environ['SENTINEL_HOST_TOKEN'], 'replay-fixture', plan, lifetime_seconds=60)
        headers = {'X-Sentinel-Token': os.environ['SENTINEL_HOST_TOKEN']}
        response = client.post('/v1/execute', json=envelope, headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['success'])
        replay = client.post('/v1/execute', json=envelope, headers=headers)
        self.assertEqual(replay.status_code, 409)
        unauthenticated = client.post('/v1/execute', json=envelope)
        self.assertEqual(unauthenticated.status_code, 401)

    def test_03_server_side_role_cannot_be_elevated_by_header(self):
        item = operations.create_operation('install', 'Fixture install', 'Security test only', {'actions': [{'action': 'install_component', 'component': 'python'}]})
        with transaction() as conn:
            conn.execute("UPDATE settings SET value_json='\"researcher\"' WHERE key='session_role'")
        response = self.client.post(f"/api/operations/{item['id']}/approve", json={'confirmed': True, 'plan_hash': plan_hash(item['plan'])}, headers={'X-Sentinel-Role': 'owner'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get(f"/api/operations/{item['id']}").json()['status'], 'pending_approval')

    def test_04_changed_plan_cannot_be_approved(self):
        item = operations.create_operation('install', 'Fixture hash check', 'Security test only', {'actions': [{'action': 'install_component', 'component': 'python'}]})
        response = self.client.post(f"/api/operations/{item['id']}/approve", json={'confirmed': True, 'plan_hash': '0' * 64})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(f"/api/operations/{item['id']}").json()['status'], 'pending_approval')

    def test_05_missing_dependency_creates_plan_without_executing(self):
        with patch('backend.operations.inspect_host', new=AsyncMock(return_value=host_report())):
            response = self.client.post('/api/operations/install-missing')
        self.assertEqual(response.status_code, 200, response.text)
        item = response.json()['operation']
        self.assertEqual(item['status'], 'pending_approval')
        self.assertEqual(item['plan']['actions'], [{'action': 'install_component', 'component': 'python'}])
        self.assertIsNone(item['started_at'])

    def test_06_selected_install_checks_latest_real_state(self):
        with patch('backend.operations.inspect_host', new=AsyncMock(return_value=host_report())):
            response = self.client.post('/api/operations/install', json={'components': ['python']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['operation']['plan']['actions'][0]['component'], 'python')
        with patch('backend.operations.inspect_host', new=AsyncMock(return_value=host_report())):
            response = self.client.post('/api/operations/install', json={'components': ['not-a-component']})
        self.assertEqual(response.status_code, 422)

    async def test_07_failed_install_has_verified_recovery_and_honest_failure(self):
        item = operations.create_operation('install', 'Fixture failed installation', 'Isolated failure-path test', {'actions': [{'action': 'install_component', 'component': 'python'}]})
        failure = {'success': False, 'error': 'Fixture installer failure', 'verification': [{'component': 'python', 'verified': False}]}
        with patch('backend.operations.execute_host', new=AsyncMock(return_value=failure)):
            await operations.run_operation(item['id'])
        with connect() as conn:
            result = operations.operation(conn, item['id'])
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Fixture installer failure', result['error'])
        self.assertTrue(result['recovery_point_id'])
        self.assertEqual(recovery.verify_recovery_point(result['recovery_point_id'])['status'], 'verified')

    async def test_08_successful_update_requires_host_verification(self):
        item = operations.create_operation('update', 'Fixture successful update', 'Isolated success-path test', {'actions': [{'action': 'update_component', 'component': 'opencode', 'version': '2.0.0'}]})
        success = {'success': True, 'verified': True, 'verification': [{'component': 'opencode', 'installed_version': '2.0.0', 'functional': True, 'verified': True}]}
        with patch('backend.operations.execute_host', new=AsyncMock(return_value=success)):
            await operations.run_operation(item['id'])
        with connect() as conn:
            result = operations.operation(conn, item['id'])
        self.assertEqual(result['status'], 'succeeded')
        self.assertTrue(result['verification'][0]['verified'])

    async def test_09_failed_update_executes_only_registered_rollback(self):
        plan = {'actions': [{'action': 'update_component', 'component': 'opencode', 'version': '2.0.0', 'previous_version': '1.0.0'}], 'rollback_plan': {'actions': [{'action': 'update_component', 'component': 'opencode', 'version': '1.0.0'}]}}
        item = operations.create_operation('update', 'Fixture failed update', 'Isolated rollback test', plan, rollback_available=True)
        failure = {'success': False, 'error': 'Fixture new version failed functional verification'}
        rollback = {'success': True, 'verified': True, 'verification': [{'component': 'opencode', 'installed_version': '1.0.0', 'verified': True}]}
        mock = AsyncMock(side_effect=[failure, rollback])
        with patch('backend.operations.execute_host', new=mock):
            await operations.run_operation(item['id'])
        with connect() as conn:
            result = operations.operation(conn, item['id'])
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['result']['rollback_performed'])
        self.assertEqual(mock.await_args.args[2], plan['rollback_plan'])

    def test_10_backup_integrity_corruption_detection_and_full_restore(self):
        evidence = Path(TEMP.name) / 'evidence'
        evidence.mkdir(exist_ok=True)
        (evidence / 'fixture.txt').write_text('original evidence fixture', encoding='utf-8')
        agents = self.project / 'agents'
        agents.mkdir(parents=True, exist_ok=True)
        (agents / 'fixture.json').write_text('{"version":"original"}', encoding='utf-8')
        with transaction() as conn:
            conn.execute("INSERT INTO settings(key,value_json) VALUES('restore_fixture','\"before\"') ON CONFLICT(key) DO UPDATE SET value_json='\"before\"'")
        point = recovery.create_recovery_point('Isolated full restore fixture', 'test')
        restore_operation = operations.create_operation('restore', 'Fixture restore', 'Isolated restore test', {'recovery_point_id': point['id'], 'components': ['database', 'files', 'config']}, risk='data_restore', requires_approval=True)
        operations.set_operation(restore_operation['id'], status='running')
        (evidence / 'fixture.txt').write_text('changed after backup', encoding='utf-8')
        (evidence / 'extra-after-backup.txt').write_text('must not survive exact restoration', encoding='utf-8')
        with transaction() as conn:
            conn.execute("UPDATE settings SET value_json='\"after\"' WHERE key='restore_fixture'")
            audit_before = conn.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
        with connect() as conn:
            result = asyncio.run(operations.run_operation(restore_operation['id']))
        with connect() as conn:
            restored = operations.operation(conn, restore_operation['id'])
            self.assertEqual(restored['status'], 'succeeded', restored.get('error'))
            self.assertEqual(settings(conn)['restore_fixture'], 'before')
            audit_after = conn.execute('SELECT COUNT(*) FROM audit_log').fetchone()[0]
        self.assertEqual((evidence / 'fixture.txt').read_text(encoding='utf-8'), 'original evidence fixture')
        self.assertFalse((evidence / 'extra-after-backup.txt').exists())
        self.assertEqual(json.loads((agents / 'fixture.json').read_text(encoding='utf-8'))['version'], 'original')
        self.assertGreaterEqual(audit_after, audit_before)
        self.assertEqual(recovery.verify_recovery_point(point['id'])['status'], 'verified')

    def test_11_corrupted_backup_cannot_be_restored(self):
        point = recovery.create_recovery_point('Isolated corruption fixture', 'test')
        target = Path(point['root_path']) / 'sentinel.db'
        with target.open('r+b') as handle:
            handle.seek(100)
            handle.write(b'CORRUPTED-FIXTURE')
        verification = recovery.verify_recovery_point(point['id'])
        self.assertEqual(verification['status'], 'corrupted')
        with self.assertRaises(RuntimeError):
            recovery.restore_recovery_point(point['id'])

    async def test_12_emergency_stop_revokes_permissions(self):
        programme_id = 'emergency-fixture-programme'
        with transaction() as conn:
            conn.execute("INSERT OR REPLACE INTO programmes(id,name,platform,eligibility_status,created_at,updated_at) VALUES(?,?,?,?,?,?)", (programme_id, 'Security fixture — not production data', 'Other', 'rejected', utcnow(), utcnow()))
            conn.execute("INSERT INTO approvals(id,programme_id,assets_json,methods_json,rate_limit,expires_at,scope_hash,status,requested_at) VALUES(?,?,?,?,?,?,?,?,?)", ('emergency-fixture-approval', programme_id, '[]', '[]', 0, '2099-01-01', 'fixture', 'approved', utcnow()))
        item = operations.create_operation('emergency_stop', 'Fixture emergency stop', 'Isolated emergency test', {'actions': [{'action': 'stop_research'}]}, requires_approval=False)
        with patch('backend.operations.execute_host', new=AsyncMock(return_value={'success': True, 'stopped_pids': []})):
            await operations.run_operation(item['id'])
        with connect() as conn:
            self.assertTrue(settings(conn)['kill_switch'])
            self.assertEqual(conn.execute("SELECT status FROM approvals WHERE id='emergency-fixture-approval'").fetchone()[0], 'revoked')

    def test_13_natural_language_reports_real_empty_ledger_and_unknown_capability(self):
        response = self.client.post('/api/assistant/message', json={'text': 'How much did I make?'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('No Data Available', response.json()['message']['content'])
        response = self.client.post('/api/assistant/message', json={'text': 'Please do something no registered operation supports'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('safe registered action', response.json()['message']['content'])

    def test_14_installation_report_contains_observed_not_inferred_results(self):
        unavailable = operations.HostUnavailable('Fixture companion unavailable')
        with patch('backend.operations.inspect_host', new=AsyncMock(side_effect=unavailable)):
            response = self.client.get('/api/operations/installation-report')
        self.assertEqual(response.status_code, 200, response.text)
        report = response.json()
        self.assertFalse(report['inspection']['host']['connected'])
        self.assertIsNone(report['inspection']['host']['report'])
        self.assertFalse(report['credential_status']['credentials_included'])

    def test_15_code_patch_backup_verification_and_reverse(self):
        target = self.project / 'backend' / 'fixture.py'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('VALUE = 1\n', encoding='utf-8')
        diff = '''diff --git a/backend/fixture.py b/backend/fixture.py
--- a/backend/fixture.py
+++ b/backend/fixture.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
'''
        self.assertEqual(patch_paths(diff), ['backend/fixture.py'])
        result = execute_action({'action': 'apply_patch', 'patch': diff}, self.project)
        self.assertTrue(result['success'], result)
        self.assertTrue(result['verified'])
        self.assertEqual(target.read_text(encoding='utf-8'), 'VALUE = 2\n')
        self.assertTrue((Path(result['backup_path']) / 'manifest.json').exists())
        reverse = execute_action({'action': 'reverse_patch', 'patch': diff}, self.project)
        self.assertTrue(reverse['success'], reverse)
        self.assertEqual(target.read_text(encoding='utf-8'), 'VALUE = 1\n')
        with self.assertRaises(ActionRejected):
            patch_paths(diff.replace('backend/fixture.py', 'backend/operation_security.py'))
        with self.assertRaises(ActionRejected):
            patch_paths(diff.replace('backend/fixture.py', '../outside.py'))

    def test_16_code_change_without_verified_model_is_unavailable(self):
        with transaction() as conn:
            conn.execute("INSERT INTO settings(key,value_json) VALUES('ollama_model','\"\"') ON CONFLICT(key) DO UPDATE SET value_json='\"\"'")
        response = self.client.post('/api/assistant/message', json={'text': 'Make a code change to the assistant colour'})
        self.assertEqual(response.status_code, 409)
        self.assertIn('verified local Ollama model', response.json()['detail'])


if __name__ == '__main__':
    unittest.main()


class MobileCompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(mobile_app)
        cls.client.__enter__()
        cls.original_token_path = mobile_auth.TOKEN_HASH_FILE
        cls.token_path = Path(TEMP.name) / 'mobile-token.sha256'
        mobile_auth.TOKEN_HASH_FILE = cls.token_path
        cls.token = 'mobile-test-token-32-characters-minimum-123456789'
        cls.token_path.write_text(hashlib.sha256(cls.token.encode()).hexdigest(), encoding='ascii')

    @classmethod
    def tearDownClass(cls):
        mobile_auth.TOKEN_HASH_FILE = cls.original_token_path
        cls.client.__exit__(None, None, None)

    def test_mobile_api_requires_token_and_does_not_expose_core_routes(self):
        self.assertEqual(self.client.get('/api/mobile/v1/overview').status_code, 401)
        self.assertEqual(self.client.get('/api/mobile/v1/overview', headers={'Authorization': 'Bearer wrong'}).status_code, 401)
        self.assertEqual(self.client.post('/api/mobile/v1/programmes', headers={'Authorization': f'Bearer {self.token}'}).status_code, 404)
        response = self.client.get('/api/mobile/v1/overview', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()['read_only'])
        self.assertEqual(response.headers.get('cache-control'), 'no-store')

    def test_mobile_api_returns_only_safe_read_models(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        overview = self.client.get('/api/mobile/v1/overview', headers=headers)
        self.assertEqual(overview.status_code, 200)
        self.assertIn('counts', overview.json())
        programmes = self.client.get('/api/mobile/v1/programmes', headers=headers)
        self.assertEqual(programmes.status_code, 200)
        for row in programmes.json():
            self.assertNotIn('notes', row)
            self.assertNotIn('assets_json', row)
        approvals = self.client.get('/api/mobile/v1/approvals', headers=headers)
        self.assertEqual(approvals.status_code, 200)
