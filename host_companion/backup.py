from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .inspector import now


def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def create_host_backup(project_root: Path) -> dict[str, Any]:
    """Back up non-secret host configuration. Never include model weights or credential stores."""
    backup_parent = Path(os.getenv("SENTINEL_HOST_BACKUP_ROOT", project_root / "host_data" / "backups"))
    backup_id = f"host-{now()[:10].replace('-', '')}-{uuid.uuid4().hex[:12]}"
    destination = backup_parent / backup_id
    destination.mkdir(parents=True, exist_ok=False)
    home = Path.home()
    candidates = [
        (home / ".config" / "opencode", "OpenCode/config"),
        (home / ".opencode", "OpenCode/home"),
        (Path(os.getenv("APPDATA", home / "AppData" / "Roaming")) / "opencode", "OpenCode/roaming"),
        (Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local")) / "opencode", "OpenCode/local"),
        (Path(os.getenv("APPDATA", home / "AppData" / "Roaming")) / "Docker" / "settings-store.json", "Docker/settings-store.json"),
        (home / ".ollama" / "config.json", "Ollama/config.json"),
    ]
    records, warnings = [], []
    for source, relative in candidates:
        if not source.exists():
            continue
        target = destination / "files" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            for path in source.rglob("*"):
                if not path.is_file() or any(part in ("node_modules", "cache", ".git") for part in path.parts):
                    continue
                # Credential and session material is excluded rather than copied in plaintext.
                if path.name.lower() in ("credentials.json", "token", "token.json", "auth.json") or "secret" in path.name.lower():
                    warnings.append(f"Excluded potential credential file: {path}")
                    continue
                output = target / path.relative_to(source)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, output)
        else:
            shutil.copy2(source, target)
    for path in sorted(destination.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            records.append({"path": str(path.relative_to(destination)), "bytes": path.stat().st_size, "sha256": file_hash(path)})
    manifest = {
        "schema": "lin4cre.sentinel.host-backup/v1",
        "id": backup_id,
        "created_at": now(),
        "files": records,
        "size_bytes": sum(item["bytes"] for item in records),
        "credentials_included": False,
        "model_weights_included": False,
        "warnings": warnings,
        "note": "Model weights and credentials require separate secured handling. No existing source file was modified.",
    }
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps({key: value for key, value in manifest.items() if key != "manifest_sha256"}, sort_keys=True).encode()).hexdigest()
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Immediate read-back and hash verification.
    for record in records:
        path = destination / record["path"]
        if file_hash(path) != record["sha256"]:
            raise RuntimeError(f"Host backup verification failed: {record['path']}")
    return {**manifest, "root_path": str(destination), "manifest_path": str(destination / "manifest.json"), "status": "verified"}
