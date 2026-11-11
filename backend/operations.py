from __future__ import annotations

import asyncio
import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .db import BACKUP_DIR, DATA_DIR, DB_PATH, ROOT, audit, connect, decode, decode_many, settings, transaction, utcnow
from .host_client import HostUnavailable, backup_host, check_host_updates, execute_host, host_status, host_storage, inspect_host
from .operation_security import permission, plan_hash
from .recovery import create_recovery_point, restore_recovery_point, sync_recovery_catalog, verify_recovery_point
from .registry import SPECS, SPEC_MAP, spec_dict

router = APIRouter(prefix="/operations", tags=["operations"])
recovery_router = APIRouter(prefix="/recovery", tags=["recovery"])
maintenance_router = APIRouter(prefix="/maintenance", tags=["maintenance"])
RUNNING: set[str] = set()


def new_id() -> str:
    return str(uuid.uuid4())


def role_for(request: Request, conn: sqlite3.Connection) -> str:
    # The active role is server-side session state. A request header must never be
    # able to elevate a researcher or viewer into an owner.
    return settings(conn).get("session_role", "owner")


def require(request: Request, action: str) -> None:
    with connect() as conn:
        role = role_for(request, conn)
    if not permission(role, action):
        raise HTTPException(403, f"The {role} role does not have {action} permission")


