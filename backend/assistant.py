from __future__ import annotations

import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .db import ROOT, connect, decode, decode_many, settings, transaction, utcnow
from .host_client import HostUnavailable, check_host_updates, inspect_host
from .operations import create_operation, inspection, operation, require, run_operation, upsert_inspection, upsert_updates
from .recovery import create_recovery_point
from .registry import SPEC_MAP

router = APIRouter(prefix="/assistant", tags=["assistant"])


@dataclass
class Intent:
    name: str
    confidence: float
    explanation: str
    entity: str | None = None


def interpret(text: str) -> Intent:
    value = text.lower().strip()
    def has(*phrases: str) -> bool:
        return any(phrase in value for phrase in phrases)
    if has("stop all", "emergency stop", "stop research", "kill switch", "stop everything"):
        return Intent("emergency_stop", 0.99, "Emergency-stop wording was explicit.")
    if has("change code", "modify code", "edit code", "fix the code", "make a code change", "implement a code", "write a patch"):
        return Intent("code_change", 0.9, "The request asks for a human-reviewed source-code patch.")
    if has("restore", "roll back", "rollback", "previous working version", "recover backup"): 
        return Intent("restore", 0.94, "The request asks for recovery-point restoration.")
    if has("back up", "backup", "recovery point", "save everything"):
        return Intent("backup", 0.97, "The request asks for a verified recovery point.")
    if has("check for updates", "check updates", "updates available", "need updating", "update check", "check whether my ai models"):
        return Intent("check_updates", 0.94, "This is a read-only official-release check.")
    if has("update all", "install updates", "install the updates", "upgrade all", "update outdated"):
        return Intent("install_updates", 0.95, "The request asks for an update installation plan.")
    if has("install anything", "install missing", "set up everything", "install what", "complete installation", "install sentinel"):
        return Intent("install_missing", 0.95, "The request asks for missing-dependency installation.")
    if has("better free ai model", "better free model", "find a better", "recommend a model", "best model"):
        return Intent("model_advice", 0.9, "The request asks for a model comparison without changing models.")
    if has("fix the docker", "repair docker", "docker connection", "docker isn't", "docker is not", "start docker"):
        return Intent("repair_docker", 0.94, "The request concerns Docker connectivity or repair.")
    if has("fix ollama", "start ollama", "ollama isn't", "ollama is not", "agent isn't responding", "agent is not responding", "check why an agent"):
        return Intent("repair_agent", 0.88, "The request concerns local AI or agent responsiveness.")
    if has("storage", "disk space", "how much space", "space is sentinel using", "disk usage"):
        return Intent("storage", 0.96, "The request asks for measured storage usage.")
    if has("find new cash", "find new bug", "new bug bounty", "new cash-paying", "discover programmes", "discover programs"):
        return Intent("discover_programmes", 0.93, "The request concerns live programme discovery.")
    if has("start researching", "research the best", "start research", "investigate the best"):
        return Intent("start_research", 0.93, "The request asks to begin authorised research.")
    if has("earnings", "how much did i make", "bounties received", "income", "paid so far"):
        return Intent("earnings", 0.93, "The request asks for actual bounty ledger totals.")
    if has("health", "everything is working", "everything working", "check whether", "system status", "check my system", "diagnose"):
        return Intent("health", 0.91, "The request asks for real health verification.")
    if has("explain what", "what are you doing", "what can you do", "explain yourself", "show operations"):
        return Intent("explain", 0.89, "The request asks for an explanation of current capabilities or activity.")
    if has("generate report", "create report", "prepare submission"):
        return Intent("reports", 0.88, "The request concerns evidence-backed reports.")
    return Intent("unknown", 0.0, "No registered deterministic intent matched.")


ALLOWED_MODEL_INTENTS = {"health", "backup", "restore", "check_updates", "install_updates", "install_missing", "storage", "repair_docker", "repair_agent", "emergency_stop", "explain", "earnings", "discover_programmes", "start_research", "reports", "model_advice", "code_change"}


