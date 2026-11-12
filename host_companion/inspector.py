from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import psutil

from backend.registry import SPEC_MAP, is_outdated, spec_dict


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_output(value: str | bytes | None, limit: int = 12000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return value.replace("\x00", "").strip()[-limit:]


def run_command(arguments: list[str], timeout: int = 15) -> dict[str, Any]:
    started = now()
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=timeout, check=False)
        stdout, stderr = clean_output(result.stdout), clean_output(result.stderr)
        return {
            "command": arguments[0],
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False,
            "started_at": started,
            "finished_at": now(),
        }
    except FileNotFoundError:
        return {"command": arguments[0], "exit_code": None, "stdout": "", "stderr": "Executable not found", "timed_out": False, "started_at": started, "finished_at": now()}
    except subprocess.TimeoutExpired as exc:
        return {"command": arguments[0], "exit_code": None, "stdout": clean_output(exc.stdout), "stderr": "Verification timed out", "timed_out": True, "started_at": started, "finished_at": now()}
    except OSError as exc:
        return {"command": arguments[0], "exit_code": None, "stdout": "", "stderr": str(exc), "timed_out": False, "started_at": started, "finished_at": now()}


def base_component(key: str) -> dict[str, Any]:
    spec = SPEC_MAP[key]
    return {
        **spec_dict(spec),
        "component": key,
        "installed_version": None,
        "location": None,
        "status": "missing" if spec.required else "not_configured",
        "last_checked": now(),
        "functional": False,
        "evidence": [],
        "error": None,
    }


def command_component(key: str, executable: str, version_args: list[str], verify_args: list[str] | None = None, timeout: int = 15) -> dict[str, Any]:
    component = base_component(key)
    location = shutil.which(executable)
    component["location"] = location
    if not location:
        component["error"] = f"{executable} was not found on PATH"
        return component
    version = run_command([location, *version_args], timeout)
    component["evidence"].append(version)
    if version["exit_code"] != 0:
        component["status"] = "verification_failed"
        component["error"] = version["stderr"] or "Version command failed"
        return component
    output = f"{version['stdout']} {version['stderr']}".strip()
    version_match = re.search(r"\d+(?:\.\d+){1,3}(?:[-+][\w.-]+)?", output)
    component["installed_version"] = version_match.group(0) if version_match else None
    verification = run_command([location, *(verify_args or version_args)], timeout) if verify_args else version
    if verify_args:
        component["evidence"].append(verification)
    component["functional"] = verification["exit_code"] == 0
    component["status"] = "healthy" if component["functional"] else "verification_failed"
    if component["functional"] and is_outdated(component["installed_version"], SPEC_MAP[key].minimum_version):
        component["status"] = "outdated"
        component["error"] = f"Installed version is below supported version {SPEC_MAP[key].minimum_version}"
    if not component["functional"]:
        component["error"] = verification["stderr"] or "Functional verification failed"
    return component


def windows_json(script: str, timeout: int = 20) -> Any:
    if os.name != "nt":
        return None
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        return None
    result = run_command([shell, "-NoProfile", "-NonInteractive", "-Command", script], timeout)
    if result["exit_code"] != 0 or not result["stdout"]:
        return None
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError:
        return None