def ensure_registry() -> None:
    with transaction() as conn:
        for spec in SPECS:
            conn.execute(
                """INSERT OR IGNORE INTO dependencies(id,component,name,category,required,source_repository,licence,status,relationships_json)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (spec.key, spec.key, spec.name, spec.category, 1 if spec.required else 0, spec.source_repository, spec.licence, "never_checked", json.dumps(spec.relationships)),
            )


def local_health() -> dict[str, Any]:
    checks = []
    try:
        with connect() as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            trigger = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='audit_log_no_delete'").fetchone()
        checks.append({"component": "database", "status": "healthy" if integrity == "ok" and not violations else "unhealthy", "summary": f"SQLite integrity: {integrity}; foreign-key violations: {len(violations)}", "evidence": {"integrity": integrity, "foreign_key_violations": len(violations)}})
        checks.append({"component": "audit_protection", "status": "healthy" if trigger else "unhealthy", "summary": "Append-only audit trigger is present" if trigger else "Audit deletion protection is missing", "evidence": {"trigger_present": bool(trigger)}})
    except sqlite3.Error as exc:
        checks.append({"component": "database", "status": "unhealthy", "summary": str(exc), "evidence": {}})
    try:
        usage = shutil.disk_usage(DATA_DIR)
        free_threshold = 2 * 1024**3
        checks.append({"component": "storage", "status": "healthy" if usage.free >= free_threshold else "unhealthy", "summary": f"{usage.free / 1024**3:.1f} GiB free on the SENTINEL data volume", "evidence": {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}})
    except OSError as exc:
        checks.append({"component": "storage", "status": "verification_failed", "summary": str(exc), "evidence": {}})
    with connect() as conn:
        current = settings(conn)
    agents = [
        {"agent": "Maintenance assistant", "status": "healthy", "summary": "Registered natural-language planner is available; model fallback requires separate verification."},
        {"agent": "Opportunity scout", "status": "not_configured", "summary": "No authenticated live programme connector is configured."},
        {"agent": "Policy analyst", "status": "not_configured" if not current.get("ollama_model") else "not_verified", "summary": "No verified local model selected" if not current.get("ollama_model") else f"Selected model: {current['ollama_model']}; inference has not been checked in this run."},
        {"agent": "Research executor", "status": "disabled", "summary": "Live testing engine remains disabled."},
        {"agent": "Evidence validator", "status": "healthy", "summary": "Deterministic evidence and human-approval gates are available."},
        {"agent": "Report generator", "status": "healthy", "summary": "Evidence-locked Markdown generator is available."},
        {"agent": "Auditor", "status": "healthy" if any(check["component"] == "audit_protection" and check["status"] == "healthy" for check in checks) else "unhealthy", "summary": "Audit integrity controls checked with the local database."},
    ]
    return {"checked_at": utcnow(), "checks": checks, "agents": agents}


def upsert_inspection(report: dict[str, Any]) -> None:
    ensure_registry()
    with transaction() as conn:
        for item in report.get("components", []):
            key = item["component"]
            spec = SPEC_MAP.get(key)
            if not spec:
                continue
            conn.execute(
                """INSERT INTO dependencies(id,component,name,category,required,installed_version,location,source_repository,licence,status,last_checked,details_json,relationships_json)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(component) DO UPDATE SET installed_version=excluded.installed_version,location=excluded.location,status=excluded.status,last_checked=excluded.last_checked,details_json=excluded.details_json""",
                (key, key, spec.name, spec.category, 1 if spec.required else 0, item.get("installed_version"), item.get("location"), spec.source_repository, spec.licence, item.get("status", "verification_failed"), item.get("last_checked") or utcnow(), json.dumps(item), json.dumps(spec.relationships)),
            )
        audit(conn, "maintenance.inspected", "system", message="Real host inspection recorded", details={"host_role": report.get("host_role"), "component_count": len(report.get("components", [])), "generated_at": report.get("generated_at")})


def upsert_updates(report: dict[str, Any]) -> None:
    with transaction() as conn:
        for item in report.get("releases", []):
            conn.execute(
                """UPDATE dependencies SET latest_compatible_version=?,update_available=?,update_category=?,release_url=?,release_notes=?,download_size_bytes=?,new_cost_detected=?,last_checked=?,details_json=? WHERE component=?""",
                (item.get("latest_compatible_version"), None if item.get("update_available") is None else int(item["update_available"]), item.get("category"), item.get("release_url"), item.get("release_notes"), item.get("download_size_bytes"), None if item.get("new_cost_detected") is None else int(item["new_cost_detected"]), item.get("last_checked"), json.dumps(item), item["component"]),
            )
        audit(conn, "updates.checked", "system", message="Official update sources checked", details={"release_count": len(report.get("releases", [])), "model_count": len(report.get("models", []))})


async def inspection() -> dict[str, Any]:
    core = local_health()
    try:
        with connect() as conn:
            report = await inspect_host(conn)
        upsert_inspection(report)
        host = {"connected": True, "report": report, "error": None}
    except HostUnavailable as exc:
        host = {"connected": False, "report": None, "error": str(exc)}
    return {"checked_at": utcnow(), "core": core, "host": host}


def operation(conn: sqlite3.Connection, operation_id: str) -> dict[str, Any]:
    item = decode(conn.execute("SELECT * FROM operations WHERE id=?", (operation_id,)).fetchone())
    if not item:
        raise HTTPException(404, "Operation not found")
    return item


def create_operation(kind: str, title: str, description: str, plan: dict[str, Any], risk: str = "read_only", approval_role: str = "owner", requires_approval: bool = True, rollback_available: bool = False) -> dict[str, Any]:
    operation_id = new_id()
    with transaction() as conn:
        conn.execute(
            """INSERT INTO operations(id,kind,title,description,risk,status,requires_approval,approval_role,plan_json,created_at,rollback_available)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (operation_id, kind, title, description, risk, "pending_approval" if requires_approval else "queued", 1 if requires_approval else 0, approval_role, json.dumps(plan), utcnow(), 1 if rollback_available else 0),
        )
        audit(conn, "operation.planned", "operation", operation_id, title, {"kind": kind, "risk": risk, "plan_hash": plan_hash(plan), "requires_approval": requires_approval})
        return operation(conn, operation_id)


def set_operation(operation_id: str, **values: Any) -> None:
    if not values:
        return
    json_fields = {"result", "verification"}
    assignments = []
    parameters = []
    for key, value in values.items():
        column = f"{key}_json" if key in json_fields else key
        assignments.append(f"{column}=?")
        parameters.append(json.dumps(value) if key in json_fields else value)
    parameters.append(operation_id)
    with transaction() as conn:
        conn.execute(f"UPDATE operations SET {', '.join(assignments)} WHERE id=?", parameters)


