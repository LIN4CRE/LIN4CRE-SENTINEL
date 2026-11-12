from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .assistant import router as assistant_router
from .db import (
    BACKUP_DIR,
    DB_PATH,
    ROOT,
    audit,
    connect,
    decode,
    decode_many,
    initialise,
    settings,
    transaction,
    utcnow,
)
from .monitor import monitor_loop
from .operations import maintenance_router, recovery_router, router as operations_router
from .scoring import WEIGHTS, evaluate
from .sources import POLICIES, REPOSITORIES, VERIFIED_AT

@asynccontextmanager
async def lifespan(_app: FastAPI):
    monitor = asyncio.create_task(monitor_loop())
    try:
        yield
    finally:
        monitor.cancel()
        try:
            await monitor
        except asyncio.CancelledError:
            pass


app = FastAPI(title="LIN4CRE SENTINEL", version="0.2.3", docs_url="/api/docs", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)

initialise()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def new_id() -> str:
    return str(uuid.uuid4())


def require_https_url(value: str, field: str) -> str:
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError(f"{field} must be a complete HTTP(S) URL")
    return value.rstrip("/")


class ProgrammeIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    platform: Literal["HackerOne", "Intigriti", "Bugcrowd", "Other"]
    handle: str = Field(default="", max_length=200)
    programme_url: str = ""
    policy_url: str = ""
    reward_criteria_url: str = ""
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    reward_min: float = Field(default=0, ge=0)
    reward_max: float = Field(default=0, ge=0)
    realistic_reward: float | None = Field(default=None, ge=0)
    assets: list[str] = Field(default_factory=list, max_length=500)
    automation_policy: Literal["allowed", "approval_required", "prohibited", "unspecified"] = "unspecified"
    ai_policy: Literal["allowed", "human_required", "prohibited", "unspecified"] = "unspecified"
    payout_process: Literal["documented", "unspecified"] = "unspecified"
    source_checked_at: str = ""
    probability_valid: float | None = Field(default=None, ge=0, le=1)
    competition_risk: float | None = Field(default=None, ge=0, le=1)
    estimated_hours: float | None = Field(default=None, gt=0, le=10000)
    notes: str = Field(default="", max_length=50000)

    @field_validator("programme_url", "policy_url", "reward_criteria_url")
    @classmethod
    def valid_urls(cls, value: str, info):
        return require_https_url(value.strip(), info.field_name)

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, value: str):
        return value.upper()

    @field_validator("assets")
    @classmethod
    def clean_assets(cls, values: list[str]):
        cleaned = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        for value in cleaned:
            if any(char in value for char in ("\r", "\n", "\x00")) or len(value) > 2048:
                raise ValueError("Assets must be single-line values of at most 2048 characters")
        return cleaned


class ProgrammePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    programme_url: str | None = None
    policy_url: str | None = None
    reward_criteria_url: str | None = None
    reward_min: float | None = Field(default=None, ge=0)
    reward_max: float | None = Field(default=None, ge=0)
    realistic_reward: float | None = Field(default=None, ge=0)
    assets: list[str] | None = None
    automation_policy: Literal["allowed", "approval_required", "prohibited", "unspecified"] | None = None
    ai_policy: Literal["allowed", "human_required", "prohibited", "unspecified"] | None = None
    payout_process: Literal["documented", "unspecified"] | None = None
    source_checked_at: str | None = None
    probability_valid: float | None = Field(default=None, ge=0, le=1)
    competition_risk: float | None = Field(default=None, ge=0, le=1)
    estimated_hours: float | None = Field(default=None, gt=0, le=10000)
    notes: str | None = Field(default=None, max_length=50000)
    archived: bool | None = None

    @field_validator("programme_url", "policy_url", "reward_criteria_url")
    @classmethod
    def valid_urls(cls, value: str | None, info):
        return require_https_url((value or "").strip(), info.field_name) if value is not None else None

    @field_validator("assets")
    @classmethod
    def clean_assets(cls, values: list[str] | None):
        if values is None:
            return None
        return ProgrammeIn.clean_assets(values)