def hardware_report() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    gpus: list[dict[str, Any]] = []
    nvidia = shutil.which("nvidia-smi")
    if nvidia:
        result = run_command([nvidia, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"])
        if result["exit_code"] == 0:
            for line in result["stdout"].splitlines():
                parts = [part.strip() for part in line.split(",")]
                if len(parts) >= 3:
                    gpus.append({"name": parts[0], "vram_bytes": int(float(parts[1]) * 1024 * 1024), "driver": parts[2], "source": "nvidia-smi"})
    if not gpus and os.name == "nt":
        data = windows_json("Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | ConvertTo-Json -Compress")
        for item in (data if isinstance(data, list) else [data] if data else []):
            gpus.append({"name": item.get("Name"), "vram_bytes": item.get("AdapterRAM"), "driver": item.get("DriverVersion"), "source": "Win32_VideoController"})
    return {
        "cpu": {"logical_cores": psutil.cpu_count(logical=True), "physical_cores": psutil.cpu_count(logical=False), "architecture": platform.machine(), "processor": platform.processor() or None},
        "ram": {"total_bytes": memory.total, "available_bytes": memory.available},
        "gpus": gpus,
    }


def storage_report() -> list[dict[str, Any]]:
    drives = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            drives.append({"mountpoint": partition.mountpoint, "filesystem": partition.fstype, "total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free, "device": partition.device})
        except (PermissionError, FileNotFoundError, OSError):
            continue
    return drives


def ports_report() -> list[dict[str, Any]]:
    expected = {8000: "SENTINEL core", 8765: "SENTINEL host companion", 11434: "Ollama"}
    results = []
    try:
        connections = psutil.net_connections(kind="tcp")
    except (PermissionError, OSError) as exc:
        return [{"port": port, "status": "not_verified", "error": str(exc)} for port in expected]
    for port, owner in expected.items():
        listeners = [connection for connection in connections if connection.laddr and connection.laddr.port == port and connection.status == psutil.CONN_LISTEN]
        processes = []
        for connection in listeners:
            process_name = None
            if connection.pid:
                try:
                    process_name = psutil.Process(connection.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Access denied"
            processes.append({"address": str(connection.laddr.ip), "pid": connection.pid, "process": process_name})
        results.append({"port": port, "expected_owner": owner, "status": "listening" if listeners else "not_listening", "listeners": processes})
    return results


def ollama_component() -> dict[str, Any]:
    component = command_component("ollama", "ollama", ["--version"], ["list"])
    endpoint = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip().rstrip("/")
    if "://" not in endpoint:
        endpoint = "http://" + endpoint
    models = []
    try:
        response = httpx.get(f"{endpoint}/api/tags", timeout=4)
        response.raise_for_status()
        payload = response.json()
        models = [{"name": model.get("name"), "digest": model.get("digest"), "size": model.get("size"), "modified_at": model.get("modified_at"), "details": model.get("details", {})} for model in payload.get("models", [])]
        component["functional"] = True
        component["status"] = "healthy" if component["installed_version"] else "healthy"
        component["api_endpoint"] = endpoint
        component["api_verified"] = True
    except (httpx.HTTPError, ValueError) as exc:
        component["api_verified"] = False
        component["api_error"] = type(exc).__name__
        component["functional"] = False
        component["status"] = "unhealthy" if component["location"] else "missing"
        component["error"] = "Ollama API did not respond successfully"
    component["models"] = models
    component["model_count"] = len(models)
    return component


def docker_components() -> list[dict[str, Any]]:
    desktop = base_component("docker_desktop")
    docker_path = shutil.which("docker")
    desktop["location"] = docker_path
    if os.name == "nt":
        data = windows_json("$paths=@('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'); Get-ItemProperty $paths -ErrorAction SilentlyContinue | Where-Object {$_.DisplayName -eq 'Docker Desktop'} | Select-Object DisplayVersion,InstallLocation | ConvertTo-Json -Compress")
        if data:
            desktop["installed_version"] = data.get("DisplayVersion")
            desktop["location"] = data.get("InstallLocation") or docker_path
    if not docker_path:
        desktop["error"] = "Docker CLI and Desktop installation were not detected"
    engine = base_component("docker_engine")
    engine["location"] = docker_path
    if docker_path:
        version = run_command([docker_path, "--version"])
        info = run_command([docker_path, "info", "--format", "{{json .}}"], timeout=20)
        engine["evidence"] = [version, info]
        if version["exit_code"] == 0:
            match = re.search(r"\d+(?:\.\d+){1,3}", version["stdout"])
            engine["installed_version"] = match.group(0) if match else None
        if info["exit_code"] == 0:
            try:
                payload = json.loads(info["stdout"])
                engine["installed_version"] = payload.get("ServerVersion") or engine["installed_version"]
                engine["details"] = {"operating_system": payload.get("OperatingSystem"), "containers": payload.get("Containers"), "images": payload.get("Images"), "driver": payload.get("Driver")}
                engine["functional"] = True
                engine["status"] = "healthy"
                desktop["functional"] = True
                desktop["status"] = "healthy"
                if not desktop["installed_version"]:
                    desktop["installed_version"] = engine["installed_version"]
                    desktop["version_source"] = "Docker Engine fallback; Desktop version unavailable"
            except json.JSONDecodeError:
                engine["status"] = "verification_failed"
                engine["error"] = "Docker info returned unreadable output"
        else:
            engine["status"] = "unhealthy"
            engine["error"] = info["stderr"] or "Docker Engine is not responding"
            desktop["status"] = "unhealthy" if desktop["installed_version"] else "verification_failed"
            desktop["error"] = "Docker Desktop/Engine functionality could not be verified"
    compose = base_component("docker_compose")
    compose["location"] = docker_path
    if docker_path:
        result = run_command([docker_path, "compose", "version", "--json"])
        compose["evidence"] = [result]
        if result["exit_code"] == 0:
            try:
                payload = json.loads(result["stdout"])
                compose["installed_version"] = str(payload.get("version", "")).lstrip("v") or None
            except json.JSONDecodeError:
                match = re.search(r"\d+(?:\.\d+){1,3}", result["stdout"])
                compose["installed_version"] = match.group(0) if match else None
            compose["functional"] = True
            compose["status"] = "healthy"
            if is_outdated(compose["installed_version"], SPEC_MAP["docker_compose"].minimum_version):
                compose["status"] = "outdated"
        else:
            compose["status"] = "unhealthy"
            compose["error"] = result["stderr"] or "Docker Compose verification failed"
    return [desktop, engine, compose]


def windows_components() -> list[dict[str, Any]]:
    wsl = base_component("wsl2")
    if os.name != "nt":
        wsl["status"] = "not_applicable"
        return [wsl]
    path = shutil.which("wsl")
    wsl["location"] = path
    if path:
        status = run_command([path, "--status"])
        distributions = run_command([path, "--list", "--verbose"])
        wsl["evidence"] = [status, distributions]
        wsl["functional"] = status["exit_code"] == 0 and distributions["exit_code"] == 0
        wsl["status"] = "healthy" if wsl["functional"] else "unhealthy"
        if not wsl["functional"]:
            wsl["error"] = status["stderr"] or distributions["stderr"] or "WSL status could not be verified"
        version = run_command([path, "--version"])
        if version["exit_code"] == 0:
            wsl["installed_version"] = version["stdout"].splitlines()[0]
    return [wsl]


def core_components() -> list[dict[str, Any]]:
    core = base_component("sentinel_core")
    root = Path(__file__).resolve().parent.parent
    core["location"] = str(root)
    core["installed_version"] = "0.2.2"
    core["functional"] = (root / "backend" / "main.py").exists() and (root / "dist" / "index.html").exists()
    core["status"] = "healthy" if core["functional"] else "verification_failed"
    if not core["functional"]:
        core["error"] = "Core backend or built frontend is missing"
    database = base_component("database")
    db_path = Path(os.getenv("SENTINEL_DB_PATH", root / "data" / "sentinel.db"))
    database["location"] = str(db_path)
    if not db_path.exists():
        database["status"] = "not_configured"
        database["error"] = "Database file has not been created"
    else:
        try:
            connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=3)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            connection.close()
            database["functional"] = integrity == "ok" and not foreign_keys
            database["status"] = "healthy" if database["functional"] else "unhealthy"
            database["evidence"] = [{"integrity_check": integrity, "foreign_key_violations": len(foreign_keys)}]
        except sqlite3.Error as exc:
            database["status"] = "unhealthy"
            database["error"] = str(exc)
    python = base_component("python")
    python["location"] = sys.executable
    python["installed_version"] = platform.python_version()
    python["functional"] = sys.version_info >= (3, 12)
    python["status"] = "healthy" if python["functional"] else "outdated"
    packages = {}
    for package in ("fastapi", "uvicorn", "pydantic", "httpx", "python-multipart", "psutil", "packaging"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    python["packages"] = packages
    if any(value is None for value in packages.values()):
        python["status"] = "unhealthy"
        python["functional"] = False
        python["error"] = "One or more required Python packages are missing"
    return [core, database, python]


def inspect_host() -> dict[str, Any]:
    components = [
        *core_components(),
        *docker_components(),
        *windows_components(),
        ollama_component(),
        command_component("opencode", "opencode", ["--version"], ["--help"]),
        command_component("node", "node", ["--version"], ["-e", "process.stdout.write('node-ok')"]),
        command_component("npm", "npm.cmd" if os.name == "nt" else "npm", ["--version"]),
        command_component("git", "git", ["--version"], ["--exec-path"]),
    ]
    security = base_component("security_tools")
    tools = {name: shutil.which(name) for name in ("nmap", "sqlmap", "burp")}
    security["details"] = {"tools": tools}
    security["status"] = "not_configured" if not any(tools.values()) else "healthy"
    security["functional"] = any(tools.values())
    components.append(security)
    return {
        "schema": "lin4cre.sentinel.host-inspection/v1",
        "generated_at": now(),
        "platform": {"system": platform.system(), "release": platform.release(), "version": platform.version(), "architecture": platform.machine(), "python": platform.python_version()},
        "hardware": hardware_report(),
        "components": components,
        "ports": ports_report(),
        "storage": storage_report(),
        "models": next((item["models"] for item in components if item["component"] == "ollama"), []),
        "host_role": "windows_host" if os.name == "nt" else "core_environment",
    }