async def run_operation(operation_id: str) -> None:
    if operation_id in RUNNING:
        return
    RUNNING.add(operation_id)
    try:
        with connect() as conn:
            item = operation(conn, operation_id)
        set_operation(operation_id, status="running", started_at=utcnow(), error=None)
        kind, plan = item["kind"], item["plan"]
        result: dict[str, Any]
        if kind == "backup":
            point = await asyncio.to_thread(create_recovery_point, plan.get("label", "AI-requested complete recovery point"), "ai")
            host_backup, host_backup_error = None, None
            try:
                with connect() as conn:
                    host_backup = await backup_host(conn)
            except HostUnavailable as exc:
                host_backup_error = str(exc)
            result = {"success": True, "partial": bool(host_backup_error), "recovery_point": point, "host_backup": host_backup, "host_backup_error": host_backup_error, "message": "Core recovery point created and verified. Host backup and exclusions are reported separately."}
            set_operation(operation_id, recovery_point_id=point["id"])
        elif kind == "restore":
            result = await asyncio.to_thread(restore_recovery_point, plan["recovery_point_id"], plan.get("components"))
        elif kind == "emergency_stop":
            with transaction() as conn:
                conn.execute("INSERT INTO settings(key,value_json) VALUES('kill_switch','true') ON CONFLICT(key) DO UPDATE SET value_json='true'")
                conn.execute("UPDATE approvals SET status='revoked',decided_at=?,decision_note='Emergency stop through SENTINEL assistant' WHERE status IN ('pending','approved')", (utcnow(),))
                audit(conn, "system.emergency_stop", "system", message="Emergency stop activated through AI operations")
            host_result = None
            host_error = None
            try:
                with connect() as conn:
                    host_result = await execute_host(conn, operation_id, {"actions": [{"action": "stop_research"}]})
            except HostUnavailable as exc:
                host_error = str(exc)
            result = {"success": True, "partial": bool(host_error), "core_stopped": True, "host_result": host_result, "host_error": host_error, "message": "Core approvals revoked. Host process stop result is reported separately."}
        else:
            recovery = await asyncio.to_thread(create_recovery_point, f"Before {item['title']}", "pre_change")
            set_operation(operation_id, recovery_point_id=recovery["id"])
            with connect() as conn:
                result = await execute_host(conn, operation_id, plan)
            if not result.get("success") and plan.get("rollback_plan"):
                try:
                    with connect() as conn:
                        rollback = await execute_host(conn, f"rollback-{operation_id}", plan["rollback_plan"])
                    result["rollback"] = rollback
                    result["rollback_performed"] = bool(rollback.get("success"))
                except HostUnavailable as exc:
                    result["rollback_error"] = str(exc)
            if result.get("inspection"):
                upsert_inspection(result["inspection"])
        failed = not result.get("success", False)
        status = "failed" if failed else ("partial" if result.get("partial") else "succeeded")
        set_operation(operation_id, status=status, finished_at=utcnow(), result=result, verification=result.get("verification"), error=result.get("error") if failed else None)
        with transaction() as conn:
            audit(conn, f"operation.{status}", "operation", operation_id, f"Operation {status}: {item['title']}", {"success": not failed, "rollback_performed": result.get("rollback_performed", False)})
    except Exception as exc:
        set_operation(operation_id, status="failed", finished_at=utcnow(), error=f"{type(exc).__name__}: {exc}", result={"success": False, "error": str(exc)})
        with transaction() as conn:
            audit(conn, "operation.failed", "operation", operation_id, "Operation failed", details={"error": f"{type(exc).__name__}: {exc}"})
    finally:
        RUNNING.discard(operation_id)


async def run_approved_operation(operation_id: str) -> None:
    await run_operation(operation_id)


@router.get("")
def list_operations(limit: int = 100):
    with connect() as conn:
        return decode_many(conn.execute("SELECT * FROM operations ORDER BY created_at DESC LIMIT ?", (max(1, min(limit, 500)),)))


@router.get("/host-status")
async def companion_status():
    with connect() as conn:
        return await host_status(conn)


@router.get("/health")
async def health():
    return await inspection()


@router.post("/inspect")
async def inspect(request: Request):
    require(request, "read")
    return await inspection()


@router.get("/registry")
def registry():
    ensure_registry()
    with connect() as conn:
        return decode_many(conn.execute("SELECT * FROM dependencies ORDER BY category,name"))


@router.post("/updates/check")
async def check_updates(request: Request):
    require(request, "read")
    with connect() as conn:
        try:
            report = await check_host_updates(conn)
        except HostUnavailable as exc:
            raise HTTPException(503, str(exc))
    upsert_updates(report)
    upsert_inspection(report["inspection"])
    return report


