from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from .source_catalog import SOURCE_CATALOG

DATA_DIR = Path(os.environ.get("BPI_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DB_PATH = DATA_DIR / "beta_intelligence.sqlite3"


class ClosingConnection(sqlite3.Connection):
    """Make SQLite's transaction context also release the file handle on Windows."""
    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=20, factory=ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, normalized_name TEXT NOT NULL UNIQUE,
          website TEXT, description TEXT, category TEXT DEFAULT 'Unclassified', ecosystem TEXT,
          stage TEXT DEFAULT 'Discovered', first_seen TEXT NOT NULL, last_updated TEXT NOT NULL,
          opportunity_score INTEGER DEFAULT 0, confidence INTEGER DEFAULT 0,
          participation TEXT DEFAULT 'Unknown', cost TEXT DEFAULT 'Unknown', watchlisted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sources (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
          url TEXT, status TEXT NOT NULL DEFAULT 'Not configured', detail TEXT,
          last_checked TEXT, source_group TEXT DEFAULT 'Other', cadence_minutes INTEGER DEFAULT 0,
          enabled INTEGER NOT NULL DEFAULT 0, access_required TEXT
        );
        CREATE TABLE IF NOT EXISTS project_sources (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          source_id INTEGER NOT NULL REFERENCES sources(id), title TEXT, url TEXT NOT NULL,
          published_at TEXT, discovered_at TEXT NOT NULL, UNIQUE(source_id,url)
        );
        CREATE TABLE IF NOT EXISTS project_events (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          event_type TEXT NOT NULL, summary TEXT NOT NULL, evidence_url TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS investors (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, website TEXT
        );
        CREATE TABLE IF NOT EXISTS funding_rounds (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          investor_id INTEGER REFERENCES investors(id), amount TEXT, round_type TEXT, date TEXT,
          evidence_url TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS requirements (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          kind TEXT NOT NULL, details TEXT, cost TEXT DEFAULT 'Unknown', evidence_url TEXT
        );
        CREATE TABLE IF NOT EXISTS founders (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          name TEXT NOT NULL, profile_url TEXT, previous_projects TEXT, evidence_url TEXT
        );
        CREATE TABLE IF NOT EXISTS grants (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          provider TEXT NOT NULL, amount TEXT, date TEXT, evidence_url TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ecosystems (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, website TEXT
        );
        CREATE TABLE IF NOT EXISTS campaigns (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          title TEXT NOT NULL, kind TEXT, url TEXT, starts_at TEXT, ends_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS waitlists (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          url TEXT NOT NULL, status TEXT, evidence_url TEXT
        );
        CREATE TABLE IF NOT EXISTS project_scores (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          score INTEGER NOT NULL, confidence INTEGER NOT NULL, rationale TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_watchlist (
          project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
          added_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS raw_items (
          id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id), item_key TEXT NOT NULL UNIQUE,
          title TEXT, content TEXT, url TEXT NOT NULL, published_at TEXT, fetched_at TEXT NOT NULL,
          payload_json TEXT, project_id INTEGER REFERENCES projects(id)
        );
        CREATE TABLE IF NOT EXISTS monitoring_runs (
          id INTEGER PRIMARY KEY, source_id INTEGER REFERENCES sources(id), started_at TEXT NOT NULL,
          finished_at TEXT, status TEXT NOT NULL, items_found INTEGER DEFAULT 0,
          new_signals INTEGER DEFAULT 0, error TEXT
        );
        CREATE TABLE IF NOT EXISTS project_reviews (
          project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
          level1_status TEXT NOT NULL DEFAULT 'PENDING', level1_reason TEXT,
          verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED', level2_status TEXT NOT NULL DEFAULT 'NOT STARTED',
          translated_description TEXT, team_summary TEXT, product_summary TEXT, funding_summary TEXT,
          participation_summary TEXT, entry_cost TEXT DEFAULT 'UNKNOWN', deadline TEXT,
          opportunity TEXT, risks TEXT, analyst_conclusion TEXT, score INTEGER,
          evidence_confidence INTEGER DEFAULT 0, score_rationale TEXT, updated_at TEXT,
          manual_status TEXT NOT NULL DEFAULT 'NONE', user_notes TEXT,
          reject_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS project_aliases (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          alias TEXT NOT NULL, normalized_alias TEXT NOT NULL UNIQUE, evidence_url TEXT
        );
        CREATE TABLE IF NOT EXISTS analysis_runs (
          id INTEGER PRIMARY KEY, run_type TEXT NOT NULL, stage TEXT NOT NULL,
          status TEXT NOT NULL, total INTEGER DEFAULT 0, completed INTEGER DEFAULT 0,
          started_at TEXT NOT NULL, updated_at TEXT NOT NULL, error TEXT
        );
        CREATE TABLE IF NOT EXISTS review_evidence (
          id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
          field_key TEXT NOT NULL, claim TEXT NOT NULL, url TEXT NOT NULL,
          verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED', checked_at TEXT NOT NULL,
          UNIQUE(project_id,field_key,url)
        );
        CREATE INDEX IF NOT EXISTS idx_project_sources_project ON project_sources(project_id);
        CREATE INDEX IF NOT EXISTS idx_events_project ON project_events(project_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_raw_items_project ON raw_items(project_id, fetched_at DESC);
        CREATE INDEX IF NOT EXISTS idx_monitoring_runs_source ON monitoring_runs(source_id, started_at DESC);
        CREATE INDEX IF NOT EXISTS idx_reviews_rank ON project_reviews(level1_status, level2_status, score DESC);
        CREATE INDEX IF NOT EXISTS idx_review_evidence_project ON review_evidence(project_id,field_key);
        """)

        # Additive migration: preserve existing source rows and project data.
        source_columns = {row[1] for row in db.execute("PRAGMA table_info(sources)")}
        for column, declaration in {
            "source_group": "TEXT DEFAULT 'Other'",
            "cadence_minutes": "INTEGER DEFAULT 0",
            "enabled": "INTEGER NOT NULL DEFAULT 0",
            "access_required": "TEXT",
        }.items():
            if column not in source_columns:
                db.execute(f"ALTER TABLE sources ADD COLUMN {column} {declaration}")

        # Mark legacy connectors from actual successful checks; placeholders remain disconnected.
        db.execute("UPDATE sources SET status='ACTIVE', enabled=1, cadence_minutes=120, source_group=CASE WHEN kind='RSS' THEN 'Technical sources' ELSE 'Technical sources' END WHERE status='Ready' AND last_checked IS NOT NULL AND name IN ('Ethereum Blog RSS','Ethereum Foundation Ecosystem Support','GitHub Repository Search')")
        db.execute("UPDATE sources SET status='DISABLED', enabled=0, detail=COALESCE(detail,'Connector is not configured.') WHERE status IN ('Ready','Not configured') AND last_checked IS NULL AND name IN ('RSS feeds','GitLab','Project websites / docs')")
        db.execute("UPDATE sources SET status='API REQUIRED', enabled=0 WHERE name IN ('Telegram','X / Twitter','Reddit') AND enabled=0")
        db.execute("UPDATE sources SET status='ACCESS REQUIRED', enabled=0 WHERE name='Discord' AND enabled=0")
        db.execute("UPDATE sources SET status='DISABLED', enabled=0 WHERE status='Not configured'")
        db.execute("UPDATE sources SET status='NEEDS VALIDATION', enabled=0 WHERE status='Ready' AND last_checked IS NULL")
        db.executemany(
            "INSERT OR IGNORE INTO sources(name,kind,url,status,detail,source_group,cadence_minutes,enabled,access_required) VALUES(?,?,?,?,?,?,?,?,?)",
            [(name, kind, url, status, detail, group, cadence, int(status == 'ACTIVE'), status if status in {'API REQUIRED','ACCESS REQUIRED'} else None)
             for name, group, kind, url, status, cadence, detail in SOURCE_CATALOG]
        )
        for name, group, kind, url, status, cadence, detail in SOURCE_CATALOG:
            db.execute("UPDATE sources SET source_group=?, cadence_minutes=?, detail=CASE WHEN last_checked IS NULL THEN ? ELSE detail END, url=COALESCE(url,?) WHERE name=? AND (last_checked IS NULL OR status NOT IN ('ACTIVE','ERROR'))",
                       (group, cadence, detail, url, name))

        # Legacy project_sources had a global UNIQUE(url), which prevented retaining
        # the same original URL as evidence from two distinct sources.
        link_sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='project_sources'").fetchone()[0]
        if "url TEXT NOT NULL UNIQUE" in link_sql:
            db.execute("CREATE TABLE project_sources_new (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE, source_id INTEGER NOT NULL REFERENCES sources(id), title TEXT, url TEXT NOT NULL, published_at TEXT, discovered_at TEXT NOT NULL, UNIQUE(source_id,url))")
            db.execute("INSERT OR IGNORE INTO project_sources_new(id,project_id,source_id,title,url,published_at,discovered_at) SELECT id,project_id,source_id,title,url,published_at,discovered_at FROM project_sources")
            db.execute("DROP TABLE project_sources")
            db.execute("ALTER TABLE project_sources_new RENAME TO project_sources")
            db.execute("CREATE INDEX IF NOT EXISTS idx_project_sources_project ON project_sources(project_id)")

        # Backfill existing links as raw-item stubs; the previous schema did not keep source bodies.
        db.execute("INSERT OR IGNORE INTO raw_items(source_id,item_key,title,content,url,published_at,fetched_at,payload_json,project_id) SELECT source_id,'legacy:'||source_id||':'||url,title,NULL,url,published_at,discovered_at,NULL,project_id FROM project_sources")
        db.execute("INSERT INTO monitoring_runs(source_id,started_at,finished_at,status,items_found,new_signals,error) SELECT id,last_checked,last_checked,'SUCCESS',0,0,NULL FROM sources s WHERE status='ACTIVE' AND last_checked IS NOT NULL AND NOT EXISTS(SELECT 1 FROM monitoring_runs mr WHERE mr.source_id=s.id)")

        # Ensure every legacy project has a review record so the screening queue is resumable.
        db.execute("INSERT OR IGNORE INTO project_reviews(project_id) SELECT id FROM projects")
        seeds = [
          ("Ethereum Blog RSS", "RSS", "https://blog.ethereum.org/feed.xml", "Ready", "Public RSS feed; projects are inferred from matched items."),
          ("Ethereum Foundation Ecosystem Support", "RSS", "https://blog.ethereum.org/en/feed.xml", "Ready", "Public RSS feed; may overlap with Ethereum Blog."),
          ("GitHub Repository Search", "GitHub API", "https://api.github.com/search/repositories", "Ready", "Public unauthenticated API; rate limits apply."),
          ("Telegram", "Social", None, "Not configured", "No Telegram API credentials or channel allowlist configured."),
          ("X / Twitter", "Social", None, "Not configured", "Requires an approved API integration."),
          ("Reddit", "Social", None, "Not configured", "Official API credentials are not configured."),
          ("Discord", "Social", None, "Not configured", "Bot/API integration is not configured."),
          ("Facebook / Instagram", "Social", None, "Not configured", "Official API access is not configured."),
          ("GitLab", "Code hosting", None, "Not configured", "Connector not implemented in MVP."),
          ("VC portfolios / funding", "Investment", None, "Not configured", "No official portfolio feeds configured; funding is never inferred as confirmed."),
          ("Project websites / docs", "Web", None, "Not configured", "No website crawler configured in MVP."),
          ("RSS feeds", "RSS", None, "Ready", "Configure additional public RSS URLs through BPI_RSS_FEEDS."),
        ]
        db.executemany("INSERT OR IGNORE INTO sources(name,kind,url,status,detail) VALUES(?,?,?,?,?)", seeds)


def rowdict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)