class ApprovalIn(BaseModel):
    assets: list[str] = Field(min_length=1, max_length=100)
    methods: list[str] = Field(min_length=1, max_length=30)
    rate_limit: int = Field(default=1, ge=1, le=60)
    expires_at: str


class DecisionIn(BaseModel):
    decision: Literal["approved", "rejected", "revoked"]
    note: str = Field(default="", max_length=5000)


class FindingIn(BaseModel):
    programme_id: str
    title: str = Field(min_length=1, max_length=300)
    asset: str = Field(min_length=1, max_length=2048)
    vulnerability_class: str = Field(min_length=1, max_length=200)
    severity: Literal["unrated", "low", "medium", "high", "critical"] = "unrated"
    summary: str = Field(default="", max_length=50000)
    reproduction_steps: str = Field(default="", max_length=100000)
    impact: str = Field(default="", max_length=50000)
    evidence: str = Field(default="", max_length=200000)
    remediation: str = Field(default="", max_length=50000)
    ai_disclosure: str = Field(default="", max_length=10000)


class FindingPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    vulnerability_class: str | None = Field(default=None, min_length=1, max_length=200)
    severity: Literal["unrated", "low", "medium", "high", "critical"] | None = None
    status: Literal["draft", "investigating", "rejected"] | None = None
    summary: str | None = Field(default=None, max_length=50000)
    reproduction_steps: str | None = Field(default=None, max_length=100000)
    impact: str | None = Field(default=None, max_length=50000)
    evidence: str | None = Field(default=None, max_length=200000)
    remediation: str | None = Field(default=None, max_length=50000)
    ai_disclosure: str | None = Field(default=None, max_length=10000)


class ValidationIn(BaseModel):
    researcher_name: str = Field(min_length=1, max_length=200)
    confirmed: bool


class ReportPatch(BaseModel):
    status: Literal["draft", "ready", "submitted", "triaged", "accepted", "resolved", "duplicate", "informative", "not_applicable", "rejected"]
    platform_report_id: str = Field(default="", max_length=200)
    human_confirmation: bool = False


class PaymentIn(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    status: Literal["awarded", "paid"]
    awarded_at: str = ""
    paid_at: str = ""
    reference: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=5000)


class SettingsPatch(BaseModel):
    kill_switch: bool | None = None
    external_ai_enabled: bool | None = None
    ollama_url: str | None = None
    ollama_model: str | None = Field(default=None, max_length=200)
    researcher_name: str | None = Field(default=None, max_length=200)
    setup_backup_verified: bool | None = None
    host_companion_url: str | None = None
    automatic_monitoring: bool | None = None
    monitor_interval_minutes: int | None = Field(default=None, ge=5, le=1440)
    setup_completed: bool | None = None


class OllamaTestIn(BaseModel):
    url: str | None = None


def get_programme(conn: sqlite3.Connection, programme_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM programmes WHERE id=?", (programme_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Programme not found")
    return decode(row)  # type: ignore[return-value]


def programme_values(data: dict[str, Any], programme_id: str, now: str, source_type: str = "manual"):
    evaluation = evaluate(data)
    return (
        programme_id, data["name"], data["platform"], data["handle"], data["programme_url"],
        data["policy_url"], data["reward_criteria_url"], data["currency"], data["reward_min"],
        data["reward_max"], data.get("realistic_reward"), json.dumps(data["assets"]),
        data["automation_policy"], data["ai_policy"], data["payout_process"], data["source_checked_at"],
        data.get("probability_valid"), data.get("competition_risk"), data.get("estimated_hours"),
        data["notes"], source_type, evaluation["eligibility_status"],
        json.dumps(evaluation["eligibility_reasons"]), evaluation["score"],
        evaluation["expected_value_per_hour"], json.dumps(evaluation["score_breakdown"]), now, now,
    )


def active_approval(conn: sqlite3.Connection, programme_id: str, asset: str) -> dict[str, Any] | None:
    approvals = decode_many(conn.execute(
        "SELECT * FROM approvals WHERE programme_id=? AND status='approved' ORDER BY decided_at DESC",
        (programme_id,),
    ))
    now = datetime.now(timezone.utc)
    for approval in approvals:
        try:
            expires = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if expires > now and asset in approval["assets"]:
            return approval
    return None