@router.get("/storage")
async def storage():
    def local_sizes():
        def size(path: Path) -> int:
            return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0
        return {"project_bytes": size(ROOT) - size(ROOT / "node_modules"), "data_bytes": size(DATA_DIR), "backup_bytes": size(BACKUP_DIR), "database_bytes": DB_PATH.stat().st_size if DB_PATH.exists() else 0}
    local = await asyncio.to_thread(local_sizes)
    try:
        with connect() as conn:
            host = await host_storage(conn)
        error = None
    except HostUnavailable as exc:
        host, error = None, str(exc)
    return {"checked_at": utcnow(), "core": local, "host": host, "host_error": error}


@router.post("/backup")
async def backup(request: Request):
    require(request, "backup")
    item = create_operation("backup", "Create verified recovery point", "Back up the database, settings, audit history, configuration, evidence, reports and research records; then verify every file.", {"label": "User-requested complete recovery point"}, risk="safe_write", approval_role="operator", requires_approval=False)
    await run_operation(item["id"])
    with connect() as conn:
        return operation(conn, item["id"])


@router.post("/install-missing")
async def install_missing(request: Request):
    require(request, "read")
    current = await inspection()
    if not current["host"]["connected"]:
        raise HTTPException(503, current["host"]["error"])
    components = current["host"]["report"]["components"]
    actions = []
    seen = set()
    for item in components:
        key = item["component"]
        spec = SPEC_MAP.get(key)
        if not spec or not spec.required or item["status"] != "missing":
            continue
        if key == "wsl2":
            actions.append({"action": "install_wsl"})
            seen.add(key)
        elif key in ("docker_engine", "docker_compose"):
            if "docker_desktop" not in seen:
                actions.append({"action": "install_component", "component": "docker_desktop"})
                seen.add("docker_desktop")
        elif spec.install_method in ("winget", "npm"):
            actions.append({"action": "install_component", "component": key})
            seen.add(key)
    if not actions:
        return {"operation": None, "message": "No missing required component with a registered safe installer was detected. Existing problems may require repair rather than installation."}
    plan = {"actions": actions, "stop_on_failure": True}
    item = create_operation("install", "Install missing required components", "Install only the detected missing components using registered official package sources, then verify functionality. No existing application will be uninstalled.", plan, risk="system_change", approval_role="owner", requires_approval=True)
    return {"operation": item, "message": f"{len(actions)} installation actions need your approval."}


class InstallIn(BaseModel):
    components: list[str] = Field(min_length=1, max_length=12)


@router.post("/install")
async def install_selected(payload: InstallIn, request: Request):
    require(request, "read")
    current = await inspection()
    if not current["host"]["connected"]:
        raise HTTPException(503, current["host"]["error"])
    detected = {item["component"]: item for item in current["host"]["report"]["components"]}
    actions, seen = [], set()
    for key in dict.fromkeys(payload.components):
        item = detected.get(key)
        spec = SPEC_MAP.get(key)
        if not item or not spec:
            raise HTTPException(422, f"Unregistered component: {key}")
        if item.get("status") not in ("missing", "unhealthy", "outdated"):
            raise HTTPException(409, f"{spec.name} is not currently missing, unhealthy or outdated; inspect again before planning")
        if key == "wsl2":
            actions.append({"action": "install_wsl"})
        elif key in ("docker_engine", "docker_compose"):
            if "docker_desktop" not in seen:
                actions.append({"action": "install_component", "component": "docker_desktop"})
                seen.add("docker_desktop")
        elif spec.install_method in ("winget", "npm"):
            actions.append({"action": "install_component", "component": key})
        else:
            raise HTTPException(422, f"No safe automatic installer is registered for {spec.name}")
    plan = {"actions": actions, "stop_on_failure": True}
    item = create_operation("install", "Install selected components", "Install only the components selected from the latest real inspection, then verify functionality. No existing application will be uninstalled.", plan, risk="system_change", approval_role="owner", requires_approval=True)
    return operation_response(item)


