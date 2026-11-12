from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .db import BACKUP_DIR, DATA_DIR, DB_PATH, ROOT, audit, connect, decode, decode_many, transaction, utcnow

VERSION = "0.2.1"
NON_SECRET_CONFIG = ("opencode.json", "opencode.jsonc", "AGENTS.md")
DATA_FOLDERS = ("evidence", "reports", "research", "logs", "scope-rules", "agents", "intelligence")


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def manifest_hash(manifest: dict[str, Any]) -> str:
    content = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    for path in source.rglob("*"):
        if path.is_symlink() or path.is_dir() or any(part in ("node_modules", "__pycache__", ".git") for part in path.parts):
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def recovery_root(point_id: str) -> Path:
    return BACKUP_DIR / "recovery" / point_id


def create_recovery_point(label: str, kind: str = "manual") -> dict[str, Any]:
    point_id = f"{utcnow()[:10].replace('-', '')}-{uuid.uuid4().hex[:12]}"
    final_root = recovery_root(point_id)
    temporary = final_root.with_name(f".building-{point_id}")
    temporary.mkdir(parents=True, exist_ok=False)
    includes = ["database", "settings", "audit_log"]
    try:
        source = connect()
        target = sqlite3.connect(temporary / "sentinel.db")
        try:
            source.backup(target)
            integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"Database backup integrity failed: {integrity}")
            target.commit()
        finally:
            target.close()
            source.close()

        files_root = temporary / "files"
        for folder in DATA_FOLDERS:
            source_folder = DATA_DIR / folder
            if source_folder.exists():
                copy_tree(source_folder, files_root / "data" / folder)
                includes.append(f"data/{folder}")
        for folder in ("agents", "config"):
            source_folder = ROOT / folder
            if source_folder.exists():
                copy_tree(source_folder, files_root / folder)
                includes.append(folder)
        for filename in NON_SECRET_CONFIG:
            source_file = ROOT / filename
            if source_file.exists():
                target_file = files_root / filename
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                includes.append(filename)

        file_records = []
        for path in sorted(temporary.rglob("*")):
            if path.is_file() and path.name != "manifest.json":
                file_records.append({"path": str(path.relative_to(temporary)), "bytes": path.stat().st_size, "sha256": digest(path)})
        manifest = {
            "schema": "lin4cre.sentinel.recovery/v1",
            "id": point_id,
            "created_at": utcnow(),
            "label": label,
            "kind": kind,
            "source_version": VERSION,
            "includes": includes,
            "credentials_included": False,
            "credential_note": "API keys and host tokens are deliberately excluded. Re-authorise credentials through the secured setup flow after recovery.",
            "database_integrity": "ok",
            "files": file_records,
            "size_bytes": sum(record["bytes"] for record in file_records),
        }
        manifest["manifest_sha256"] = manifest_hash(manifest)
        manifest_path = temporary / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        os.replace(temporary, final_root)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    with transaction() as conn:
        conn.execute(
            """INSERT INTO recovery_points(id,created_at,label,kind,root_path,manifest_path,status,sha256,size_bytes,includes_json,source_version,last_known_good)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,1)""",
            (point_id, manifest["created_at"], label, kind, str(final_root), str(final_root / "manifest.json"), "verified", manifest["manifest_sha256"], manifest["size_bytes"], json.dumps(includes), VERSION),
        )
        audit(conn, "recovery.created", "recovery", point_id, f"Recovery point created and verified: {label}", {"bytes": manifest["size_bytes"], "includes": includes, "credentials_included": False})
    return {**manifest, "root_path": str(final_root), "manifest_path": str(final_root / "manifest.json"), "status": "verified", "last_known_good": 1}


def read_manifest(point_id: str) -> tuple[Path, dict[str, Any]]:
    root = recovery_root(point_id)
    path = root / "manifest.json"
    if not path.exists():
        raise FileNotFoundError("Recovery manifest not found")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("id") != point_id or manifest.get("schema") != "lin4cre.sentinel.recovery/v1":
        raise ValueError("Recovery manifest identity or schema is invalid")
    return root, manifest


