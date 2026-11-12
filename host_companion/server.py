from __future__ import annotations

import asyncio
import json
import os
import secrets
import threading
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from backend.operation_security import verify_authorisation
from .backup import create_host_backup
from .executor import ActionRejected, execute_plan
from .inspector import inspect_host, now, storage_report
from .updates import check_model_updates, check_updates

ROOT = Path(__file__).resolve().parent.parent
HOST_DATA = Path(os.getenv("SENTINEL_HOST_DATA_DIR", ROOT / "host_data"))
TOKEN_FILE = HOST_DATA / "host-token"
NONCE_FILE = HOST_DATA / "used-operations.json"
REPLAY_LOCK = threading.Lock()
app = FastAPI(title="SENTINEL Host Companion", version="0.2.3", docs_url=None, redoc_url=None)


def token() -> str:
    configured = os.getenv("SENTINEL_HOST_TOKEN")
    if configured:
        return configured
    if not TOKEN_FILE.exists():
        raise HTTPException(503, "Host companion token is not configured")
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


def authenticate(x_sentinel_token: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_sentinel_token, token()):
        raise HTTPException(401, "Invalid host companion credentials")


def prevent_replay(operation_id: str) -> None:
    HOST_DATA.mkdir(parents=True, exist_ok=True)
    records = []
    if NONCE_FILE.exists():
        try:
            records = json.loads(NONCE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(503, "Replay-protection state is unreadable; execution is blocked") from exc
    if any(record.get("operation_id") == operation_id for record in records):
        raise HTTPException(409, "This signed operation has already been used")
    records.append({"operation_id": operation_id, "used_at": now()})
    records = records[-500:]
    temporary = NONCE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
    os.replace(temporary, NONCE_FILE)


@app.get("/v1/status")
def status():
    return {"status": "operational", "version": app.version, "token_configured": bool(os.getenv("SENTINEL_HOST_TOKEN") or TOKEN_FILE.exists()), "time": now(), "host_role": "windows_host" if os.name == "nt" else "core_environment"}


@app.get("/v1/health", dependencies=[Depends(authenticate)])
def health():
    return {"status": "operational", "version": app.version, "time": now(), "host_role": "windows_host" if os.name == "nt" else "core_environment"}


@app.get("/v1/inspect", dependencies=[Depends(authenticate)])
async def inspect():
    return await asyncio.to_thread(inspect_host)


@app.get("/v1/updates", dependencies=[Depends(authenticate)])
async def updates():
    inspection = await asyncio.to_thread(inspect_host)
    releases = await check_updates(inspection["components"])
    models = await check_model_updates(inspection.get("models", []))
    return {"checked_at": now(), "releases": releases, "models": models, "inspection": inspection}


@app.get("/v1/storage", dependencies=[Depends(authenticate)])
async def storage():
    def report():
        project_bytes = sum(path.stat().st_size for path in ROOT.rglob("*") if path.is_file() and "node_modules" not in path.parts and ".git" not in path.parts)
        return {"drives": storage_report(), "sentinel_project_bytes": project_bytes, "project_root": str(ROOT)}
    return await asyncio.to_thread(report)


@app.post("/v1/backup", dependencies=[Depends(authenticate)])
async def backup():
    return await asyncio.to_thread(create_host_backup, ROOT)


@app.post("/v1/execute", dependencies=[Depends(authenticate)])
async def execute(payload: dict[str, Any]):
    valid, reason = verify_authorisation(token(), payload)
    if not valid:
        raise HTTPException(403, reason)
    try:
        # Validate before marking the nonce used, so malformed requests can be corrected safely.
        from .executor import validate_plan
        validate_plan(payload["plan"])
    except ActionRejected as exc:
        raise HTTPException(422, str(exc))
    with REPLAY_LOCK:
        prevent_replay(payload["operation_id"])
    try:
        result = await asyncio.to_thread(execute_plan, payload["plan"], ROOT)
        return {"operation_id": payload["operation_id"], "finished_at": now(), **result}
    except Exception as exc:
        return {"operation_id": payload["operation_id"], "finished_at": now(), "success": False, "verified": False, "error": f"Host execution failed: {type(exc).__name__}: {exc}", "rollback_performed": False}


def main() -> None:
    # Loopback only. Never expose the host companion to a LAN or public interface.
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