@router.post("/updates/plan")
async def plan_updates(request: Request):
    require(request, "read")
    ensure_registry()
    with connect() as conn:
        records = decode_many(conn.execute("SELECT * FROM dependencies WHERE update_available=1 AND latest_compatible_version IS NOT NULL"))
    actions, rollback_actions = [], []
    for item in records:
        if item["new_cost_detected"] == 1 or SPEC_MAP[item["component"]].install_method not in ("winget", "npm"):
            continue
        actions.append({"action": "update_component", "component": item["component"], "version": item["latest_compatible_version"], "previous_version": item["installed_version"]})
        if SPEC_MAP[item["component"]].install_method == "npm" and item["installed_version"]:
            rollback_actions.append({"action": "update_component", "component": item["component"], "version": item["installed_version"]})
    if not actions:
        return {"operation": None, "message": "No verified compatible updates are ready for automatic installation. Major, paid-review and unsupported updates remain excluded."}
    plan = {"actions": actions, "stop_on_failure": True}
    if rollback_actions:
        plan["rollback_plan"] = {"actions": rollback_actions, "stop_on_failure": False}
    item = create_operation("update", "Install verified compatible updates", "Create a recovery point, install only the listed approved updates, run functional verification and use the registered rollback if a safe one exists.", plan, risk="system_change", approval_role="owner", requires_approval=True, rollback_available=bool(rollback_actions))
    return {"operation": item, "message": f"{len(actions)} updates need your approval."}


class RepairIn(BaseModel):
    component: str


@router.post("/repair")
async def repair(payload: RepairIn, request: Request):
    require(request, "read")
    actions = {
        "docker_engine": {"action": "repair_docker"},
        "docker_desktop": {"action": "repair_docker"},
        "ollama": {"action": "start_ollama"},
        "python": {"action": "install_python_packages"},
    }
    if payload.component not in actions:
        raise HTTPException(422, "No safe automatic repair is registered for this component. SENTINEL will not reset, uninstall or delete data as a repair.")
    item = create_operation("repair", f"Repair {SPEC_MAP[payload.component].name}", "Run the least-invasive registered repair, then verify the actual service. No reset, uninstall, deletion or security-setting change is included.", {"actions": [actions[payload.component]]}, risk="system_change", approval_role="owner", requires_approval=True)
    return operation_response(item)


class ApprovalIn(BaseModel):
    confirmed: bool
    plan_hash: str


@router.post("/{operation_id}/approve")
async def approve(operation_id: str, payload: ApprovalIn, request: Request):
    require(request, "install")
    if not payload.confirmed:
        raise HTTPException(422, "Explicit human confirmation is required")
    with connect() as conn:
        item = operation(conn, operation_id)
    if item["status"] != "pending_approval":
        raise HTTPException(409, f"Operation is {item['status']} and cannot be approved")
    if plan_hash(item["plan"]) != payload.plan_hash:
        raise HTTPException(409, "The plan changed after it was displayed. Review the new plan before approving.")
    set_operation(operation_id, status="queued", approved_at=utcnow())
    with transaction() as conn:
        audit(conn, "operation.approved", "operation", operation_id, f"Human approved operation: {item['title']}", {"plan_hash": payload.plan_hash, "role": role_for(request, conn)})
    asyncio.create_task(run_approved_operation(operation_id))
    with connect() as conn:
        return operation(conn, operation_id)


@router.post("/{operation_id}/retry")
def retry(operation_id: str, request: Request):
    require(request, "read")
    with connect() as conn:
        original = operation(conn, operation_id)
    if original["status"] != "failed":
        raise HTTPException(409, "Only failed operations can be retried")
    item = create_operation(original["kind"], f"Retry: {original['title']}", original["description"], original["plan"], original["risk"], original["approval_role"], True, bool(original["rollback_available"]))
    set_operation(item["id"], retry_of=operation_id)
    return item


@router.post("/{operation_id}/cancel")
def cancel(operation_id: str, request: Request):
    require(request, "read")
    with connect() as conn:
        item = operation(conn, operation_id)
    if item["status"] not in ("pending_approval", "queued"):
        raise HTTPException(409, "Only pending or queued operations can be cancelled; use emergency stop for active research")
    set_operation(operation_id, status="cancelled", finished_at=utcnow())
    with transaction() as conn:
        audit(conn, "operation.cancelled", "operation", operation_id, f"Operation cancelled: {item['title']}")
    with connect() as conn:
        return operation(conn, operation_id)