async def model_intent(text: str, current: dict[str, Any]) -> Intent | None:
    model = current.get("ollama_model")
    if not model:
        return None
    url = current.get("ollama_url", "http://127.0.0.1:11434").rstrip("/")
    prompt = (
        "Classify the user's request into exactly one allowed SENTINEL operations intent. "
        "Return only JSON with keys intent and confidence. Do not propose commands, paths, targets or arguments. "
        f"Allowed intents: {sorted(ALLOWED_MODEL_INTENTS)}. If unsure, use unknown.\n\nUser request: {text}"
    )
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{url}/api/generate", json={"model": model, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0}})
            response.raise_for_status()
            payload = response.json()
        content = payload.get("response", "")
        parsed = json.loads(content)
        name = parsed.get("intent")
        confidence = float(parsed.get("confidence", 0))
        if name in ALLOWED_MODEL_INTENTS and confidence >= 0.65:
            return Intent(name, confidence, f"Local model {model} classified the request; the registered planner validated the intent.")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
    return None


def code_context(text: str) -> str:
    from host_companion.executor import CODE_ROOTS, CODE_SUFFIXES, PROTECTED_CODE_PATHS
    lowered = text.lower()
    candidates = []
    for folder in sorted(CODE_ROOTS):
        root = ROOT / folder
        if not root.exists():
            continue
        for path in root.rglob("*"):
            relative = str(path.relative_to(ROOT))
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in CODE_SUFFIXES or relative in PROTECTED_CODE_PATHS or path.stat().st_size > 40_000:
                continue
            score = sum(3 for token in path.stem.lower().split(("-", "_")) if len(token) > 2 and token in lowered)
            score += sum(1 for token in ("assistant", "style", "operation", "recovery", "maintenance") if token in lowered and token in relative.lower())
            if "colour" in lowered or "color" in lowered or "button" in lowered:
                score += 2 if path.suffix == ".css" else 0
            candidates.append((score, relative, path))
    selected = sorted(candidates, key=lambda item: (-item[0], item[1]))[:4]
    sections = []
    budget = 70_000
    for _, relative, path in selected:
        content = path.read_text(encoding="utf-8", errors="replace")[: min(25_000, budget)]
        budget -= len(content)
        sections.append(f"FILE {relative}\n{content}")
        if budget <= 0:
            break
    return "\n\n".join(sections)


async def generate_code_patch(text: str, current: dict[str, Any]) -> str:
    model = current.get("ollama_model")
    if not model:
        raise HTTPException(409, "Code changes need a verified local Ollama model. Select and test a model first; SENTINEL will not invent a patch or use a paid API.")
    url = current.get("ollama_url", "http://127.0.0.1:11434").rstrip("/")
    prompt = (
        "Create a minimal unified Git diff for the user's software change. Output only diff text, with no explanation. "
        "Every diff must start with diff --git a/<path> b/<path>. Only ordinary text files under backend/, src/, tests/, docs/ or host_companion/ are allowed. "
        "Do not modify dependencies, secrets, configuration, Docker files, security policy, audit controls or approval controls. "
        "Do not include commands, installers, shell scripts, symlinks, renames or binary files. If the request cannot be completed safely, output nothing.\n\n"
        f"User request: {text}\n\nRelevant current source context:\n{code_context(text)}"
    )
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(f"{url}/api/generate", json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}})
            response.raise_for_status()
            content = response.json().get("response", "")
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, f"The configured local model could not produce a code patch: {type(exc).__name__}") from exc
    if "```diff" in content:
        content = content.split("```diff", 1)[1].split("```", 1)[0]
    content = content.strip() + "\n"
    try:
        from host_companion.executor import patch_paths
        paths = patch_paths(content)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, f"The model response was not a permitted code patch: {exc}") from exc
    if not content.startswith("diff --git "):
        raise HTTPException(422, "The model response did not start with a unified Git diff")
    return content


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None


