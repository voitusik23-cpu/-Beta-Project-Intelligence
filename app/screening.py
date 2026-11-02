from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from .database import connect
from .discovery import now

SPAM_MARKERS = (
    "auto-claim bot", "daily claimer", "airdrop bot", "multi-wallet", "faucet bot",
    "auto-farm", "autofarm", "claim tool", "auto bridge", "token deploy tools",
    "daily airdrops", "crypto professor", "airdrop alpha",
)
EDITORIAL_MARKERS = (
    "protocol update", "protocol cluster updates", "announcement", "program recap",
    "cohort ", "tickets are live", "celebrating ", "internship", "checkpoint #",
    "shutdown announcement", "security alert", "allocation update", "what is ",
)
OPPORTUNITY_MARKERS = (
    "applications are open", "apply now", "open to public participation", "join the testnet",
    "waitlist is open", "registration is open", "public beta", "testnet is live",
    "grant program", "applications rolling", "open challenge", "bounty",
)
PRODUCT_MARKERS = (
    "live on ethereum mainnet", "runs on ethereum mainnet today", "is live on mainnet",
    "public testnet", "public beta", "launches today", "is now live", "open challenge",
    "mainnet is live", "live on mainnet", "publicly available", "autoresearch challenge",
)


def classify_project(project: dict, sources: list[str], evidence_count: int) -> tuple[str, str]:
    name = (project.get("name") or "").lower().replace("-", " ").replace("_", " ")
    description = (project.get("description") or "").lower()
    text = f"{name} {description}"
    source_set = set(sources)

    if not evidence_count:
        return "REJECTED", "Нет ссылок на исходные публикации; карточка не проверяема."
    if any(marker in text for marker in SPAM_MARKERS):
        return "REJECTED", "Автоматизация клейма/фарминга или массовой активности; исключено из списка проектов для участия."
    if any(marker in name for marker in ("faucet", "node guide", "checkin", "fullstack dapp", "console", "explorer", "devnet-config", "kurtosis", "dispenser", "devnet suite")):
        return "REJECTED", "Репозиторий-инструмент, учебный пример или каталог, а не самостоятельная возможность участия в проекте."

    has_github = "GitHub Repository Search" in source_set
    has_site = bool(project.get("website") and project["website"].startswith(("http://", "https://")))
    is_ef_article = bool(source_set) and source_set.issubset({"Ethereum Blog RSS", "Ethereum Foundation Ecosystem Support"})
    has_opportunity = any(marker in text for marker in OPPORTUNITY_MARKERS)
    product_signal = any(marker in text for marker in PRODUCT_MARKERS)

    tool_markers = (
        "kurtosis package", "blockchain explorer", "local testnet", "local devnet",
        "node guide", "step-by-step guide", "faucet dashboard", "developer tooling",
        "learning project", "educational project", "testnet configuration repository",
    )
    if any(marker in text for marker in tool_markers):
        return "REJECTED", "Разработческий инструмент, учебный проект или инструкция; нет отдельной возможности участия для пользователя."

    published = project.get("latest_published_at")
    if is_ef_article and not has_site and published:
        try:
            published_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if published_date.tzinfo is None: published_date = published_date.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - published_date > timedelta(days=365):
                return "REJECTED", "Архивная публикация старше года без отдельного сайта, подтверждённого текущего продукта или доступной возможности участия; исходная ссылка сохранена."
        except (TypeError, ValueError):
            pass

    if is_ef_article and not has_site and not has_opportunity and not product_signal and any(marker in text for marker in EDITORIAL_MARKERS):
        return "REJECTED", "Публикация/обновление Ethereum Foundation без отдельного проекта или открытого действия для пользователя."
    if is_ef_article and not has_site and not has_opportunity and not product_signal:
        return "REJECTED", "Новостная или исследовательская статья без отдельного проекта, действующего продукта или открытого участия."
    prototype = any(marker in text for marker in ("prototype", "experimental", "learning project", "hackathon", "demo app", "read-only planner"))
    host = project["website"].lower().split("/")[2] if has_site else ""
    repo_document = host == "github.com" or host == "www.github.com"
    generic_hosting = bool(host and re.search(r"(\.vercel\.app|\.github\.io|\.netlify\.app|\.pages\.dev|\.web\.app)$", host))
    if has_github and has_site and not prototype and not generic_hosting and not repo_document:
        return "PASS", "Есть сайт и исходный репозиторий; проверяются актуальность продукта, команда, условия и официальные каналы."
    if has_github and has_site and (prototype or generic_hosting or repo_document):
        return "REVIEW", "Найден работающий сайт/репозиторий, но это ранний прототип или размещение на общем хостинге; требуется независимая проверка проекта."
    if has_opportunity and evidence_count:
        return "REVIEW", "Есть сигнал о регистрации, тестировании или грантовой возможности; требуется проверить статус и условия."
    if has_github:
        return "REVIEW", "Есть репозиторий, но независимый официальный сайт или масштаб продукта не подтверждён."
    if has_site:
        return "REVIEW", "Есть сайт и источник, но сведения о команде, продукте и текущем участии требуют подтверждения."
    return "REVIEW", "Сохранено для ручной проверки: карточка пока не содержит достаточных независимых подтверждений."


