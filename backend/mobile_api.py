from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from .db import connect
from .mobile_auth import require_mobile_token

router = APIRouter(prefix="/api/mobile/v1", dependencies=[Depends(require_mobile_token)])


def _table_count(conn: sqlite3.Connection, table: str, where: str = "") -> int:
    # Table identifiers here are fixed literals, never request-controlled.
    query = f"SELECT COUNT(*) FROM {table} {where}"
    return int(conn.execute(query).fetchone()[0])


@router.get("/health")
def mobile_health() -> dict[str, str]:
    return {"status": "operational", "service": "SENTINEL read-only mobile companion"}


@router.get("/overview")
def overview() -> dict[str, Any]:
    with connect() as conn:
        counts = {
            "programmes": _table_count(conn, "programmes", "WHERE archived=0"),
            "pending_approvals": _table_count(conn, "approvals", "WHERE status='pending'"),
            "active_approvals": _table_count(conn, "approvals", "WHERE status='approved'"),
            "findings": _table_count(conn, "findings"),
            "validated_findings": _table_count(conn, "findings", "WHERE status='validated'"),
            "submitted_reports": _table_count(conn, "reports", "WHERE status IN ('submitted','triaged','accepted','resolved','paid')"),
            "accepted_reports": _table_count(conn, "reports", "WHERE status IN ('accepted','resolved','paid')"),
        }
        paid = [dict(row) for row in conn.execute(
            "SELECT currency, ROUND(SUM(amount),2) AS amount FROM payments WHERE status='paid' GROUP BY currency ORDER BY currency"
        ).fetchall()]
    return {"status": "operational", "version": "0.2.3", "read_only": True, "counts": counts, "paid": paid}


@router.get("/programmes")
def programmes(limit: int = Query(default=50, ge=1, le=100)) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT id, name, platform, currency, reward_min, reward_max,
                      eligibility_status, score, source_checked_at, updated_at
               FROM programmes WHERE archived=0 ORDER BY updated_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/approvals")
def approvals(limit: int = Query(default=50, ge=1, le=100)) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT a.id, a.status, a.assets_json, a.methods_json, a.rate_limit,
                      a.expires_at, a.requested_at, p.name AS programme_name, p.platform
               FROM approvals a JOIN programmes p ON p.id=a.programme_id
               ORDER BY CASE a.status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
                        a.requested_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["assets"] = json.loads(item.pop("assets_json") or "[]")
        item["methods"] = json.loads(item.pop("methods_json") or "[]")
        result.append(item)
    return result


@router.api_route("/{unmatched:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def mobile_not_found(unmatched: str):
    # This ASGI app intentionally has no mutations or catch-all proxy to the core API.
    return JSONResponse(status_code=404, content={"detail": "Mobile companion endpoint not found"}, headers={"Cache-Control": "no-store"})