def add_message(conn, conversation_id: str, role: str, content: str, operation_id: str | None = None, metadata: dict[str, Any] | None = None, status: str = "complete") -> dict[str, Any]:
    message_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO chat_messages(id,conversation_id,role,content,created_at,operation_id,status,metadata_json) VALUES(?,?,?,?,?,?,?,?)",
        (message_id, conversation_id, role, content, utcnow(), operation_id, status, json.dumps(metadata or {})),
    )
    return decode(conn.execute("SELECT * FROM chat_messages WHERE id=?", (message_id,)).fetchone())  # type: ignore[return-value]


def conversation(conn, conversation_id: str) -> dict[str, Any]:
    item = decode(conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone())
    if not item:
        raise HTTPException(404, "Conversation not found")
    return item


def format_bytes(value: int | float | None) -> str:
    if value is None:
        return "No Data Available"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} TiB"


def plan_install(report: dict[str, Any]) -> dict[str, Any] | None:
    actions, seen = [], set()
    for item in report["components"]:
        key = item["component"]
        if item.get("status") != "missing" or not item.get("required"):
            continue
        if key == "wsl2":
            actions.append({"action": "install_wsl"})
        elif key in ("docker_engine", "docker_compose"):
            if "docker_desktop" not in seen:
                actions.append({"action": "install_component", "component": "docker_desktop"})
                seen.add("docker_desktop")
        elif item.get("install_method") in ("winget", "npm"):
            actions.append({"action": "install_component", "component": key})
            seen.add(key)
    return {"actions": actions, "stop_on_failure": True} if actions else None


def plan_updates() -> dict[str, Any] | None:
    with connect() as conn:
        records = decode_many(conn.execute("SELECT * FROM dependencies WHERE update_available=1 AND latest_compatible_version IS NOT NULL"))
    actions, rollback = [], []
    for item in records:
        spec = SPEC_MAP.get(item["component"])
        if item["new_cost_detected"] == 1 or not spec or spec.install_method not in ("winget", "npm"):
            continue
        actions.append({"action": "update_component", "component": item["component"], "version": item["latest_compatible_version"], "previous_version": item["installed_version"]})
        if spec.install_method == "npm" and item["installed_version"]:
            rollback.append({"action": "update_component", "component": item["component"], "version": item["installed_version"]})
    if not actions:
        return None
    plan: dict[str, Any] = {"actions": actions, "stop_on_failure": True}
    if rollback:
        plan["rollback_plan"] = {"actions": rollback, "stop_on_failure": False}
    return plan


@router.get("/conversations")
def conversations():
    with connect() as conn:
        return decode_many(conn.execute("SELECT c.*,(SELECT COUNT(*) FROM chat_messages m WHERE m.conversation_id=c.id) AS message_count FROM conversations c ORDER BY c.created_at DESC"))


@router.get("/conversations/{conversation_id}")
def messages(conversation_id: str):
    with connect() as conn:
        conversation(conn, conversation_id)
        return decode_many(conn.execute("SELECT * FROM chat_messages WHERE conversation_id=? ORDER BY created_at", (conversation_id,)))