def screen_projects(batch_size: int = 40) -> dict:
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        resumable = db.execute("SELECT * FROM analysis_runs WHERE run_type='INITIAL' AND status IN ('RUNNING','ERROR') AND completed<total ORDER BY id DESC LIMIT 1").fetchone()
        if resumable:
            run_id = resumable["id"]
            db.execute("UPDATE analysis_runs SET status='RUNNING',total=?,updated_at=?,error=NULL WHERE id=?", (total, now(), run_id))
            projects = [dict(row) for row in db.execute("SELECT p.* FROM projects p JOIN project_reviews r ON r.project_id=p.id WHERE r.level1_status='PENDING' OR r.score IS NULL ORDER BY p.id")]
        else:
            cursor = db.execute("INSERT INTO analysis_runs(run_type,stage,status,total,completed,started_at,updated_at) VALUES('INITIAL','LEVEL 1','RUNNING',?,0,?,?)", (total, now(), now()))
            run_id = cursor.lastrowid
            projects = [dict(row) for row in db.execute("SELECT * FROM projects ORDER BY id")]
        pending_count = len(projects)
        already_done = max(0, total - pending_count)
        db.execute("UPDATE analysis_runs SET completed=?,updated_at=? WHERE id=?", (already_done, now(), run_id))

    completed = 0
    try:
        for offset in range(0, len(projects), max(1, batch_size)):
            batch = projects[offset:offset + max(1, batch_size)]
            with connect() as db:
                for project in batch:
                    source_rows = db.execute("SELECT DISTINCT s.name FROM project_sources ps JOIN sources s ON s.id=ps.source_id WHERE ps.project_id=?", (project["id"],)).fetchall()
                    sources = [row[0] for row in source_rows]
                    evidence_count = db.execute("SELECT COUNT(*) FROM project_sources WHERE project_id=?", (project["id"],)).fetchone()[0]
                    latest = db.execute("SELECT MAX(COALESCE(published_at,discovered_at)) FROM project_sources WHERE project_id=?", (project["id"],)).fetchone()[0]
                    project["latest_published_at"] = latest
                    status, reason = classify_project(project, sources, evidence_count)
                    db.execute("UPDATE project_reviews SET level1_status=?,level1_reason=?,updated_at=? WHERE project_id=?", (status, reason, now(), project["id"]))
            for project in batch:
                score_project(project["id"])
            completed += len(batch)
            with connect() as db:
                db.execute("UPDATE analysis_runs SET completed=?,updated_at=? WHERE id=?", (min(total, already_done + completed), now(), run_id))
        with connect() as db:
            counts = {row[0]: row[1] for row in db.execute("SELECT level1_status,COUNT(*) FROM project_reviews GROUP BY level1_status")}
            db.execute("UPDATE analysis_runs SET status='COMPLETE',stage='LEVEL 1 COMPLETE',updated_at=? WHERE id=?", (now(), run_id))
        return {"run_id": run_id, "total": len(projects), "counts": counts}
    except Exception as exc:
        with connect() as db:
            db.execute("UPDATE analysis_runs SET status='ERROR',updated_at=?,error=? WHERE id=?", (now(), str(exc)[:1000], run_id))
        raise


