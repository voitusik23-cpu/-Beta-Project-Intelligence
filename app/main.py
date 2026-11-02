from __future__ import annotations

import csv
import asyncio
import io
import json
from contextlib import asynccontextmanager
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import connect, init_db
from .discovery import now
from .monitoring import monitor_loop, run_manual_scan
from .screening import screen_projects


class TranslationInput(BaseModel):
    translated_description: str = Field(min_length=1, max_length=12000)


class ReviewInput(BaseModel):
    manual_status: str | None = None
    level2_status: str | None = None
    verification_status: str | None = None
    translated_description: str | None = None
    team_summary: str | None = None
    product_summary: str | None = None
    funding_summary: str | None = None
    participation_summary: str | None = None
    entry_cost: str | None = None
    deadline: str | None = None
    opportunity: str | None = None
    risks: str | None = None
    analyst_conclusion: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    evidence_confidence: int | None = Field(default=None, ge=0, le=100)
    score_rationale: str | None = None
    user_notes: str | None = None
    reject_reason: str | None = None


class ReviewEvidenceInput(BaseModel):
    field_key: str = Field(min_length=2, max_length=40)
    claim: str = Field(min_length=3, max_length=4000)
    url: str = Field(min_length=8, max_length=2000)
    verification_status: str = "UNVERIFIED"


class SourceConfigInput(BaseModel):
    enabled: bool | None = None
    cadence_minutes: int | None = Field(default=None, ge=15, le=10080)


