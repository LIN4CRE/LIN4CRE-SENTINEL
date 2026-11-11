from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from backend.registry import SPEC_MAP, compare_versions
from .inspector import clean_output, inspect_host, now, run_command, windows_json

ALLOWED_ACTIONS = {"install_component", "update_component", "repair_docker", "start_ollama", "pull_model", "install_python_packages", "stop_research", "install_wsl", "apply_patch", "reverse_patch"}
CODE_ROOTS = {"backend", "frontend", "host_companion", "src", "tests", "docs"}
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".css", ".md", ".txt", ".html", ".svg"}
PROTECTED_CODE_PATHS = {
    "backend/main.py", "backend/db.py", "backend/operations.py", "backend/operation_security.py",
    "backend/assistant.py", "backend/registry.py", "backend/recovery.py", "backend/host_client.py",
    "host_companion/executor.py", "host_companion/server.py", "host_companion/backup.py",
}


class ActionRejected(ValueError):
    pass


def patch_paths(patch: str) -> list[str]:
    if not isinstance(patch, str) or len(patch.encode("utf-8")) > 200_000:
        raise ActionRejected("The code patch is missing or exceeds the 200 KB limit")
    paths = []
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            match = re.fullmatch(r"diff --git a/([^\s]+) b/([^\s]+)", line)
            if not match or match.group(1) != match.group(2):
                raise ActionRejected("Only ordinary, same-path unified Git diffs are allowed")
            value = match.group(1)
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or ".git" in path.parts or value in PROTECTED_CODE_PATHS or path.parts[0] not in CODE_ROOTS or path.suffix.lower() not in CODE_SUFFIXES:
                raise ActionRejected(f"Code path is outside the approved source policy: {value}")
            paths.append(value)
    if not paths or len(paths) > 20 or len(set(paths)) != len(paths):
        raise ActionRejected("A patch must touch between 1 and 20 distinct approved files")
    if "new file mode " in patch and "new file mode 100644" not in patch:
        raise ActionRejected("Only ordinary new text files are allowed")
    if re.search(r"^(?:old mode|new mode|new file mode (?!100644)|deleted file mode (?!100644)|similarity index|rename from|rename to|copy from|copy to)", patch, re.MULTILINE):
        raise ActionRejected("Mode, rename, copy and symlink patches are not allowed")
    return paths


def apply_code_patch(action: dict[str, Any], root: Path, reverse: bool = False) -> dict[str, Any]:
    patch = action.get("patch", "")
    paths = patch_paths(patch)
    git = shutil.which("git")
    if not git:
        return {"success": False, "verified": False, "error": "Git is required to validate and apply code patches safely"}
    backup = root / "data" / "backups" / "code" / f"{time.time_ns()}-{os.getpid()}"
    backup.mkdir(parents=True, exist_ok=False)
    records = []
    try:
        for value in paths:
            source = root / value
            record = {"path": value, "existed": source.exists()}
            if source.exists():
                if not source.is_file() or source.is_symlink():
                    raise ActionRejected(f"Patch target is not an ordinary file: {value}")
                content = source.read_bytes()
                record["sha256"] = hashlib.sha256(content).hexdigest()
                destination = backup / "files" / value
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                if hashlib.sha256(destination.read_bytes()).hexdigest() != record["sha256"]:
                    raise RuntimeError(f"Code backup verification failed: {value}")
            records.append(record)
        (backup / "patch.diff").write_text(patch, encoding="utf-8")
        (backup / "manifest.json").write_text(json.dumps({"files": records, "reverse": reverse}, indent=2), encoding="utf-8")
        arguments = [git, "apply", "--check", "--whitespace=error"]
        if reverse:
            arguments.append("--reverse")
        arguments.append("-")
        checked = subprocess.run(arguments, cwd=root, input=patch.encode(), capture_output=True, timeout=30, check=False)
        if checked.returncode != 0:
            return {"success": False, "verified": False, "error": clean_output(checked.stderr) or "Patch preflight failed", "backup_path": str(backup)}
        arguments.remove("--check")
        applied = subprocess.run(arguments, cwd=root, input=patch.encode(), capture_output=True, timeout=30, check=False)
        if applied.returncode != 0:
            return {"success": False, "verified": False, "error": clean_output(applied.stderr) or "Patch application failed", "backup_path": str(backup)}
        verification = []
        opposite_arguments = [git, "apply", "--check"] + ([] if reverse else ["--reverse"]) + ["-"]
        reverse_check = subprocess.run(opposite_arguments, cwd=root, input=patch.encode(), capture_output=True, timeout=30, check=False)
        verification.append({"check": "forward_patch_preflight" if reverse else "reverse_patch_preflight", "verified": reverse_check.returncode == 0, "error": clean_output(reverse_check.stderr)})
        python_files = [root / value for value in paths if value.endswith(".py") and (root / value).exists()]
        for path in python_files:
            try:
                import py_compile
                py_compile.compile(str(path), doraise=True)
                verification.append({"check": f"python_syntax:{path.name}", "verified": True})
            except py_compile.PyCompileError as exc:
                verification.append({"check": f"python_syntax:{path.name}", "verified": False, "error": str(exc)})
        if any(value.endswith((".ts", ".tsx", ".css")) for value in paths) and (root / "package.json").exists():
            npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
            build = run_command([npm, "run", "build"], timeout=240) if npm else {"exit_code": None, "stderr": "npm is unavailable"}
            verification.append({"check": "frontend_production_build", "verified": build["exit_code"] == 0, "error": build.get("stderr")})
        verified = all(item["verified"] for item in verification)
        return {"success": verified, "verified": verified, "verification": verification, "backup_path": str(backup), "changed_paths": paths, "reverse": reverse, "message": "Patch applied and verified" if verified else "Patch was applied but verification failed; the registered reverse plan is required"}
    except Exception as exc:
        return {"success": False, "verified": False, "error": f"{type(exc).__name__}: {exc}", "backup_path": str(backup)}