def verify_recovery_point(point_id: str) -> dict[str, Any]:
    started = utcnow()
    try:
        root, manifest = read_manifest(point_id)
        expected_manifest_hash = manifest.get("manifest_sha256")
        if expected_manifest_hash != manifest_hash(manifest):
            raise ValueError("Recovery manifest hash does not match its contents")
        errors = []
        for record in manifest["files"]:
            relative = Path(record["path"])
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"Unsafe manifest path: {record['path']}")
                continue
            path = root / relative
            if path.is_symlink():
                errors.append(f"Symbolic links are not valid recovery content: {record['path']}")
            elif not path.exists():
                errors.append(f"Missing: {record['path']}")
            elif path.stat().st_size != record["bytes"]:
                errors.append(f"Size changed: {record['path']}")
            elif digest(path) != record["sha256"]:
                errors.append(f"Hash changed: {record['path']}")
        database = root / "sentinel.db"
        if database.exists():
            connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            connection.close()
            if integrity != "ok":
                errors.append(f"Database integrity: {integrity}")
            if foreign_keys:
                errors.append(f"Database foreign-key violations: {len(foreign_keys)}")
        else:
            errors.append("Missing: sentinel.db")
        status = "verified" if not errors else "corrupted"
        result = {"id": point_id, "status": status, "verified_at": utcnow(), "started_at": started, "errors": errors, "file_count": len(manifest["files"]), "size_bytes": manifest["size_bytes"]}
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
        result = {"id": point_id, "status": "corrupted", "verified_at": utcnow(), "started_at": started, "errors": [str(exc)], "file_count": 0, "size_bytes": 0}
    with transaction() as conn:
        exists = conn.execute("SELECT id FROM recovery_points WHERE id=?", (point_id,)).fetchone()
        if exists:
            conn.execute("UPDATE recovery_points SET status=?, last_known_good=? WHERE id=?", (result["status"], 1 if result["status"] == "verified" else 0, point_id))
        audit(conn, "recovery.verified", "recovery", point_id, f"Recovery verification {result['status']}", {"errors": result["errors"]})
    return result


def sync_recovery_catalog() -> None:
    directory = BACKUP_DIR / "recovery"
    if not directory.exists():
        return
    with transaction() as conn:
        for path in directory.glob("*/manifest.json"):
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
                point_id = manifest["id"]
                if conn.execute("SELECT id FROM recovery_points WHERE id=?", (point_id,)).fetchone():
                    continue
                conn.execute(
                    "INSERT INTO recovery_points(id,created_at,label,kind,root_path,manifest_path,status,sha256,size_bytes,includes_json,source_version,last_known_good) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (point_id, manifest["created_at"], manifest["label"], manifest["kind"], str(path.parent), str(path), "not_verified", manifest["manifest_sha256"], manifest["size_bytes"], json.dumps(manifest["includes"]), manifest["source_version"], 0),
                )
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue


def selected_paths(root: Path, components: list[str]) -> list[tuple[Path, Path]]:
    targets: list[tuple[Path, Path]] = []
    if "files" in components:
        targets.extend((root / "files" / "data" / folder, DATA_DIR / folder) for folder in DATA_FOLDERS)
    if "config" in components:
        targets.extend((root / "files" / folder, ROOT / folder) for folder in ("agents", "config"))
        targets.extend((root / "files" / filename, ROOT / filename) for filename in NON_SECRET_CONFIG)
    return targets


def replace_path(source: Path, target: Path) -> None:
    """Replace a selected tree exactly; the caller has already made a safety point."""
    stage = target.with_name(f".{target.name}.restoring-{uuid.uuid4().hex[:10]}")
    try:
        if source.is_dir():
            copy_tree(source, stage)
        elif source.is_file() and not source.is_symlink():
            stage.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, stage)
        if target.is_symlink() or (target.exists() and not target.is_dir()):
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        if stage.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage, target)
    finally:
        if stage.is_dir():
            shutil.rmtree(stage)
        elif stage.exists():
            stage.unlink()


def restore_selected_files(root: Path, components: list[str]) -> None:
    for source, target in selected_paths(root, components):
        replace_path(source, target)


def verify_selected_files(root: Path, components: list[str]) -> list[str]:
    errors: list[str] = []
    for source, target in selected_paths(root, components):
        expected = {str(path.relative_to(source)): path for path in source.rglob("*") if path.is_file() and not path.is_symlink()} if source.is_dir() else ({source.name: source} if source.is_file() else {})
        actual = {str(path.relative_to(target)): path for path in target.rglob("*") if path.is_file() and not path.is_symlink()} if target.is_dir() else ({target.name: target} if target.is_file() else {})
        if set(expected) != set(actual):
            errors.append(f"File set differs for {target}: missing={sorted(set(expected)-set(actual))}, unexpected={sorted(set(actual)-set(expected))}")
        for relative in set(expected) & set(actual):
            if digest(expected[relative]) != digest(actual[relative]):
                errors.append(f"Restored content hash differs: {target}/{relative}")
    return errors


