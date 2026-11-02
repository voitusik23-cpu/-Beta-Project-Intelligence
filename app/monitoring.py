from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from .database import connect
from .discovery import collect_github, collect_rss_source, now


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def run_source(source_id: int) -> dict:
    started = now()
    with connect() as db:
        source = db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if not source:
            return {"source_id": source_id, "status": "ERROR", "error": "Source not found."}
        cursor = db.execute("INSERT INTO monitoring_runs(source_id,started_at,status) VALUES(?,?,'RUNNING')", (source_id, started))
        run_id = cursor.lastrowid
        name, kind, enabled = source["name"], source["kind"], source["enabled"]
    try:
        if kind == "RSS":
            result = collect_rss_source(source_id)
        elif name == "GitHub Repository Search":
            result = collect_github()
        else:
            result = {"source_count": 0, "new_projects_or_signals": 0, "errors": ["No implemented connector for this source."]}
        errors = result.get("errors", [])
        status = "ERROR" if errors else "SUCCESS"
        error = "; ".join(errors)[:1500] if errors else None
        with connect() as db:
            db.execute("UPDATE monitoring_runs SET finished_at=?,status=?,items_found=?,new_signals=?,error=? WHERE id=?",
                       (now(), status, result.get("items_found", result.get("new_projects_or_signals", 0)), result.get("new_projects_or_signals", 0), error, run_id))
            if not errors:
                db.execute("UPDATE sources SET status='ACTIVE',enabled=1,last_checked=?,detail=? WHERE id=?",
                           (now(), "Last check completed successfully.", source_id))
            elif source["status"] not in {"API REQUIRED", "ACCESS REQUIRED", "DISABLED"}:
                db.execute("UPDATE sources SET status='ERROR',last_checked=?,detail=? WHERE id=?", (now(), error, source_id))
        return {"source_id": source_id, "source": name, "status": status, "result": result}
    except Exception as exc:
        error = str(exc)[:1500]
        with connect() as db:
            db.execute("UPDATE monitoring_runs SET finished_at=?,status='ERROR',error=? WHERE id=?", (now(), error, run_id))
            db.execute("UPDATE sources SET status='ERROR',last_checked=?,detail=? WHERE id=?", (now(), error, source_id))
        return {"source_id": source_id, "source": name, "status": "ERROR", "error": error}


def run_manual_scan() -> dict:
    with connect() as db:
        rows = db.execute("SELECT id FROM sources WHERE status IN ('ACTIVE','NEEDS VALIDATION','ERROR') AND (kind='RSS' OR name='GitHub Repository Search') AND url IS NOT NULL ORDER BY kind,name").fetchall()
    results = [run_source(row["id"]) for row in rows]
    return {"checked_at": now(), "source_count": len(results), "sources": results,
            "new_projects_or_signals": sum((r.get("result") or {}).get("new_projects_or_signals", 0) for r in results),
            "errors": [r.get("error") or "; ".join((r.get("result") or {}).get("errors", [])) for r in results if r["status"] == "ERROR"]}


async def monitor_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        with connect() as db:
            rows = [dict(row) for row in db.execute("SELECT id,cadence_minutes,last_checked FROM sources WHERE enabled=1 AND status='ACTIVE' AND cadence_minutes>0 AND (kind='RSS' OR name='GitHub Repository Search')")]
        current = datetime.now(timezone.utc)
        for row in rows:
            checked = _parse_time(row["last_checked"])
            due = checked is None or current - checked >= timedelta(minutes=max(15, row["cadence_minutes"]))
            if due:
                await asyncio.to_thread(run_source, row["id"])
        try:
            await asyncio.wait_for(stop.wait(), timeout=30)
        except asyncio.TimeoutError:
            pass