@router.post("/message")
async def message(payload: MessageIn, request: Request):
    require(request, "read")
    text = payload.text.strip()
    with transaction() as conn:
        conversation_id = payload.conversation_id
        if conversation_id:
            conversation(conn, conversation_id)
        else:
            conversation_id = str(uuid.uuid4())
            conn.execute("INSERT INTO conversations(id,created_at,title) VALUES(?,?,?)", (conversation_id, utcnow(), text[:70]))
        add_message(conn, conversation_id, "user", text)
        current = settings(conn)
    intent = interpret(text)
    if intent.name == "unknown":
        model_result = await model_intent(text, current)
        if model_result:
            intent = model_result

    content = ""
    operation_item = None
    metadata: dict[str, Any] = {"intent": intent.name, "confidence": intent.confidence, "interpretation": intent.explanation}
    status = "complete"

    if intent.name == "code_change":
        require(request, "repair")
        patch = await generate_code_patch(text, current)
        plan = {"actions": [{"action": "apply_patch", "patch": patch}], "stop_on_failure": True, "rollback_plan": {"actions": [{"action": "reverse_patch", "patch": patch}], "stop_on_failure": False}}
        operation_item = create_operation("code_change", "Review proposed code change", "Apply only the displayed unified diff after owner approval. Every affected source file is backed up and hashed; Python syntax or frontend build checks run where applicable, with a registered reverse patch on failure.", plan, risk="code_change", approval_role="owner", requires_approval=True, rollback_available=True)
        content = "I prepared a proposed code patch using the configured local model. Nothing has changed. Review the complete diff in the approval card; only that exact signed plan can run. Model-generated code still requires your technical and security review."
        metadata["links"] = [{"label": "Review proposed patch", "path": "/maintenance?tab=operations"}]
    elif intent.name == "health":
        result = await inspection()
        core_bad = [check for check in result["core"]["checks"] if check["status"] != "healthy"]
        if result["host"]["connected"]:
            components = result["host"]["report"]["components"]
            counts = {state: sum(1 for item in components if item["status"] == state) for state in ("healthy", "missing", "outdated", "unhealthy", "verification_failed")}
            content = f"I checked the actual host and core. Host results: {counts['healthy']} healthy, {counts['missing']} missing, {counts['outdated']} outdated, {counts['unhealthy']} unhealthy, and {counts['verification_failed']} verification failures. Core checks found {len(core_bad)} issue(s). Details are in Maintenance."
            metadata["health"] = result
        else:
            content = f"The core checks completed with {len(core_bad)} issue(s), but I could not verify Windows components: {result['host']['error']} I have not marked them healthy."
        metadata["links"] = [{"label": "Open health details", "path": "/maintenance"}]
    elif intent.name == "storage":
        # Measure directly to avoid treating cached values as current.
        def sizes():
            from .db import BACKUP_DIR, DATA_DIR, DB_PATH, ROOT
            def size(path):
                return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0
            return {"project": size(ROOT) - size(ROOT / "node_modules"), "data": size(DATA_DIR), "backups": size(BACKUP_DIR), "database": DB_PATH.stat().st_size if DB_PATH.exists() else 0}
        measured = await asyncio.to_thread(sizes)
        content = f"Current core measurements: project {format_bytes(measured['project'])}, data {format_bytes(measured['data'])}, backups {format_bytes(measured['backups'])}, and database {format_bytes(measured['database'])}. Open Maintenance for host drive measurements when the companion is connected."
        metadata["storage"] = measured
        metadata["links"] = [{"label": "Storage details", "path": "/maintenance?tab=storage"}]
    elif intent.name == "backup":
        require(request, "backup")
        operation_item = create_operation("backup", "Create verified recovery point", "Back up and verify core data plus available non-secret host configuration.", {"label": "AI-requested complete recovery point"}, risk="safe_write", approval_role="operator", requires_approval=False)
        status = "running"
        content = "I’m creating a recovery point and verifying its files. Credentials and model weights are excluded; any unavailable host backup will be reported as partial rather than hidden."
        asyncio.create_task(run_operation(operation_item["id"]))
    elif intent.name == "emergency_stop":
        require(request, "security")
        operation_item = create_operation("emergency_stop", "Emergency stop all research", "Revoke every test approval, activate the kill switch and stop only SENTINEL-registered research processes.", {"actions": [{"action": "stop_research"}]}, risk="emergency_safe", approval_role="owner", requires_approval=False)
        status = "running"
        content = "Emergency stop initiated. Core approvals are being revoked; host process termination will be reported separately."
        asyncio.create_task(run_operation(operation_item["id"]))
    elif intent.name == "check_updates":
        try:
            with connect() as conn:
                report = await check_host_updates(conn)
            upsert_updates(report)
            upsert_inspection(report["inspection"])
            available = [item for item in report["releases"] if item.get("update_available")]
            failed = [item for item in report["releases"] if item.get("status") == "verification_failed"]
            model_updates = [item for item in report["models"] if item.get("update_available")]
            content = f"Official sources returned {len(available)} component update(s) and {len(model_updates)} AI-model update(s). {len(failed)} release checks failed verification. No update has been installed. Review versions and notes in Maintenance."
            metadata["updates"] = {"releases": report["releases"], "models": report["models"]}
            metadata["links"] = [{"label": "Review updates", "path": "/maintenance?tab=updates"}]
        except HostUnavailable as exc:
            content = f"I couldn’t complete the official update check: {exc}"
    elif intent.name == "install_missing":
        current_health = await inspection()
        if not current_health["host"]["connected"]:
            content = f"I can’t build a truthful installation plan without inspecting the host: {current_health['host']['error']}"
        else:
            plan = plan_install(current_health["host"]["report"])
            if not plan:
                content = "I found no missing required component with a registered safe installer. Existing unhealthy components may need a repair plan instead."
            else:
                operation_item = create_operation("install", "Install missing required components", "Install only detected missing components from registered official sources and verify each result.", plan, risk="system_change", approval_role="owner", requires_approval=True)
                content = f"I found {len(plan['actions'])} installation action(s). Review exactly what will change and approve only if you agree."
                status = "pending_approval"
    elif intent.name == "install_updates":
        plan = plan_updates()
        if not plan:
            content = "No verified compatible updates are ready for automatic installation. Run an update check first. Major updates, cost-review items and unsupported components remain excluded."
        else:
            operation_item = create_operation("update", "Install verified compatible updates", "Create a recovery point, install the listed updates, verify functionality and use any registered safe rollback.", plan, risk="system_change", approval_role="owner", requires_approval=True, rollback_available=bool(plan.get("rollback_plan")))
            content = f"I prepared {len(plan['actions'])} update action(s). Nothing is installed until you approve the exact plan."
            status = "pending_approval"
    elif intent.name in ("repair_docker", "repair_agent"):
        component = "docker_engine" if intent.name == "repair_docker" else "ollama"
        action = "repair_docker" if component == "docker_engine" else "start_ollama"
        operation_item = create_operation("repair", f"Repair {component}", "Run the least-invasive registered repair and verify the service. No reset, uninstall or data deletion is included.", {"actions": [{"action": action}]}, risk="system_change", approval_role="owner", requires_approval=True)
        content = f"I can try the safe {component} repair: {action}. It will not reset Docker, reinstall anything, delete data or change security settings. Approval is required."
        status = "pending_approval"
    elif intent.name == "restore":
        require(request, "restore")
        with connect() as conn:
            point = decode(conn.execute("SELECT * FROM recovery_points WHERE status='verified' ORDER BY created_at DESC LIMIT 1").fetchone())
        if not point:
            content = "No verified recovery point is available. I will not attempt a restore from an unverified or corrupted backup."
        else:
            operation_item = create_operation("restore", "Restore latest verified recovery point", f"Create a safety point and restore {point['label']} from {point['created_at']}, then verify and roll back if needed.", {"recovery_point_id": point["id"], "components": ["database", "files", "config"]}, risk="data_restore", approval_role="owner", requires_approval=True, rollback_available=True)
            content = f"The latest verified recovery point is {point['label']} ({point['created_at']}). Review the restore plan carefully; a new safety point will be created first."
            status = "pending_approval"
    elif intent.name == "earnings":
        with connect() as conn:
            paid = [dict(row) for row in conn.execute("SELECT currency,SUM(amount) total,COUNT(*) count FROM payments WHERE status='paid' GROUP BY currency")]
        content = "Actual paid bounties: " + (", ".join(f"{row['total']:.2f} {row['currency']} across {row['count']} payment(s)" for row in paid) if paid else "No Data Available — no paid bounty records exist.") + " Estimated opportunity value is never included."
        metadata["links"] = [{"label": "Open earnings ledger", "path": "/earnings"}]
    elif intent.name == "discover_programmes":
        content = "No authenticated live programme connector is configured, so I cannot truthfully return new programmes in this run. I will not scrape a directory and invent reward or scope fields. You can import verified canonical programme data now; the next safe connector must preserve source URLs and retrieval timestamps."
        metadata["links"] = [{"label": "Import verified programmes", "path": "/opportunities"}]
    elif intent.name == "start_research":
        with connect() as conn:
            eligible = conn.execute("SELECT COUNT(*) FROM programmes WHERE archived=0 AND eligibility_status='eligible'").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM approvals WHERE status='approved' AND expires_at>?", (utcnow(),)).fetchone()[0]
        content = f"I found {eligible} eligible programme(s) and {active} active approval(s). The live research executor is disabled, so I have not started testing. The safe next step is to review scope and approvals; no target has been contacted."
        metadata["links"] = [{"label": "Review approvals", "path": "/approvals"}]
    elif intent.name == "reports":
        with connect() as conn:
            ready = conn.execute("SELECT COUNT(*) FROM findings f LEFT JOIN reports r ON r.finding_id=f.id WHERE f.status='validated' AND r.id IS NULL").fetchone()[0]
        content = f"There are {ready} human-validated finding(s) awaiting report generation. Open Research to inspect the evidence and generate a report; I will not submit it automatically."
        metadata["links"] = [{"label": "Open research", "path": "/research"}]
    elif intent.name == "model_advice":
        content = "I can compare installed models and official update digests, but I cannot truthfully call a model 'better for vulnerability research' without a measured benchmark. No model has been changed. The safe option is to verify your actual hardware and installed models, then evaluate candidates locally before approval."
        metadata["links"] = [{"label": "Verify AI setup", "path": "/settings?section=ai"}]
    elif intent.name == "explain":
        with connect() as conn:
            active_ops = decode_many(conn.execute("SELECT id,title,status,kind FROM operations WHERE status IN ('running','queued','pending_approval') ORDER BY created_at DESC LIMIT 5"))
        content = "I translate ordinary-language requests into registered operations, verify real results and ask before consequential changes. I cannot run arbitrary shell commands or expand testing scope. Current pending/active operations: " + (", ".join(f"{item['title']} ({item['status']})" for item in active_ops) if active_ops else "none")
        metadata["operations"] = active_ops
    else:
        content = "I don’t have a safe registered action for that request. You can ask me to check health, install missing components, check or install updates, repair Docker/Ollama, measure storage, back up, restore, stop research, explain activity, or summarise actual earnings. I’ll say when something is unavailable rather than simulate it."

    if operation_item:
        metadata["operation"] = operation_item
    with transaction() as conn:
        assistant = add_message(conn, conversation_id, "assistant", content, operation_item["id"] if operation_item else None, metadata, status)
        return {"conversation_id": conversation_id, "message": assistant, "operation": operation_item}


@router.get("/capabilities")
def capabilities():
    return {
        "planner": "constrained_registered_intents",
        "arbitrary_shell_execution": False,
        "model_can_define_commands": False,
        "actions": ["health", "storage", "backup", "restore", "check_updates", "install_updates", "install_missing", "repair_docker", "repair_agent", "emergency_stop", "earnings", "discover_programmes", "start_research", "reports", "model_advice", "code_change", "explain"],
        "unavailable": ["live_programme_connector", "live_research_executor", "autonomous_submission"],
    }
