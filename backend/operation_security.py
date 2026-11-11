from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

ALLOWED_ROLES = {"viewer", "researcher", "operator", "owner"}
ROLE_PERMISSIONS = {
    "viewer": {"read"},
    "researcher": {"read", "research", "backup"},
    "operator": {"read", "research", "backup", "repair"},
    "owner": {"read", "research", "backup", "repair", "install", "update", "restore", "security", "model"},
}


def canonical_plan(plan: dict[str, Any]) -> str:
    return json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def plan_hash(plan: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_plan(plan).encode("utf-8")).hexdigest()


def sign_operation(secret: str, operation_id: str, expires: int, plan: dict[str, Any]) -> str:
    message = f"{operation_id}.{expires}.{plan_hash(plan)}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def authorisation(secret: str, operation_id: str, plan: dict[str, Any], role: str = "owner", lifetime_seconds: int = 300) -> dict[str, Any]:
    expires = int(time.time()) + lifetime_seconds
    return {"operation_id": operation_id, "expires": expires, "plan": plan, "role": role, "signature": sign_operation(secret, operation_id, expires, plan)}


def verify_authorisation(secret: str, payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        operation_id = str(payload["operation_id"])
        expires = int(payload["expires"])
        plan = payload["plan"]
        role = str(payload["role"])
        signature = str(payload["signature"])
    except (KeyError, TypeError, ValueError):
        return False, "Authorisation envelope is incomplete"
    if role != "owner":
        return False, "Host mutations require the owner role"
    if expires < int(time.time()):
        return False, "Authorisation has expired"
    if expires > int(time.time()) + 600:
        return False, "Authorisation lifetime is invalid"
    expected = sign_operation(secret, operation_id, expires, plan)
    if not hmac.compare_digest(expected, signature):
        return False, "Plan signature does not match"
    return True, "Authorised"


def permission(role: str, action: str) -> bool:
    return action in ROLE_PERMISSIONS.get(role, set())