def validate_plan(plan: dict[str, Any]) -> None:
    actions = plan.get("actions")
    if not isinstance(actions, list) or not actions or len(actions) > 12:
        raise ActionRejected("A plan must contain between 1 and 12 registered actions")
    for action in actions:
        if not isinstance(action, dict) or action.get("action") not in ALLOWED_ACTIONS:
            raise ActionRejected("The plan contains an unregistered action")
        name = action["action"]
        if name in ("install_component", "update_component"):
            component = action.get("component")
            if component not in SPEC_MAP or not SPEC_MAP[component].install_method:
                raise ActionRejected("The requested component has no registered installer")
            if SPEC_MAP[component].install_method in ("deferred", "recovery", "builtin", "wsl"):
                raise ActionRejected("This component requires its dedicated installation path")
            if action.get("version") and not re.fullmatch(r"[A-Za-z0-9.+_:-]{1,80}", str(action["version"])):
                raise ActionRejected("Target version contains invalid characters")
        elif name == "install_wsl":
            if os.name != "nt":
                raise ActionRejected("WSL installation is only available on Windows")
        elif name == "pull_model":
            model = str(action.get("model") or "")
            if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._/-]{0,150}(?::[a-zA-Z0-9._-]{1,80})?", model):
                raise ActionRejected("Model name is invalid")
        elif name in ("apply_patch", "reverse_patch"):
            patch_paths(action.get("patch", ""))
        elif name in ("repair_docker", "start_ollama", "install_python_packages", "stop_research"):
            pass


def refresh_windows_path() -> None:
    if os.name != "nt":
        return
    value = windows_json("$m=[Environment]::GetEnvironmentVariable('Path','Machine'); $u=[Environment]::GetEnvironmentVariable('Path','User'); @{Path=($m+';'+$u)} | ConvertTo-Json -Compress")
    if value and value.get("Path"):
        os.environ["PATH"] = value["Path"]


