import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEMP = tempfile.TemporaryDirectory()
os.environ['SENTINEL_DATA_DIR'] = TEMP.name
os.environ['SENTINEL_DB_PATH'] = str(Path(TEMP.name) / 'test.db')
os.environ['SENTINEL_BACKUP_DIR'] = str(Path(TEMP.name) / 'backups')
os.environ['SENTINEL_DISABLE_MONITOR'] = '1'

from host_companion import inspector


def version_result(output: str, exit_code: int = 0) -> dict:
    return {
        'command': ['opencode', '--version'],
        'exit_code': exit_code,
        'stdout': output,
        'stderr': '',
        'timed_out': False,
        'started_at': '2026-11-12T00:00:00+00:00',
        'finished_at': '2026-11-12T00:00:01+00:00',
    }


class OpenCodeDetectionTests(unittest.TestCase):
    """OpenCode must be found wherever it is really installed."""

    def setUp(self) -> None:
        self.root = Path(TEMP.name) / f'opencode-{self._testMethodName}'
        self.local = self.root / 'local'
        self.roaming = self.root / 'roaming'
        self.local.mkdir(parents=True, exist_ok=True)
        self.roaming.mkdir(parents=True, exist_ok=True)
        self.environment = patch.dict(
            os.environ,
            {'LOCALAPPDATA': str(self.local), 'APPDATA': str(self.roaming)},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        which = patch.object(inspector.shutil, 'which', lambda name: None)
        which.start()
        self.addCleanup(which.stop)

    def _desktop_application(self) -> Path:
        folder = self.local / 'Programs' / 'ai.opencode.desktop'
        folder.mkdir(parents=True, exist_ok=True)
        application = folder / 'OpenCode.exe'
        application.write_bytes(b'MZ')
        return application

    def _desktop_command_line(self) -> Path:
        folder = self.roaming / 'ai.opencode.desktop' / 'cli' / '1.2.3-x64'
        folder.mkdir(parents=True, exist_ok=True)
        command = folder / 'opencode-cli.exe'
        command.write_bytes(b'MZ')
        return command

    def test_desktop_command_line_build_is_detected(self) -> None:
        command = self._desktop_command_line()
        with patch.object(inspector, 'run_command', return_value=version_result('opencode v1.2.3')):
            component = inspector.opencode_component()
        self.assertEqual(component['status'], 'healthy')
        self.assertEqual(component['installed_version'], '1.2.3')
        self.assertTrue(component['functional'])
        self.assertEqual(component['location'], str(command))
        self.assertEqual(component['details']['install_kind'], 'desktop command line')

    def test_desktop_application_is_detected_without_being_started(self) -> None:
        application = self._desktop_application()
        with patch.object(inspector, 'windows_file_version', return_value='2.2.5.0'):
            component = inspector.opencode_component()
        self.assertEqual(component['status'], 'healthy')
        self.assertEqual(component['installed_version'], '2.2.5.0')
        self.assertTrue(component['functional'])
        self.assertEqual(component['location'], str(application))
        self.assertEqual(component['details']['install_kind'], 'desktop application')

    def test_command_line_on_path_is_detected(self) -> None:
        command = Path(TEMP.name) / 'opencode-on-path.exe'
        command.write_bytes(b'MZ')
        with patch.object(inspector.shutil, 'which', lambda name: str(command) if name == 'opencode' else None):
            with patch.object(inspector, 'run_command', return_value=version_result('opencode v3.4.5')):
                component = inspector.opencode_component()
        self.assertEqual(component['status'], 'healthy')
        self.assertEqual(component['installed_version'], '3.4.5')
        self.assertEqual(component['details']['install_kind'], 'command line on PATH')

    def test_absent_installation_is_reported_honestly(self) -> None:
        component = inspector.opencode_component()
        self.assertEqual(component['status'], 'not_configured')
        self.assertFalse(component['functional'])
        self.assertIsNone(component['installed_version'])
        self.assertIn('not found', component['error'])

    def test_configuration_folder_is_recorded(self) -> None:
        self._desktop_command_line()
        configuration = self.root / '.config' / 'opencode'
        configuration.mkdir(parents=True, exist_ok=True)
        with patch.object(inspector, 'run_command', return_value=version_result('opencode v1.2.3')):
            with patch.object(inspector.Path, 'home', classmethod(lambda cls: self.root)):
                component = inspector.opencode_component()
        self.assertTrue(component['details']['configuration'])
        self.assertTrue(any(entry['path'].endswith('opencode') for entry in component['details']['configuration']))


if __name__ == '__main__':
    unittest.main()