@router.post("/emergency-stop")
async def emergency_stop(request: Request):
    require(request, "security")
    item = create_operation("emergency_stop", "Emergency stop all research", "Revoke every test approval, activate the kill switch and stop only SENTINEL-registered research processes.", {"actions": [{"action": "stop_research"}]}, risk="emergency_safe", approval_role="owner", requires_approval=False)
    await run_operation(item["id"])
    with connect() as conn:
        return operation(conn, item["id"])


@router.get("/installation-report")
async def installation_report():
    current = await inspection()
    with connect() as conn:
        operations = decode_many(conn.execute("SELECT * FROM operations WHERE kind IN ('install','repair','update') ORDER BY created_at DESC LIMIT 100"))
        latest_recovery = conn.execute("SELECT * FROM recovery_points WHERE last_known_good=1 ORDER BY created_at DESC LIMIT 1").fetchone()
        current_settings = settings(conn)
    return {
        "schema": "lin4cre.sentinel.installation-report/v1",
        "generated_at": utcnow(),
        "application_version": "0.2.0",
        "inspection": current,
        "operations": operations,
        "latest_verified_recovery": decode(latest_recovery),
        "setup_completed": bool(current_settings.get("setup_completed")),
        "credential_status": {"host_companion_paired": bool(current_settings.get("host_companion_url")) and current["host"]["connected"], "credentials_included": False},
        "limitations": [
            "This report contains observed results, not a guarantee that every component is installed or functional.",
            "Windows elevation, restart and vendor-installer outcomes are included only when actually observed.",
            "Model weights and credentials are excluded from recovery reports and backups.",
        ],
    }


@router.get("/{operation_id}")
def get_operation(operation_id: str):
    with connect() as conn:
        return operation(conn, operation_id)


def operation_response(item: dict[str, Any]) -> dict[str, Any]:
    return {"operation": item, "message": "Approval is required before any system change."}


@recovery_router.get("")
def list_recovery():
    sync_recovery_catalog()
    with connect() as conn:
        return decode_many(conn.execute("SELECT * FROM recovery_points ORDER BY created_at DESC"))


@recovery_router.post("/{point_id}/verify")
def verify(point_id: str, request: Request):
    require(request, "read")
    return verify_recovery_point(point_id)


class RestoreIn(BaseModel):
    components: list[Literal["database", "files", "config"]] = Field(default_factory=lambda: ["database", "files", "config"])


@recovery_router.post("/{point_id}/restore")
def restore(point_id: str, payload: RestoreIn, request: Request):
    require(request, "read")
    verification = verify_recovery_point(point_id)
    if verification["status"] != "verified":
        raise HTTPException(422, "Restore is blocked because recovery verification failed")
    plan = {"recovery_point_id": point_id, "components": payload.components}
    item = create_operation("restore", "Restore verified recovery point", "Create a new safety point, restore the selected components, verify the result and automatically attempt rollback if verification fails.", plan, risk="data_restore", approval_role="owner", requires_approval=True, rollback_available=True)
    return operation_response(item)


@maintenance_router.get("/summary")
async def summary():
    ensure_registry()
    core = local_health()
    with connect() as conn:
        dependencies = decode_many(conn.execute("SELECT * FROM dependencies ORDER BY category,name"))
        latest = conn.execute("SELECT MAX(last_checked) FROM dependencies").fetchone()[0]
        recovery = conn.execute("SELECT * FROM recovery_points WHERE last_known_good=1 ORDER BY created_at DESC LIMIT 1").fetchone()
        host = await host_status(conn)
    required = [item for item in dependencies if item["required"]]
    if not latest:
        overall = "never_checked"
    elif any(item["status"] in ("unhealthy", "verification_failed") for item in required):
        overall = "unhealthy"
    elif any(item["status"] in ("missing", "outdated", "not_configured", "never_checked") for item in required) or not host["connected"]:
        overall = "degraded"
    else:
        overall = "healthy"
    return {"overall": overall, "last_checked": latest, "core": core, "host": host, "dependencies": dependencies, "latest_recovery": decode(recovery), "update_counts": {"security": sum(1 for item in dependencies if item["update_available"] == 1 and item["update_category"] == "security"), "critical": sum(1 for item in dependencies if item["update_available"] == 1 and item["update_category"] == "critical"), "application": sum(1 for item in dependencies if item["update_available"] == 1 and item["update_category"] == "application"), "available": sum(1 for item in dependencies if item["update_available"] == 1)}}