def run_winget(action: dict[str, Any], root: Path) -> dict[str, Any]:
    component = action["component"]
    spec = SPEC_MAP[component]
    executable = shutil.which("winget")
    if not executable:
        return {"success": False, "error": "Windows Package Manager (winget) was not found. Install/update Microsoft App Installer, then retry.", "elevation_required": False}
    arguments = [executable, "install", "--id", spec.package_id, "--exact", "--silent", "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity"]
    if action.get("version"):
        arguments += ["--version", str(action["version"])]
    log_path = root / "logs" / f"winget-{component}-{int(time.time())}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    arguments += ["--log", str(log_path)]
    result = run_command(arguments, timeout=1800)
    output = f"{result['stdout']}\n{result['stderr']}".lower()
    elevation = any(phrase in output for phrase in ("administrator", "elevated", "elevation required", "access is denied"))
    result.update({"success": result["exit_code"] == 0, "elevation_required": elevation, "log_path": str(log_path), "package_id": spec.package_id})
    if not result["success"] and not result.get("error"):
        result["error"] = result["stderr"] or result["stdout"] or f"winget exited with code {result['exit_code']}"
    return result


def run_npm(action: dict[str, Any]) -> dict[str, Any]:
    spec = SPEC_MAP[action["component"]]
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not executable:
        return {"success": False, "error": "npm is unavailable. Install and verify Node.js first."}
    package = spec.package_id
    if action.get("version"):
        package = f"{package}@{action['version']}"
    result = run_command([executable, "install", "-g", package], timeout=900)
    result.update({"success": result["exit_code"] == 0, "package": package})
    if not result["success"]:
        result["error"] = result["stderr"] or result["stdout"] or "npm installation failed"
    return result


def repair_docker() -> dict[str, Any]:
    if os.name != "nt":
        return {"success": False, "error": "Automatic Docker Desktop repair is only registered for Windows; no Docker reset was attempted."}
    executable = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe"
    if not executable.exists():
        return {"success": False, "error": "Docker Desktop.exe was not found. Reinstall is required; no reset or uninstall was attempted."}
    try:
        subprocess.Popen([str(executable)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return {"success": False, "error": str(exc)}
    docker = shutil.which("docker")
    if not docker:
        return {"success": False, "error": "Docker Desktop started, but the Docker CLI is not on PATH"}
    deadline = time.time() + 120
    while time.time() < deadline:
        result = run_command([docker, "info", "--format", "{{.ServerVersion}}"], timeout=10)
        if result["exit_code"] == 0:
            return {"success": True, "message": "Docker Desktop started and Docker Engine responded", "verified_version": result["stdout"]}
        time.sleep(4)
    return {"success": False, "error": "Docker Desktop was launched, but Docker Engine did not respond within 120 seconds"}


def start_ollama(root: Path) -> dict[str, Any]:
    endpoint = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    try:
        response = httpx.get(f"{endpoint}/api/tags", timeout=3)
        response.raise_for_status()
        return {"success": True, "message": "Ollama API was already responding; no second server was started"}
    except httpx.HTTPError:
        pass
    executable = shutil.which("ollama")
    if not executable:
        return {"success": False, "error": "Ollama executable was not found"}
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = (log_dir / "ollama-serve.log").open("ab")
    try:
        kwargs: dict[str, Any] = {"stdout": log, "stderr": log}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen([executable, "serve"], **kwargs)
    except OSError as exc:
        return {"success": False, "error": str(exc)}
    finally:
        log.close()
    deadline = time.time() + 30
    while time.time() < deadline:
        if process.poll() is not None:
            return {"success": False, "error": f"Ollama server exited with code {process.returncode}; inspect ollama-serve.log"}
        try:
            response = httpx.get(f"{endpoint}/api/tags", timeout=2)
            response.raise_for_status()
            return {"success": True, "message": "Ollama server started and its API responded", "pid": process.pid}
        except httpx.HTTPError:
            time.sleep(1)
    return {"success": False, "error": "Ollama process started but its API did not respond within 30 seconds", "pid": process.pid}


def stop_research(root: Path) -> dict[str, Any]:
    runtime = root / "runtime" / "research-processes.json"
    stopped, errors = [], []
    if runtime.exists():
        try:
            records = json.loads(runtime.read_text(encoding="utf-8"))
            for record in records:
                pid, expected = int(record["pid"]), record.get("expected_process", "ollama")
                try:
                    import psutil
                    process = psutil.Process(pid)
                    if expected not in process.name().lower():
                        errors.append(f"PID {pid} was not stopped because its process identity did not match")
                        continue
                    process.terminate()
                    stopped.append(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as exc:
                    errors.append(f"PID {pid}: {type(exc).__name__}")
            runtime.unlink()
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"Research process registry could not be read: {exc}")
    return {"success": not errors, "stopped_pids": stopped, "errors": errors, "message": "Only SENTINEL-registered research processes were eligible for termination"}


def execute_action(action: dict[str, Any], root: Path) -> dict[str, Any]:
    name = action["action"]
    started = now()
    if name in ("apply_patch", "reverse_patch"):
        result = apply_code_patch(action, root, reverse=name == "reverse_patch")
    elif name in ("install_component", "update_component"):
        method = SPEC_MAP[action["component"]].install_method
        result = run_winget(action, root) if method == "winget" else run_npm(action) if method == "npm" else {"success": False, "error": "No safe registered installer"}
    elif name == "repair_docker":
        result = repair_docker()
    elif name == "start_ollama":
        result = start_ollama(root)
    elif name == "pull_model":
        executable = shutil.which("ollama")
        if not executable:
            result = {"success": False, "error": "Ollama is not installed or not on PATH"}
        else:
            result = run_command([executable, "pull", action["model"]], timeout=3600)
            result.update({"success": result["exit_code"] == 0, "model": action["model"]})
            if not result["success"]:
                result["error"] = result["stderr"] or result["stdout"] or "Model download failed"
    elif name == "install_python_packages":
        requirements = root / "requirements.txt"
        result = run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements)], timeout=1200)
        result.update({"success": result["exit_code"] == 0, "requirements": str(requirements)})
        if not result["success"]:
            result["error"] = result["stderr"] or "Python package installation failed"
    elif name == "install_wsl":
        executable = shutil.which("wsl")
        result = run_command([executable, "--install", "--no-distribution"], timeout=900) if executable else {"exit_code": None, "stderr": "WSL executable not found"}
        result.update({"success": result["exit_code"] == 0, "restart_may_be_required": True, "elevation_required": True})
        if not result["success"]:
            result["error"] = result["stderr"] or "WSL installation failed; administrator approval may be required"
    elif name == "stop_research":
        result = stop_research(root)
    else:
        result = {"success": False, "error": "Unregistered action"}
    return {"action": name, "started_at": started, "finished_at": now(), **result}


