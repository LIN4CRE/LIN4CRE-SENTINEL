import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

TEMP = tempfile.TemporaryDirectory()
if "backend.db" in sys.modules:
    # Discovery shares one imported application; keep raw connection fixtures on
    # the same isolated database instead of redirecting only the environment.
    from backend.db import BACKUP_DIR, DATA_DIR, DB_PATH
    os.environ["SENTINEL_DATA_DIR"] = str(DATA_DIR)
    os.environ["SENTINEL_DB_PATH"] = str(DB_PATH)
    os.environ["SENTINEL_BACKUP_DIR"] = str(BACKUP_DIR)
else:
    os.environ["SENTINEL_DATA_DIR"] = TEMP.name
    os.environ["SENTINEL_DB_PATH"] = str(Path(TEMP.name) / "test.db")
    os.environ["SENTINEL_BACKUP_DIR"] = str(Path(TEMP.name) / "backups")

from fastapi.testclient import TestClient
from backend.main import app
from backend.scoring import evaluate


def programme(**changes):
    data = {
        "name": "Researcher verified programme",
        "platform": "HackerOne",
        "handle": "verified-handle",
        "programme_url": "https://example.org/programme",
        "policy_url": "https://example.org/policy",
        "reward_criteria_url": "https://example.org/rewards",
        "currency": "GBP",
        "reward_min": 100,
        "reward_max": 5000,
        "realistic_reward": 1000,
        "assets": ["app.example.org"],
        "automation_policy": "approval_required",
        "ai_policy": "human_required",
        "payout_process": "documented",
        "source_checked_at": "2026-11-11",
        "probability_valid": 0.2,
        "competition_risk": 0.25,
        "estimated_hours": 10,
        "notes": "Test fixture exercises validation logic; never inserted into application data.",
    }
    data.update(changes)
    return data


class ScoringTests(unittest.TestCase):
    def test_cash_only_rejection(self):
        result = evaluate(programme(reward_max=0))
        self.assertEqual(result["eligibility_status"], "rejected")
        self.assertIsNone(result["score"])

    def test_unspecified_permission_requires_review(self):
        result = evaluate(programme(automation_policy="unspecified"))
        self.assertEqual(result["eligibility_status"], "review_required")

    def test_score_is_deterministic_and_explainable(self):
        result = evaluate(programme())
        self.assertEqual(result["eligibility_status"], "eligible")
        self.assertEqual(len(result["score_breakdown"]), 6)
        self.assertAlmostEqual(result["expected_value_per_hour"], 15.0)


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_complete_human_controlled_workflow(self):
        created = self.client.post("/api/programmes", json=programme())
        self.assertEqual(created.status_code, 201, created.text)
        programme_id = created.json()["id"]
        self.assertEqual(created.json()["eligibility_status"], "eligible")

        out_of_scope = self.client.post(f"/api/programmes/{programme_id}/approvals", json={
            "assets": ["other.example.org"], "methods": ["manual_browser"], "rate_limit": 1,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        })
        self.assertEqual(out_of_scope.status_code, 422)

        approval = self.client.post(f"/api/programmes/{programme_id}/approvals", json={
            "assets": ["app.example.org"], "methods": ["manual_browser"], "rate_limit": 1,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        })
        self.assertEqual(approval.status_code, 201, approval.text)
        approval_id = approval.json()["id"]
        self.assertEqual(approval.json()["status"], "pending")

        finding_without_approval = self.client.post("/api/findings", json={
            "programme_id": programme_id, "title": "Observed test fixture", "asset": "app.example.org",
            "vulnerability_class": "Access control", "summary": "Actual observation placeholder in isolated test only",
        })
        self.assertEqual(finding_without_approval.status_code, 422)

        decided = self.client.post(f"/api/approvals/{approval_id}/decision", json={"decision": "approved", "note": "Scope checked in isolated workflow test"})
        self.assertEqual(decided.status_code, 200, decided.text)

        finding = self.client.post("/api/findings", json={
            "programme_id": programme_id, "title": "Observed test fixture", "asset": "app.example.org",
            "vulnerability_class": "Access control", "summary": "Isolated test data",
        })
        self.assertEqual(finding.status_code, 201, finding.text)
        finding_id = finding.json()["id"]
        incomplete = self.client.post(f"/api/findings/{finding_id}/validate", json={"researcher_name": "Test Researcher", "confirmed": True})
        self.assertEqual(incomplete.status_code, 422)

        updated = self.client.patch(f"/api/findings/{finding_id}", json={
            "reproduction_steps": "1. Isolated test step", "impact": "Isolated demonstrated impact",
            "evidence": "Isolated test evidence", "ai_disclosure": "No AI used in test fixture",
        })
        self.assertEqual(updated.status_code, 200, updated.text)
        validated = self.client.post(f"/api/findings/{finding_id}/validate", json={"researcher_name": "Test Researcher", "confirmed": True})
        self.assertEqual(validated.status_code, 200, validated.text)

        report = self.client.post(f"/api/findings/{finding_id}/report")
        self.assertEqual(report.status_code, 201, report.text)
        report_id = report.json()["id"]
        submitted = self.client.patch(f"/api/reports/{report_id}", json={"status": "submitted", "platform_report_id": "TEST-EXTERNAL-ID", "human_confirmation": False})
        self.assertEqual(submitted.status_code, 422)
        submitted = self.client.patch(f"/api/reports/{report_id}", json={"status": "submitted", "platform_report_id": "TEST-EXTERNAL-ID", "human_confirmation": True})
        self.assertEqual(submitted.status_code, 200, submitted.text)

        payment_before_acceptance = self.client.post(f"/api/reports/{report_id}/payments", json={"amount": 100, "currency": "GBP", "status": "paid", "paid_at": "2026-11-11"})
        self.assertEqual(payment_before_acceptance.status_code, 422)
        accepted = self.client.patch(f"/api/reports/{report_id}", json={"status": "accepted", "platform_report_id": "TEST-EXTERNAL-ID", "human_confirmation": True})
        self.assertEqual(accepted.status_code, 200)
        paid_without_date = self.client.post(f"/api/reports/{report_id}/payments", json={"amount": 100, "currency": "GBP", "status": "paid"})
        self.assertEqual(paid_without_date.status_code, 422)
        paid = self.client.post(f"/api/reports/{report_id}/payments", json={"amount": 100, "currency": "GBP", "status": "paid", "paid_at": "2026-11-11"})
        self.assertEqual(paid.status_code, 201, paid.text)

        stopped = self.client.patch("/api/settings", json={"kill_switch": True})
        self.assertEqual(stopped.status_code, 200)
        self.assertTrue(stopped.json()["kill_switch"])
        self.assertEqual(self.client.get(f"/api/programmes/{programme_id}").json()["approvals"][0]["status"], "revoked")

    def test_audit_log_cannot_be_modified(self):
        import sqlite3
        connection = sqlite3.connect(os.environ["SENTINEL_DB_PATH"])
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM audit_log")
        connection.close()


if __name__ == "__main__":
    unittest.main()