REVIEW_FIELDS = set(ReviewInput.model_fields) - {"manual_status"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    stop = asyncio.Event()
    task = asyncio.create_task(monitor_loop(stop))
    try:
        yield
    finally:
        stop.set()
        await task


app = FastAPI(title="Beta Project Intelligence", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/static/index.html", encoding="utf-8") as f: return f.read()


@app.get("/api/projects")
def projects(stage: str | None = None, q: str | None = None, watchlist: bool = False, limit: int = Query(500, ge=1, le=1000)):
    sql = "SELECT p.*, r.level1_status, r.level1_reason, r.level2_status, r.verification_status, r.translated_description, r.score_rationale, r.manual_status, (SELECT GROUP_CONCAT(DISTINCT s.name) FROM project_sources ps JOIN sources s ON s.id=ps.source_id WHERE ps.project_id=p.id) AS source_names, (SELECT COUNT(*) FROM project_sources ps WHERE ps.project_id=p.id) AS signal_count, (SELECT COUNT(*) FROM funding_rounds fr WHERE fr.project_id=p.id) AS funding_count FROM projects p LEFT JOIN project_reviews r ON r.project_id=p.id WHERE 1=1"
    args: list = []
    if stage: sql += " AND p.stage=?"; args.append(stage)
    if q: sql += " AND (p.name LIKE ? OR p.description LIKE ? OR p.category LIKE ?)"; args.extend([f"%{q}%"]*3)
    if watchlist: sql += " AND p.watchlisted=1"
    sql += " ORDER BY p.last_updated DESC LIMIT ?"; args.append(limit)
    with connect() as db: return [dict(r) for r in db.execute(sql, args)]


@app.get("/api/projects/{project_id}")
def project_detail(project_id: int):
    with connect() as db:
        project = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project: raise HTTPException(404, "Project not found")
        result = dict(project)
        result["signals"] = [dict(r) for r in db.execute("SELECT ps.*,s.name AS source_name FROM project_sources ps JOIN sources s ON s.id=ps.source_id WHERE ps.project_id=? ORDER BY ps.discovered_at DESC", (project_id,))]
        result["events"] = [dict(r) for r in db.execute("SELECT * FROM project_events WHERE project_id=? ORDER BY created_at DESC", (project_id,))]
        result["funding"] = [dict(r) for r in db.execute("SELECT fr.*,i.name AS investor FROM funding_rounds fr LEFT JOIN investors i ON i.id=fr.investor_id WHERE fr.project_id=?", (project_id,))]
        result["requirements"] = [dict(r) for r in db.execute("SELECT * FROM requirements WHERE project_id=?", (project_id,))]
        result["founders"] = [dict(r) for r in db.execute("SELECT * FROM founders WHERE project_id=?", (project_id,))]
        result["grants"] = [dict(r) for r in db.execute("SELECT * FROM grants WHERE project_id=?", (project_id,))]
        result["campaigns"] = [dict(r) for r in db.execute("SELECT * FROM campaigns WHERE project_id=?", (project_id,))]
        result["waitlists"] = [dict(r) for r in db.execute("SELECT * FROM waitlists WHERE project_id=?", (project_id,))]
        result["review_evidence"] = [dict(r) for r in db.execute("SELECT * FROM review_evidence WHERE project_id=? ORDER BY field_key,checked_at DESC", (project_id,))]
        review = db.execute("SELECT * FROM project_reviews WHERE project_id=?", (project_id,)).fetchone()
        result["review"] = dict(review) if review else None
        result["raw_items"] = [dict(r) for r in db.execute("SELECT title,url,published_at,fetched_at FROM raw_items WHERE project_id=? ORDER BY fetched_at DESC LIMIT 50", (project_id,))]
        return result


@app.post("/api/projects/{project_id}/watchlist")
def toggle_watchlist(project_id: int):
    with connect() as db:
        row = db.execute("SELECT watchlisted FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row: raise HTTPException(404, "Project not found")
        value = 0 if row[0] else 1
        db.execute("UPDATE projects SET watchlisted=? WHERE id=?", (value, project_id))
        if value: db.execute("INSERT OR IGNORE INTO user_watchlist(project_id,added_at) VALUES(?,?)", (project_id, now()))
        else: db.execute("DELETE FROM user_watchlist WHERE project_id=?", (project_id,))
    return {"watchlisted": bool(value)}


@app.get("/api/sources")
def sources():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT s.*, (SELECT status FROM monitoring_runs mr WHERE mr.source_id=s.id ORDER BY mr.id DESC LIMIT 1) AS last_run_status, (SELECT error FROM monitoring_runs mr WHERE mr.source_id=s.id ORDER BY mr.id DESC LIMIT 1) AS last_run_error FROM sources s ORDER BY source_group,kind,name")]


@app.patch("/api/sources/{source_id}")
def configure_source(source_id: int, data: SourceConfigInput):
    values = data.model_dump(exclude_unset=True)
    if not values: raise HTTPException(400, "No source settings supplied")
    with connect() as db:
        source = db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if not source: raise HTTPException(404, "Source not found")
        supported = source["kind"] == "RSS" and bool(source["url"]) or source["name"] == "GitHub Repository Search"
        if values.get("enabled") is True and not supported:
            raise HTTPException(422, "This source has no implemented connector. Its registry status cannot be changed to active.")
        if "enabled" in values:
            if values["enabled"] and source["status"] not in {"ACTIVE", "NEEDS VALIDATION", "ERROR"}:
                raise HTTPException(422, "Resolve required access or validation before enabling this source")
            db.execute("UPDATE sources SET enabled=? WHERE id=?", (int(values["enabled"]), source_id))
        if "cadence_minutes" in values:
            db.execute("UPDATE sources SET cadence_minutes=? WHERE id=?", (values["cadence_minutes"], source_id))
    return {"saved": True, "source_id": source_id}


@app.get("/api/events")
def events(limit: int = Query(60, ge=1, le=200)):
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT e.*,p.name AS project_name FROM project_events e JOIN projects p ON p.id=e.project_id ORDER BY e.created_at DESC LIMIT ?", (limit,))]


@app.post("/api/collect")
async def collect():
    return await asyncio.to_thread(run_manual_scan)


@app.get("/api/monitoring/runs")
def monitoring_runs(limit: int = Query(100, ge=1, le=500)):
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT mr.*,s.name AS source_name FROM monitoring_runs mr LEFT JOIN sources s ON s.id=mr.source_id ORDER BY mr.id DESC LIMIT ?", (limit,))]


@app.post("/api/review/screen")
async def initial_screening():
    return await asyncio.to_thread(screen_projects)


@app.get("/api/review/queue")
def review_queue(status: str | None = None, limit: int = Query(500, ge=1, le=1000)):
    with connect() as db:
        sql = "SELECT p.id,p.name,p.website,p.category,p.ecosystem,p.stage,p.description,p.first_seen,p.last_updated,p.opportunity_score,p.confidence,r.level1_status,r.level1_reason,r.level2_status,r.verification_status,r.manual_status,r.updated_at FROM projects p JOIN project_reviews r ON r.project_id=p.id WHERE 1=1"
        args: list = []
        if status:
            sql += " AND r.level1_status=?"; args.append(status.upper())
        sql += " ORDER BY CASE r.level1_status WHEN 'PASS' THEN 0 WHEN 'REVIEW' THEN 1 ELSE 2 END, p.opportunity_score DESC, p.name LIMIT ?"; args.append(limit)
        return [dict(r) for r in db.execute(sql, args)]


@app.get("/api/review/runs")
def review_runs(limit: int = Query(50, ge=1, le=200)):
    with connect() as db: return [dict(r) for r in db.execute("SELECT * FROM analysis_runs ORDER BY id DESC LIMIT ?", (limit,))]


@app.get("/api/my-top-projects")
def my_top_projects(limit: int = Query(50, ge=1, le=100)):
    with connect() as db:
        return [dict(r) for r in db.execute("""SELECT p.*,r.level1_status,r.level2_status,r.verification_status,r.translated_description,
          r.team_summary,r.product_summary,r.funding_summary,r.participation_summary,r.entry_cost,r.deadline,
          r.opportunity,r.risks,r.analyst_conclusion,r.score,r.evidence_confidence,r.score_rationale,r.updated_at,
          (SELECT GROUP_CONCAT(DISTINCT i.name) FROM funding_rounds fr JOIN investors i ON i.id=fr.investor_id WHERE fr.project_id=p.id) AS investors
          FROM projects p JOIN project_reviews r ON r.project_id=p.id
          WHERE r.level1_status='PASS' AND r.level2_status='COMPLETE' AND r.verification_status='VERIFIED'
            AND COALESCE(r.score,0)>=60 AND COALESCE(r.evidence_confidence,0)>=60 AND r.manual_status!='REJECTED'
          ORDER BY r.score DESC,r.evidence_confidence DESC,p.name LIMIT ?""", (limit,))]


@app.post("/api/projects/{project_id}/translation")
def save_translation(project_id: int, data: TranslationInput):
    with connect() as db:
        if not db.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone(): raise HTTPException(404, "Project not found")
        db.execute("UPDATE project_reviews SET translated_description=?,updated_at=? WHERE project_id=?", (data.translated_description, now(), project_id))
    return {"saved": True, "project_id": project_id}


@app.patch("/api/projects/{project_id}/review")
def update_review(project_id: int, data: ReviewInput):
    values = data.model_dump(exclude_unset=True)
    allowed = {
        "manual_status": {"NONE", "APPROVED", "WATCH", "LATER", "REJECTED", "REVIEWED"},
        "level2_status": {"NOT STARTED", "IN PROGRESS", "COMPLETE"},
        "verification_status": {"VERIFIED", "PARTIALLY VERIFIED", "UNVERIFIED", "CONTRADICTED", "STALE"},
    }
    for key, valid in allowed.items():
        if key in values and values[key] not in valid: raise HTTPException(422, f"Invalid {key}")
    if any(value is not None and len(value) > 12000 for value in values.values() if isinstance(value, str)):
        raise HTTPException(422, "Review fields must be 12,000 characters or fewer")
    if not values: raise HTTPException(400, "No review fields provided")
    values["updated_at"] = now()
    with connect() as db:
        if not db.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone(): raise HTTPException(404, "Project not found")
        if values.get("verification_status") == "VERIFIED":
            total = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=?", (project_id,)).fetchone()[0]
            unverified = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND verification_status!='VERIFIED'", (project_id,)).fetchone()[0]
            if total < 3 or unverified:
                raise HTTPException(422, "Mark VERIFIED only after at least three evidence records are individually VERIFIED")
        if values.get("level2_status") == "COMPLETE":
            merged = dict(db.execute("SELECT * FROM project_reviews WHERE project_id=?", (project_id,)).fetchone())
            merged.update(values)
            required = ("team_summary", "product_summary", "funding_summary", "participation_summary", "risks", "analyst_conclusion")
            if any(not (merged.get(field) or "").strip() for field in required):
                raise HTTPException(422, "Deep review needs an explicit value or UNKNOWN for team, product, funding, participation, risks, and conclusion")
            evidence_count = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=?", (project_id,)).fetchone()[0]
            if evidence_count < 3:
                raise HTTPException(422, "Deep review needs at least three linked evidence records before completion")
            for field, evidence_key in (("team_summary", "team"), ("product_summary", "product"), ("funding_summary", "funding"), ("participation_summary", "participation"), ("risks", "risks")):
                if not merged.get(field, "").strip().upper().startswith("UNKNOWN"):
                    if not db.execute("SELECT 1 FROM review_evidence WHERE project_id=? AND field_key=? LIMIT 1", (project_id, evidence_key)).fetchone():
                        raise HTTPException(422, f"Add linked {evidence_key} evidence or explicitly mark that field UNKNOWN")
        sets = ",".join(f"{key}=?" for key in values)
        db.execute(f"UPDATE project_reviews SET {sets} WHERE project_id=?", (*values.values(), project_id))
    from .screening import score_project
    score_project(project_id)
    return {"saved": True, "project_id": project_id}


@app.post("/api/projects/{project_id}/review/evidence")
def add_review_evidence(project_id: int, data: ReviewEvidenceInput):
    from urllib.parse import urlparse
    parsed = urlparse(data.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc: raise HTTPException(422, "Evidence URL must use HTTP or HTTPS")
    if data.field_key not in {"team", "product", "funding", "participation", "risks", "opportunity", "technology", "documentation", "ecosystem", "deadline", "social", "security"}:
        raise HTTPException(422, "Unknown evidence field")
    if data.verification_status not in {"VERIFIED", "PARTIALLY VERIFIED", "UNVERIFIED", "CONTRADICTED", "STALE"}:
        raise HTTPException(422, "Invalid verification status")
    with connect() as db:
        if not db.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone(): raise HTTPException(404, "Project not found")
        db.execute("INSERT INTO review_evidence(project_id,field_key,claim,url,verification_status,checked_at) VALUES(?,?,?,?,?,?) ON CONFLICT(project_id,field_key,url) DO UPDATE SET claim=excluded.claim,verification_status=excluded.verification_status,checked_at=excluded.checked_at",
                   (project_id, data.field_key, data.claim, data.url, data.verification_status, now()))
    from .screening import score_project
    score_project(project_id)
    return {"saved": True, "project_id": project_id}


@app.get("/api/export.json")
def export_json():
    with connect() as db:
        data = []
        for row in db.execute("SELECT * FROM projects ORDER BY name"):
            item = dict(row); pid = item["id"]
            item["signals"] = [dict(r) for r in db.execute("SELECT s.name AS source,ps.title,ps.url,ps.published_at,ps.discovered_at FROM project_sources ps JOIN sources s ON s.id=ps.source_id WHERE ps.project_id=?", (pid,))]
            item["events"] = [dict(r) for r in db.execute("SELECT event_type,summary,evidence_url,created_at FROM project_events WHERE project_id=?", (pid,))]
            data.append(item)
    return JSONResponse(data, headers={"Content-Disposition": "attachment; filename=beta-projects.json"})


@app.get("/api/export.csv")
def export_csv():
    with connect() as db: rows = [dict(r) for r in db.execute("SELECT name,website,category,ecosystem,stage,first_seen,last_updated,opportunity_score,confidence,participation,cost,description FROM projects ORDER BY name")]
    output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=list(rows[0]) if rows else ["name", "website", "category", "ecosystem", "stage", "first_seen", "last_updated", "opportunity_score", "confidence", "participation", "cost", "description"])
    writer.writeheader(); writer.writerows(rows)
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=beta-projects.csv"})


@app.get("/api/health")
def health():
    with connect() as db:
        return {"app": "beta-project-intelligence", "status": "ok", "projects": db.execute("SELECT COUNT(*) FROM projects").fetchone()[0], "database": "SQLite", "active_sources": db.execute("SELECT COUNT(*) FROM sources WHERE status='ACTIVE' AND enabled=1").fetchone()[0], "top_projects": db.execute("SELECT COUNT(*) FROM project_reviews WHERE level1_status='PASS' AND level2_status='COMPLETE' AND verification_status='VERIFIED' AND COALESCE(score,0)>=60 AND COALESCE(evidence_confidence,0)>=60").fetchone()[0]}
