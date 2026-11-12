from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx

from .db import ROOT, settings
from .operation_security import authorisation

COMPANION_DEFAULT = "http://host.docker.internal:8765"
COMPANION_HOSTS = ("localhost", "127.0.0.1", "host.docker.internal")
COMPANION_PORTS = (None, 8765)


class HostUnavailable(RuntimeError):
    pass


def companion_base(current: dict[str, Any]) -> str:
    """Resolve the host companion endpoint for this process.

    The Windows setup manager and the deployment script export
    ``SENTINEL_HOST_COMPANION_URL`` so the core can reach a companion that runs
    on the same machine. The override is honoured only while the stored setting
    still holds the untouched default, and it must satisfy the same loopback-only
    policy the settings API enforces, so a stray environment value can never
    redirect host operations to an arbitrary endpoint.
    """
    stored = str(current.get("host_companion_url") or COMPANION_DEFAULT).rstrip("/")
    override = os.getenv("SENTINEL_HOST_COMPANION_URL", "").strip().rstrip("/")
    if override and stored == COMPANION_DEFAULT:
        try:
            parsed = urlparse(override)
            port = parsed.port
        except ValueError:
            return stored
        if parsed.scheme == "http" and parsed.hostname in COMPANION_HOSTS and port in COMPANION_PORTS:
            return override
    return stored


def host_token() -> str:
    configured = os.getenv("SENTINEL_HOST_TOKEN", "").strip()
    if configured:
        return configured
    token_file = ROOT / "host_data" / "host-token"
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()
    return ""


async def host_request(conn, method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 20) -> dict[str, Any]:
    current = settings(conn)
    base = companion_base(current)
    token = host_token()
    if not token:
        raise HostUnavailable("The Windows host companion is not paired. Complete SENTINEL Setup to configure its local credentials.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=4), follow_redirects=False) as client:
            response = await client.request(method, f"{base}{path}", json=payload, headers={"X-Sentinel-Token": token})
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise HostUnavailable(f"The host companion did not respond within the allowed time: {type(exc).__name__}") from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:1000]
        raise HostUnavailable(f"Host companion rejected the request ({exc.response.status_code}): {detail}") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HostUnavailable(f"Host companion is unavailable: {type(exc).__name__}") from exc


async def host_status(conn) -> dict[str, Any]:
    current = settings(conn)
    base = companion_base(current)
    paired = bool(host_token())
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(f"{base}/v1/status")
            response.raise_for_status()
            data = response.json()
        return {"connected": True, "paired": paired, "details": data, "error": None if paired else "Companion is running but credentials are not configured"}
    except (httpx.HTTPError, ValueError) as exc:
        return {"connected": False, "paired": paired, "details": None, "error": f"Not connected: {type(exc).__name__}"}


async def inspect_host(conn) -> dict[str, Any]:
    return await host_request(conn, "GET", "/v1/inspect", timeout=90)


async def check_host_updates(conn) -> dict[str, Any]:
    return await host_request(conn, "GET", "/v1/updates", timeout=180)


async def host_storage(conn) -> dict[str, Any]:
    return await host_request(conn, "GET", "/v1/storage", timeout=30)


async def backup_host(conn) -> dict[str, Any]:
    return await host_request(conn, "POST", "/v1/backup", {}, timeout=1800)


async def execute_host(conn, operation_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    token = host_token()
    if not token:
        raise HostUnavailable("Cannot authorise host operation without a paired host token")
    envelope = authorisation(token, operation_id, plan, role="owner", lifetime_seconds=300)
    return await host_request(conn, "POST", "/v1/execute", envelope, timeout=3900)