def execute_plan(plan: dict[str, Any], root: Path) -> dict[str, Any]:
    validate_plan(plan)
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for action in plan["actions"]:
        result = execute_action(action, root)
        results.append(result)
        if not result.get("success") and plan.get("stop_on_failure", True):
            break
    refresh_windows_path()
    inspection = inspect_host()
    components = {item["component"]: item for item in inspection["components"]}
    verification = []
    for action in plan["actions"]:
        key = action.get("component")
        if key:
            component = components.get(key, {})
            target = action.get("version")
            version_ok = True if not target else compare_versions(component.get("installed_version"), target) == 0
            verification.append({"component": key, "status": component.get("status"), "installed_version": component.get("installed_version"), "functional": component.get("functional"), "target_version": target, "verified": bool(component.get("functional")) and version_ok})
        elif action["action"] == "repair_docker":
            verification.append({"component": "docker_engine", "status": components.get("docker_engine", {}).get("status"), "verified": bool(components.get("docker_engine", {}).get("functional"))})
        elif action["action"] == "start_ollama":
            verification.append({"component": "ollama", "status": components.get("ollama", {}).get("status"), "verified": bool(components.get("ollama", {}).get("functional"))})
        elif action["action"] == "pull_model":
            model_names = [model.get("name") for model in inspection.get("models", [])]
            verification.append({"model": action["model"], "verified": action["model"] in model_names, "available_models": model_names})
        elif action["action"] in ("apply_patch", "reverse_patch"):
            matching = next((item for item in results if item["action"] == action["action"]), {})
            verification.extend(matching.get("verification") or [{"check": "code_patch", "verified": bool(matching.get("verified"))}])
    verified = all(item.get("verified") for item in verification) if verification else all(result.get("success") for result in results)
    return {"success": all(result.get("success") for result in results) and verified, "actions": results, "verification": verification, "verified": verified, "inspection": inspection, "rollback_performed": False}