@app.get("/api/health")
def health():
    with connect() as conn:
        current = settings(conn)
    return {
        "status": "operational",
        "version": app.version,
        "database": "sqlite_connected",
        "testing_engine": "enabled" if current["testing_engine_enabled"] else "disabled",
        "auto_submission": "disabled",
        "kill_switch": current["kill_switch"],
        "time": utcnow(),
    }


@app.get("/api/sources")
def sources():
    return {"checked_at": VERIFIED_AT, "repositories": REPOSITORIES, "policies": POLICIES}


@app.get("/api/scoring")
def scoring():
    return {
        "weights": WEIGHTS,
        "formula": "score = Σ(normalised factor × weight); estimated value/hour = realistic reward × valid-bug probability × (1 − competition risk) ÷ estimated hours",
        "disclaimer": "Scores use researcher-supplied estimates. They are prioritisation heuristics, not payout predictions or guarantees.",
    }


@app.get("/api/dashboard")
def dashboard():
    with connect() as conn:
        current = settings(conn)
        counts = {
            "programmes": conn.execute("SELECT COUNT(*) FROM programmes WHERE archived=0").fetchone()[0],
            "eligible": conn.execute("SELECT COUNT(*) FROM programmes WHERE archived=0 AND eligibility_status='eligible'").fetchone()[0],
            "pending_approvals": conn.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()[0],
            "findings": conn.execute("SELECT COUNT(*) FROM findings WHERE status NOT IN ('rejected')").fetchone()[0],
            "validated_findings": conn.execute("SELECT COUNT(*) FROM findings WHERE status='validated'").fetchone()[0],
            "submitted_reports": conn.execute("SELECT COUNT(*) FROM reports WHERE status NOT IN ('draft','ready')").fetchone()[0],
            "accepted_reports": conn.execute("SELECT COUNT(*) FROM reports WHERE status IN ('accepted','resolved')").fetchone()[0],
            "pc_audits": conn.execute("SELECT COUNT(*) FROM pc_audits").fetchone()[0],
        }
        paid = conn.execute("SELECT currency, SUM(amount) AS total FROM payments WHERE status='paid' GROUP BY currency").fetchall()
        awarded = conn.execute("SELECT currency, SUM(amount) AS total FROM payments WHERE status='awarded' GROUP BY currency").fetchall()
        recent = decode_many(conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 8"))
    return {
        "counts": counts,
        "paid": [dict(row) for row in paid],
        "awarded": [dict(row) for row in awarded],
        "settings": current,
        "recent_activity": recent,
    }


@app.get("/api/programmes")
def list_programmes(include_archived: bool = False):
    query = "SELECT * FROM programmes"
    if not include_archived:
        query += " WHERE archived=0"
    query += " ORDER BY CASE WHEN score IS NULL THEN 1 ELSE 0 END, score DESC, updated_at DESC"
    with connect() as conn:
        return decode_many(conn.execute(query))


@app.post("/api/programmes", status_code=201)
def create_programme(payload: ProgrammeIn):
    data = payload.model_dump()
    if data["reward_max"] < data["reward_min"]:
        raise HTTPException(422, "Maximum reward cannot be lower than minimum reward")
    programme_id = new_id()
    with transaction() as conn:
        duplicate = conn.execute(
            "SELECT id FROM programmes WHERE programme_url=? AND programme_url<>''",
            (data["programme_url"],),
        ).fetchone()
        if duplicate:
            raise HTTPException(409, "A programme with this canonical URL already exists")
        conn.execute(
            """INSERT INTO programmes(
                id,name,platform,handle,programme_url,policy_url,reward_criteria_url,currency,
                reward_min,reward_max,realistic_reward,assets_json,automation_policy,ai_policy,
                payout_process,source_checked_at,probability_valid,competition_risk,estimated_hours,
                notes,source_type,eligibility_status,eligibility_reasons_json,score,
                expected_value_per_hour,score_breakdown_json,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            programme_values(data, programme_id, utcnow()),
        )
        audit(conn, "programme.created", "programme", programme_id, f"Programme recorded: {data['name']}", {"platform": data["platform"], "source": data["programme_url"]})
        return get_programme(conn, programme_id)


@app.post("/api/programmes/import", status_code=201)
def import_programmes(payload: list[ProgrammeIn]):
    if len(payload) > 100:
        raise HTTPException(422, "Import is limited to 100 programmes at a time")
    imported, errors = [], []
    for index, item in enumerate(payload):
        try:
            created = create_programme(item)
            imported.append(created)
        except HTTPException as exc:
            errors.append({"index": index, "name": item.name, "error": exc.detail})
    with transaction() as conn:
        audit(conn, "programme.imported", "programme", message=f"Import processed: {len(imported)} created, {len(errors)} rejected", details={"errors": errors})
    return {"imported": imported, "errors": errors}


@app.get("/api/programmes/{programme_id}")
def programme_detail(programme_id: str):
    with connect() as conn:
        programme = get_programme(conn, programme_id)
        programme["approvals"] = decode_many(conn.execute("SELECT * FROM approvals WHERE programme_id=? ORDER BY requested_at DESC", (programme_id,)))
        programme["findings"] = decode_many(conn.execute("SELECT * FROM findings WHERE programme_id=? ORDER BY updated_at DESC", (programme_id,)))
        return programme


@app.patch("/api/programmes/{programme_id}")
def update_programme(programme_id: str, payload: ProgrammePatch):
    updates = payload.model_dump(exclude_unset=True)
    with transaction() as conn:
        current = get_programme(conn, programme_id)
        merged = {**current, **updates}
        if merged["reward_max"] < merged["reward_min"]:
            raise HTTPException(422, "Maximum reward cannot be lower than minimum reward")
        evaluation = evaluate(merged)
        merged.update(evaluation)
        merged["updated_at"] = utcnow()
        columns = [
            "name","programme_url","policy_url","reward_criteria_url","reward_min","reward_max",
            "realistic_reward","automation_policy","ai_policy","payout_process","source_checked_at",
            "probability_valid","competition_risk","estimated_hours","notes","archived",
            "eligibility_status","score","expected_value_per_hour",
        ]
        assignments = ", ".join(f"{column}=?" for column in columns)
        values = [merged.get(column) for column in columns]
        values += [json.dumps(merged["assets"]), json.dumps(merged["eligibility_reasons"]), json.dumps(merged["score_breakdown"]), merged["updated_at"], programme_id]
        conn.execute(
            f"UPDATE programmes SET {assignments}, assets_json=?, eligibility_reasons_json=?, score_breakdown_json=?, updated_at=? WHERE id=?",
            values,
        )
        if updates.get("assets") is not None or updates.get("automation_policy") in ("prohibited", "unspecified"):
            conn.execute("UPDATE approvals SET status='revoked', decided_at=?, decision_note=? WHERE programme_id=? AND status IN ('pending','approved')", (utcnow(), "Programme scope or testing policy changed; re-approval required.", programme_id))
        audit(conn, "programme.updated", "programme", programme_id, f"Programme updated: {merged['name']}", {"fields": list(updates)})
        return get_programme(conn, programme_id)


@app.get("/api/approvals")
def list_approvals():
    with connect() as conn:
        rows = decode_many(conn.execute(
            """SELECT a.*, p.name AS programme_name, p.platform AS platform
               FROM approvals a JOIN programmes p ON p.id=a.programme_id
               ORDER BY CASE a.status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, a.requested_at DESC"""
        ))
        return rows


@app.post("/api/programmes/{programme_id}/approvals", status_code=201)
def request_approval(programme_id: str, payload: ApprovalIn):
    with transaction() as conn:
        programme = get_programme(conn, programme_id)
        current = settings(conn)
        if current["kill_switch"]:
            raise HTTPException(423, "Kill switch is active")
        if programme["eligibility_status"] == "rejected":
            raise HTTPException(422, "A rejected programme cannot receive test approval")
        if not set(payload.assets).issubset(set(programme["assets"])):
            raise HTTPException(422, "Every requested asset must exactly match the programme's recorded eligible scope")
        try:
            expires = datetime.fromisoformat(payload.expires_at.replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires <= datetime.now(timezone.utc):
                raise ValueError
        except ValueError:
            raise HTTPException(422, "Approval expiry must be a valid future ISO timestamp")
        canonical = json.dumps({"programme_id": programme_id, "assets": sorted(payload.assets), "methods": sorted(payload.methods), "rate_limit": payload.rate_limit, "expires_at": payload.expires_at}, sort_keys=True)
        approval_id = new_id()
        conn.execute(
            """INSERT INTO approvals(id,programme_id,assets_json,methods_json,rate_limit,expires_at,scope_hash,requested_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (approval_id, programme_id, json.dumps(payload.assets), json.dumps(payload.methods), payload.rate_limit, payload.expires_at, hashlib.sha256(canonical.encode()).hexdigest(), utcnow()),
        )
        audit(conn, "approval.requested", "approval", approval_id, f"Test approval requested for {programme['name']}", {"assets": payload.assets, "methods": payload.methods, "rate_limit": payload.rate_limit, "expires_at": payload.expires_at})
        return decode(conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone())


@app.post("/api/approvals/{approval_id}/decision")
def decide_approval(approval_id: str, payload: DecisionIn):
    with transaction() as conn:
        approval = decode(conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone())
        if not approval:
            raise HTTPException(404, "Approval not found")
        current = settings(conn)
        if payload.decision == "approved":
            if current["kill_switch"]:
                raise HTTPException(423, "Kill switch is active")
            expires = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires <= datetime.now(timezone.utc):
                raise HTTPException(422, "Approval request has expired; create a new request")
            programme = get_programme(conn, approval["programme_id"])
            if programme["eligibility_status"] == "rejected":
                raise HTTPException(422, "Programme eligibility has changed; approval is blocked")
            if not set(approval["assets"]).issubset(set(programme["assets"])):
                raise HTTPException(422, "Programme scope has changed; request a new approval")
        if approval["status"] not in ("pending", "approved"):
            raise HTTPException(409, f"Cannot change an approval in {approval['status']} state")
        conn.execute("UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=?", (payload.decision, utcnow(), payload.note, approval_id))
        audit(conn, f"approval.{payload.decision}", "approval", approval_id, f"Test approval {payload.decision}", {"note": payload.note, "assets": approval["assets"]})
        return decode(conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone())


@app.get("/api/findings")
def list_findings():
    with connect() as conn:
        return decode_many(conn.execute(
            """SELECT f.*, p.name AS programme_name, p.platform AS platform,
                      r.id AS report_id, r.status AS report_status
               FROM findings f JOIN programmes p ON p.id=f.programme_id
               LEFT JOIN reports r ON r.finding_id=f.id ORDER BY f.updated_at DESC"""
        ))


@app.post("/api/findings", status_code=201)
def create_finding(payload: FindingIn):
    with transaction() as conn:
        programme = get_programme(conn, payload.programme_id)
        if payload.asset not in programme["assets"]:
            raise HTTPException(422, "Finding asset does not exactly match recorded eligible scope")
        if not active_approval(conn, payload.programme_id, payload.asset):
            raise HTTPException(422, "An active human test approval covering this exact asset is required before recording research")
        finding_id = new_id()
        now = utcnow()
        data = payload.model_dump()
        conn.execute(
            """INSERT INTO findings(id,programme_id,title,asset,vulnerability_class,severity,summary,
               reproduction_steps,impact,evidence,remediation,ai_disclosure,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (finding_id, data["programme_id"], data["title"], data["asset"], data["vulnerability_class"], data["severity"], data["summary"], data["reproduction_steps"], data["impact"], data["evidence"], data["remediation"], data["ai_disclosure"], now, now),
        )
        audit(conn, "finding.created", "finding", finding_id, f"Research record created: {data['title']}", {"asset": data["asset"], "status": "draft"})
        return decode(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())


@app.patch("/api/findings/{finding_id}")
def update_finding(finding_id: str, payload: FindingPatch):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "No changes supplied")
    with transaction() as conn:
        finding = decode(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())
        if not finding:
            raise HTTPException(404, "Finding not found")
        if finding["status"] == "validated" and set(updates) - {"status"}:
            raise HTTPException(409, "Validated findings are evidence-locked; create a new research record for corrections")
        assignments = ", ".join(f"{key}=?" for key in updates)
        conn.execute(f"UPDATE findings SET {assignments}, updated_at=? WHERE id=?", (*updates.values(), utcnow(), finding_id))
        audit(conn, "finding.updated", "finding", finding_id, f"Research record updated: {finding['title']}", {"fields": list(updates)})
        return decode(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())


@app.post("/api/findings/{finding_id}/validate")
def validate_finding(finding_id: str, payload: ValidationIn):
    if not payload.confirmed:
        raise HTTPException(422, "Human confirmation is required")
    with transaction() as conn:
        finding = decode(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())
        if not finding:
            raise HTTPException(404, "Finding not found")
        missing = [key for key in ("summary", "reproduction_steps", "impact", "evidence") if not finding[key].strip()]
        if missing:
            raise HTTPException(422, f"Validation requires complete evidence fields: {', '.join(missing)}")
        now = utcnow()
        conn.execute("UPDATE findings SET status='validated', validated_at=?, validated_by=?, updated_at=? WHERE id=?", (now, payload.researcher_name, now, finding_id))
        audit(conn, "finding.validated", "finding", finding_id, f"Human validated finding: {finding['title']}", {"validated_by": payload.researcher_name})
        return decode(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())


def report_markdown(finding: dict[str, Any], programme: dict[str, Any]) -> str:
    def section(title: str, value: str):
        return f"## {title}\n\n{value.strip() if value.strip() else 'Not provided.'}\n"
    return (
        f"# {finding['title']}\n\n"
        f"**Programme:** {programme['name']} ({programme['platform']})  \n"
        f"**Affected asset:** `{finding['asset']}`  \n"
        f"**Vulnerability class:** {finding['vulnerability_class']}  \n"
        f"**Researcher severity assessment:** {finding['severity']}  \n"
        f"**Human validation:** {finding['validated_at']} by {finding['validated_by']}\n\n"
        + section("Summary", finding["summary"])
        + section("Reproduction steps", finding["reproduction_steps"])
        + section("Security impact", finding["impact"])
        + section("Evidence", finding["evidence"])
        + section("Suggested remediation", finding["remediation"])
        + section("AI-use disclosure", finding["ai_disclosure"])
        + "\n---\nGenerated from the human-validated SENTINEL research record. Review against current programme rules before submission.\n"
    )


@app.post("/api/findings/{finding_id}/report", status_code=201)
def generate_report(finding_id: str):
    with transaction() as conn:
        finding = decode(conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,)).fetchone())
        if not finding:
            raise HTTPException(404, "Finding not found")
        if finding["status"] != "validated":
            raise HTTPException(422, "Only a human-validated finding can become a report")
        existing = conn.execute("SELECT id FROM reports WHERE finding_id=?", (finding_id,)).fetchone()
        if existing:
            raise HTTPException(409, "A report already exists for this finding")
        programme = get_programme(conn, finding["programme_id"])
        report_id, now = new_id(), utcnow()
        content = report_markdown(finding, programme)
        conn.execute("INSERT INTO reports(id,finding_id,content_md,created_at,updated_at) VALUES (?,?,?,?,?)", (report_id, finding_id, content, now, now))
        audit(conn, "report.generated", "report", report_id, f"Evidence-backed report generated: {finding['title']}")
        return decode(conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone())


@app.get("/api/reports")
def list_reports():
    with connect() as conn:
        return decode_many(conn.execute(
            """SELECT r.*, f.title, f.asset, f.severity, p.name AS programme_name, p.platform,
                      p.currency AS programme_currency
               FROM reports r JOIN findings f ON f.id=r.finding_id
               JOIN programmes p ON p.id=f.programme_id ORDER BY r.updated_at DESC"""
        ))


@app.get("/api/reports/{report_id}/download")
def download_report(report_id: str):
    with connect() as conn:
        report = decode(conn.execute("SELECT r.*, f.title FROM reports r JOIN findings f ON f.id=r.finding_id WHERE r.id=?", (report_id,)).fetchone())
        if not report:
            raise HTTPException(404, "Report not found")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in report["title"].lower()).strip("-")[:80] or "sentinel-report"
        path = BACKUP_DIR.parent / "reports" / f"{safe_name}-{report_id[:8]}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report["content_md"], encoding="utf-8")
        return FileResponse(path, media_type="text/markdown", filename=path.name)


@app.patch("/api/reports/{report_id}")
def update_report(report_id: str, payload: ReportPatch):
    with transaction() as conn:
        report = decode(conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone())
        if not report:
            raise HTTPException(404, "Report not found")
        if payload.status == "submitted" and not payload.human_confirmation:
            raise HTTPException(422, "Human confirmation is required to record a submission; SENTINEL never submits automatically")
        now = utcnow()
        submitted_at = now if payload.status == "submitted" and not report["submitted_at"] else report["submitted_at"]
        decision_at = now if payload.status in ("accepted", "resolved", "duplicate", "informative", "not_applicable", "rejected") else report["decision_at"]
        conn.execute("UPDATE reports SET status=?, platform_report_id=?, submitted_at=?, decision_at=?, updated_at=? WHERE id=?", (payload.status, payload.platform_report_id, submitted_at, decision_at, now, report_id))
        audit(conn, "report.status_changed", "report", report_id, f"Report status recorded as {payload.status}", {"platform_report_id": payload.platform_report_id, "human_confirmation": payload.human_confirmation})
        return decode(conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone())


@app.get("/api/payments")
def list_payments():
    with connect() as conn:
        return decode_many(conn.execute(
            """SELECT pay.*, f.title, p.name AS programme_name, r.platform_report_id
               FROM payments pay JOIN reports r ON r.id=pay.report_id
               JOIN findings f ON f.id=r.finding_id JOIN programmes p ON p.id=f.programme_id
               ORDER BY pay.created_at DESC"""
        ))


@app.post("/api/reports/{report_id}/payments", status_code=201)
def record_payment(report_id: str, payload: PaymentIn):
    with transaction() as conn:
        report = decode(conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone())
        if not report:
            raise HTTPException(404, "Report not found")
        if report["status"] not in ("accepted", "resolved"):
            raise HTTPException(422, "Record the programme's accepted/resolved decision before entering a bounty")
        if payload.status == "paid" and not payload.paid_at:
            raise HTTPException(422, "Actual payment date is required for a paid bounty")
        payment_id = new_id()
        conn.execute(
            "INSERT INTO payments(id,report_id,amount,currency,status,awarded_at,paid_at,reference,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (payment_id, report_id, payload.amount, payload.currency.upper(), payload.status, payload.awarded_at or None, payload.paid_at or None, payload.reference, payload.notes, utcnow()),
        )
        audit(conn, f"payment.{payload.status}", "payment", payment_id, f"Actual bounty {payload.status} recorded", {"amount": payload.amount, "currency": payload.currency.upper(), "report_id": report_id})
        return decode(conn.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone())


@app.get("/api/audit")
def audit_log(limit: int = 200):
    limit = max(1, min(limit, 1000))
    with connect() as conn:
        return decode_many(conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)))


@app.get("/api/settings")
def get_settings():
    with connect() as conn:
        return settings(conn)


@app.patch("/api/settings")
def update_settings(payload: SettingsPatch):
    updates = payload.model_dump(exclude_unset=True)
    with transaction() as conn:
        if "ollama_url" in updates:
            parsed = urlparse(updates["ollama_url"])
            if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1", "host.docker.internal"):
                raise HTTPException(422, "Ollama endpoint must be localhost, 127.0.0.1 or host.docker.internal")
        if "host_companion_url" in updates:
            parsed = urlparse(updates["host_companion_url"])
            if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "host.docker.internal") or parsed.port not in (None, 8765):
                raise HTTPException(422, "Host companion must use the loopback host on port 8765")
        if updates.get("external_ai_enabled"):
            raise HTTPException(422, "External AI remains disabled in milestone one; no provider credentials or paid calls are configured")
        for key, value in updates.items():
            conn.execute("INSERT INTO settings(key,value_json) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json", (key, json.dumps(value)))
        if updates.get("kill_switch"):
            conn.execute("UPDATE approvals SET status='revoked', decided_at=?, decision_note=? WHERE status IN ('pending','approved')", (utcnow(), "Global kill switch activated."))
            audit(conn, "system.kill_switch_activated", "system", message="Global kill switch activated; all active and pending test approvals revoked")
        elif updates.get("kill_switch") is False:
            audit(conn, "system.kill_switch_reset", "system", message="Global kill switch reset; new approvals still require human review")
        else:
            audit(conn, "settings.updated", "system", message="SENTINEL settings updated", details={"fields": list(updates)})
        return settings(conn)


@app.post("/api/ai/ollama/test")
async def test_ollama(payload: OllamaTestIn):
    with connect() as conn:
        configured = settings(conn)["ollama_url"]
    url = (payload.url or configured).rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1", "host.docker.internal"):
        raise HTTPException(422, "Only local Ollama endpoints are permitted")
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(f"{url}/api/tags")
            response.raise_for_status()
            data = response.json()
        models = [{"name": model.get("name"), "size": model.get("size"), "modified_at": model.get("modified_at")} for model in data.get("models", [])]
        with transaction() as conn:
            audit(conn, "ai.ollama_connected", "system", message="Ollama connection verified", details={"endpoint": url, "model_count": len(models)})
        return {"connected": True, "endpoint": url, "models": models}
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
        return {"connected": False, "endpoint": url, "models": [], "error": f"Ollama did not respond successfully: {type(exc).__name__}"}


@app.post("/api/system/pc-audit", status_code=201)
def import_pc_audit(payload: dict[str, Any]):
    if not payload or len(json.dumps(payload)) > 10_000_000:
        raise HTTPException(422, "Audit JSON is empty or too large")
    audit_id = new_id()
    with transaction() as conn:
        conn.execute("INSERT INTO pc_audits(id,imported_at,source_name,data_json) VALUES(?,?,?,?)", (audit_id, utcnow(), str(payload.get("audit", "PowerShell audit"))[:200], json.dumps(payload)))
        audit(conn, "system.pc_audit_imported", "system", audit_id, "Read-only Windows PC audit imported")
        return {"id": audit_id, "imported_at": utcnow(), "received_fields": sorted(payload.keys())}


@app.post("/api/system/backup", status_code=201)
def create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = BACKUP_DIR / f"sentinel-{stamp}-{uuid.uuid4().hex[:6]}.db"
    source = connect()
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
        integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")
        target.commit()
    finally:
        target.close()
        source.close()
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest = destination.with_suffix(".sha256")
    manifest.write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    with transaction() as conn:
        audit(conn, "system.backup_created", "system", message="Verified SQLite backup created", details={"file": destination.name, "sha256": digest})
    return {"file": destination.name, "sha256": digest, "bytes": destination.stat().st_size, "download_url": f"/api/system/backups/{destination.name}"}


@app.get("/api/system/backups/{filename}")
def download_backup(filename: str):
    if filename != Path(filename).name or not (filename.endswith(".db") or filename.endswith(".sha256")):
        raise HTTPException(400, "Invalid backup filename")
    path = BACKUP_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Backup not found")
    return FileResponse(path, filename=filename)


@app.get("/api/system/export")
def export_data():
    tables = ("programmes", "approvals", "findings", "reports", "payments", "audit_log", "settings", "pc_audits")
    with connect() as conn:
        return {"exported_at": utcnow(), "format_version": 1, "data": {table: decode_many(conn.execute(f"SELECT * FROM {table}")) for table in tables}}


app.include_router(assistant_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(recovery_router, prefix="/api")
app.include_router(maintenance_router, prefix="/api")

DIST = ROOT / "dist"
if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def frontend(full_path: str):
    index = DIST / "index.html"
    if not index.exists():
        raise HTTPException(503, "Frontend has not been built. Run npm run build.")
    candidate = (DIST / full_path).resolve()
    if full_path and candidate.is_file() and DIST.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(index)