def score_project(project_id: int) -> dict:
    """Score only evidence entered in the structured dossier; unknown facts earn no points."""
    with connect() as db:
        project = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        review = db.execute("SELECT * FROM project_reviews WHERE project_id=?", (project_id,)).fetchone()
        if not project or not review:
            raise ValueError("Project review record not found")
        funding = db.execute("SELECT COUNT(*) FROM funding_rounds WHERE project_id=? AND evidence_url!=''", (project_id,)).fetchone()[0]
        founders = db.execute("SELECT COUNT(*) FROM founders WHERE project_id=? AND evidence_url IS NOT NULL AND evidence_url!=''", (project_id,)).fetchone()[0]
        requirements = [dict(row) for row in db.execute("SELECT * FROM requirements WHERE project_id=?", (project_id,))]
        sources = [row[0] for row in db.execute("SELECT DISTINCT s.name FROM project_sources ps JOIN sources s ON s.id=ps.source_id WHERE ps.project_id=?", (project_id,))]
        product_evidence = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND field_key='product' AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        funding_verified = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND field_key='funding' AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        team_verified = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND field_key='team' AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        ecosystem_evidence = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND field_key='ecosystem' AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        participation_evidence = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND field_key='participation' AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        documentation_evidence = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND field_key='documentation' AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        cutoff = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()
        recent_repo = db.execute("SELECT COUNT(*) FROM project_sources ps JOIN sources s ON s.id=ps.source_id WHERE ps.project_id=? AND s.name='GitHub Repository Search' AND COALESCE(ps.published_at,ps.discovered_at)>=?", (project_id, cutoff)).fetchone()[0]

        components = {
            "funding": 20 if funding and funding_verified else 0,
            "team": 15 if founders and team_verified else 0,
            "product": 15 if product_evidence and review["product_summary"] else 0,
            "free_participation": 15 if participation_evidence and any((r.get("cost") or "").strip().lower() in {"free", "0", "0 usd", "free; no gas"} and r.get("evidence_url") for r in requirements) else 0,
            "technical_activity": 10 if recent_repo else 0,
            "early_stage": 10 if review["verification_status"] == "VERIFIED" and project["stage"] in {"Waitlist", "Testnet", "Participation", "Beta", "Discovered"} else 0,
            "documentation": 5 if documentation_evidence and any(r.get("kind") == "documentation" and r.get("evidence_url") for r in requirements) else 0,
            "ecosystem": 10 if ecosystem_evidence and project["ecosystem"] else 0,
        }
        score = sum(components.values())
        evidence_count = db.execute("SELECT COUNT(*) FROM project_sources WHERE project_id=?", (project_id,)).fetchone()[0]
        verified_count = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND verification_status='VERIFIED'", (project_id,)).fetchone()[0]
        partial_count = db.execute("SELECT COUNT(*) FROM review_evidence WHERE project_id=? AND verification_status='PARTIALLY VERIFIED'", (project_id,)).fetchone()[0]
        confidence = min(100, min(20, evidence_count * 3) + verified_count * 15 + partial_count * 6)
        rationale = "; ".join(f"{key} {value}/{limit}" for key, value, limit in [
            ("подтверждённое финансирование", components["funding"], 20), ("команда", components["team"], 15),
            ("продукт", components["product"], 15), ("бесплатное участие", components["free_participation"], 15),
            ("техническая активность", components["technical_activity"], 10), ("ранняя стадия", components["early_stage"], 10),
            ("документация", components["documentation"], 5), ("экосистема", components["ecosystem"], 10)])
        previous = (project["opportunity_score"], project["confidence"])
        db.execute("UPDATE project_reviews SET score=?,evidence_confidence=?,score_rationale=?,updated_at=? WHERE project_id=?", (score, confidence, rationale, now(), project_id))
        if previous != (score, confidence):
            db.execute("INSERT INTO project_scores(project_id,score,confidence,rationale,created_at) VALUES(?,?,?,?,?)", (project_id, score, confidence, rationale, now()))
        db.execute("UPDATE projects SET opportunity_score=?,confidence=? WHERE id=?", (score, confidence, project_id))
        return {"score": score, "confidence": confidence, "components": components, "rationale": rationale}