def reconcile_restored_database(previous: Path) -> None:
    """Retain append-only/security history without retaining reverted business records."""
    old = sqlite3.connect(previous)
    old.row_factory = sqlite3.Row
    new = connect()
    try:
        for table in ("audit_log", "operations", "recovery_points"):
            columns = [row[1] for row in old.execute(f"PRAGMA table_info({table})")]
            if not columns:
                continue
            placeholders = ",".join("?" for _ in columns)
            statement = f"INSERT OR IGNORE INTO {table}({','.join(columns)}) VALUES({placeholders})"
            rows = old.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                new.execute(statement, [row[column] for column in columns])
        old_kill_switch = old.execute("SELECT value_json FROM settings WHERE key='kill_switch'").fetchone()
        if old_kill_switch and json.loads(old_kill_switch[0]):
            new.execute("INSERT INTO settings(key,value_json) VALUES('kill_switch','true') ON CONFLICT(key) DO UPDATE SET value_json='true'")
        new.execute("UPDATE approvals SET status='revoked',decided_at=?,decision_note='Revoked during recovery; fresh human authorisation is required' WHERE status IN ('pending','approved')", (utcnow(),))
        new.commit()
    finally:
        new.close()
        old.close()


def restore_recovery_point(point_id: str, components: list[str] | None = None) -> dict[str, Any]:
    verification = verify_recovery_point(point_id)
    if verification["status"] != "verified":
        raise RuntimeError("Restore blocked: recovery point is corrupted or unavailable")
    components = components or ["database", "files", "config"]
    if not set(components).issubset({"database", "files", "config"}):
        raise ValueError("Unknown restore component")
    root, manifest = read_manifest(point_id)
    safety = create_recovery_point(f"Automatic safety point before restoring {point_id}", "pre_restore")
    rollback_root = recovery_root(safety["id"])
    database_replaced = False
    previous_database = DATA_DIR / f"sentinel.pre-restore-{uuid.uuid4().hex[:8]}.db"
    temporary_database = DATA_DIR / f"sentinel.restoring-{uuid.uuid4().hex[:8]}.db"
    try:
        if "database" in components:
            source = sqlite3.connect(root / "sentinel.db")
            target = sqlite3.connect(temporary_database)
            try:
                source.backup(target)
                integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise RuntimeError("Staged restore database failed integrity check")
                target.commit()
            finally:
                target.close()
                source.close()
            live = connect()
            try:
                live.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            finally:
                live.close()
            os.replace(DB_PATH, previous_database)
            os.replace(temporary_database, DB_PATH)
            database_replaced = True
            # Old WAL/SHM files belong to the pre-restore database and must not be replayed into the restored snapshot.
            for suffix in ("-wal", "-shm"):
                sidecar = Path(str(DB_PATH) + suffix)
                if sidecar.exists():
                    os.replace(sidecar, rollback_root / f"pre-restore-sentinel.db{suffix}")
            reconcile_restored_database(previous_database)
        if "files" in components or "config" in components:
            restore_selected_files(root, components)

        connection = connect()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        connection.close()
        required = {"programmes", "findings", "reports", "audit_log", "settings", "recovery_points", "operations"}
        file_errors = verify_selected_files(root, components) if "files" in components or "config" in components else []
        if integrity != "ok" or not required.issubset(tables) or file_errors:
            raise RuntimeError("Restored state did not pass post-restore verification: " + "; ".join(file_errors) if file_errors else "Restored database did not pass post-restore verification")
        with transaction() as conn:
            conn.execute("UPDATE recovery_points SET restored_at=? WHERE id=?", (utcnow(), point_id))
            audit(conn, "recovery.restored", "recovery", point_id, f"Recovery point restored: {manifest['label']}", {"components": components, "safety_point": safety["id"], "verified": True})
        return {"success": True, "restored_id": point_id, "components": components, "verified": True, "safety_point_id": safety["id"], "rollback_performed": False}
    except Exception as exc:
        rollback_errors = []
        if database_replaced:
            try:
                if previous_database.exists():
                    for suffix in ("-wal", "-shm"):
                        failed_sidecar = Path(str(DB_PATH) + suffix)
                        if failed_sidecar.exists():
                            os.replace(failed_sidecar, rollback_root / f"failed-restore-sentinel.db{suffix}")
                    os.replace(previous_database, DB_PATH)
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        if "files" in components or "config" in components:
            try:
                restore_selected_files(rollback_root, components)
                remaining = verify_selected_files(rollback_root, components)
                if remaining:
                    rollback_errors.extend(remaining)
            except Exception as rollback_error:
                rollback_errors.append(f"File rollback failed: {rollback_error}")
        with transaction() as conn:
            audit(conn, "recovery.rollback", "recovery", point_id, "Restore failed; automatic database rollback attempted", {"error": str(exc), "rollback_errors": rollback_errors, "safety_point": safety["id"]})
        return {"success": False, "restored_id": point_id, "verified": False, "error": str(exc), "safety_point_id": safety["id"], "rollback_performed": not rollback_errors, "rollback_errors": rollback_errors}
    finally:
        if temporary_database.exists():
            temporary_database.unlink()
        # Keep the pre-restore DB as an additional recovery artifact; never delete the last good copy.
        if previous_database.exists() and previous_database != DB_PATH:
            destination = rollback_root / "live-before-restore.db"
            if not destination.exists():
                os.replace(previous_database, destination)
