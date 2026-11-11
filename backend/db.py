from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("SENTINEL_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.getenv("SENTINEL_DB_PATH", DATA_DIR / "sentinel.db"))
BACKUP_DIR = Path(os.getenv("SENTINEL_BACKUP_DIR", DATA_DIR / "backups"))

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS programmes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    handle TEXT NOT NULL DEFAULT '',
    programme_url TEXT NOT NULL DEFAULT '',
    policy_url TEXT NOT NULL DEFAULT '',
    reward_criteria_url TEXT NOT NULL DEFAULT '',
    currency TEXT NOT NULL DEFAULT 'GBP',
    reward_min REAL NOT NULL DEFAULT 0,
    reward_max REAL NOT NULL DEFAULT 0,
    realistic_reward REAL,
    assets_json TEXT NOT NULL DEFAULT '[]',
    automation_policy TEXT NOT NULL DEFAULT 'unspecified',
    ai_policy TEXT NOT NULL DEFAULT 'unspecified',
    payout_process TEXT NOT NULL DEFAULT 'unspecified',
    source_checked_at TEXT NOT NULL DEFAULT '',
    probability_valid REAL,
    competition_risk REAL,
    estimated_hours REAL,
    notes TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'manual',
    eligibility_status TEXT NOT NULL,
    eligibility_reasons_json TEXT NOT NULL DEFAULT '[]',
    score REAL,
    expected_value_per_hour REAL,
    score_breakdown_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    programme_id TEXT NOT NULL REFERENCES programmes(id),
    assets_json TEXT NOT NULL,
    methods_json TEXT NOT NULL,
    rate_limit INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    scope_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TEXT NOT NULL,
    decided_at TEXT,
    decision_note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    programme_id TEXT NOT NULL REFERENCES programmes(id),
    title TEXT NOT NULL,
    asset TEXT NOT NULL,
    vulnerability_class TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'unrated',
    status TEXT NOT NULL DEFAULT 'draft',
    summary TEXT NOT NULL DEFAULT '',
    reproduction_steps TEXT NOT NULL DEFAULT '',
    impact TEXT NOT NULL DEFAULT '',
    evidence TEXT NOT NULL DEFAULT '',
    remediation TEXT NOT NULL DEFAULT '',
    ai_disclosure TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    validated_at TEXT,
    validated_by TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL UNIQUE REFERENCES findings(id),
    platform_report_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    content_md TEXT NOT NULL,
    submitted_at TEXT,
    decision_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL REFERENCES reports(id),
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL,
    awarded_at TEXT,
    paid_at TEXT,
    reference TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TRIGGER IF NOT EXISTS audit_log_no_update
BEFORE UPDATE ON audit_log BEGIN
    SELECT RAISE(ABORT, 'audit log is append-only');
END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
BEFORE DELETE ON audit_log BEGIN
    SELECT RAISE(ABORT, 'audit log is append-only');
END;

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pc_audits (
    id TEXT PRIMARY KEY,
    imported_at TEXT NOT NULL,
    source_name TEXT NOT NULL,
    data_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dependencies (
    id TEXT PRIMARY KEY,
    component TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    required INTEGER NOT NULL DEFAULT 1,
    installed_version TEXT,
    latest_compatible_version TEXT,
    location TEXT,
    source_repository TEXT NOT NULL DEFAULT '',
    licence TEXT NOT NULL DEFAULT 'Unknown',
    status TEXT NOT NULL DEFAULT 'never_checked',
    last_checked TEXT,
    update_available INTEGER,
    update_category TEXT,
    release_url TEXT,
    release_notes TEXT,
    download_size_bytes INTEGER,
    new_cost_detected INTEGER,
    details_json TEXT NOT NULL DEFAULT '{}',
    relationships_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS operations (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    risk TEXT NOT NULL DEFAULT 'read_only',
    status TEXT NOT NULL,
    requires_approval INTEGER NOT NULL DEFAULT 0,
    approval_role TEXT NOT NULL DEFAULT 'owner',
    plan_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT,
    verification_json TEXT,
    created_at TEXT NOT NULL,
    approved_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    recovery_point_id TEXT,
    rollback_available INTEGER NOT NULL DEFAULT 0,
    retry_of TEXT
);

CREATE TABLE IF NOT EXISTS recovery_points (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    label TEXT NOT NULL,
    kind TEXT NOT NULL,
    root_path TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    status TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    includes_json TEXT NOT NULL DEFAULT '[]',
    source_version TEXT NOT NULL,
    last_known_good INTEGER NOT NULL DEFAULT 0,
    restored_at TEXT
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    operation_id TEXT,
    status TEXT NOT NULL DEFAULT 'complete',
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS monitor_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    summary_json TEXT NOT NULL DEFAULT '{}'
);
"""

DEFAULT_SETTINGS = {
    "ai_strategy": "hybrid",
    "opportunity_scope": "cash",
    "autonomy": "approval",
    "kill_switch": False,
    "testing_engine_enabled": False,
    "auto_submission_enabled": False,
    "external_ai_enabled": False,
    "external_provider": "none",
    "monthly_spend_cap_gbp": 0,
    "ollama_url": "http://host.docker.internal:11434",
    "ollama_model": "",
    "researcher_name": "",
    "setup_backup_verified": False,
    "host_companion_url": "http://host.docker.internal:8765",
    "monitor_interval_minutes": 60,
    "automatic_monitoring": True,
    "last_monitor_run": "",
    "session_role": "owner",
    "setup_completed": False,
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClosingConnection(sqlite3.Connection):
    """SQLite's normal context manager commits but does not close; SENTINEL's does both."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialise() -> None:
    with transaction() as conn:
        conn.executescript(SCHEMA)
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value_json) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
        existing = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        if existing == 0:
            audit(
                conn,
                "system.initialised",
                "system",
                message="SENTINEL local core initialised with cash-only and human-approval safeguards.",
                details={"database": str(DB_PATH), "testing_engine": "disabled"},
            )


def audit(
    conn: sqlite3.Connection,
    event_type: str,
    entity_type: str,
    entity_id: str = "",
    message: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """INSERT INTO audit_log(timestamp, event_type, entity_type, entity_id, message, details_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (utcnow(), event_type, entity_type, entity_id, message, json.dumps(details or {})),
    )


def settings(conn: sqlite3.Connection) -> dict[str, Any]:
    return {row["key"]: json.loads(row["value_json"]) for row in conn.execute("SELECT * FROM settings")}


def decode(row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    for key in list(item):
        if key.endswith("_json"):
            target = key[:-5]
            try:
                item[target] = json.loads(item[key])
            except (TypeError, json.JSONDecodeError):
                item[target] = None
            del item[key]
    return item


def decode_many(rows: Any) -> list[dict[str, Any]]:
    return [decode(row) for row in rows]  # type: ignore[misc]
