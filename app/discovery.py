from __future__ import annotations

import email.utils
import hashlib
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .database import connect

UA = "BetaProjectIntelligence/0.1 (local research tool)"
TERMS = ["testnet", "devnet", "waitlist", "beta", "points", "airdrop", "launch", "protocol", "blockchain", "web3", "crypto", "rollup", "layer 2", "zk", "wallet", "defi", "incubation", "mainnet"]
GITHUB_QUERIES = ["web3 testnet", "crypto protocol beta", "blockchain devnet"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(3_000_000)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def infer_category(text: str) -> str:
    t = text.lower()
    for category, keys in [("Infrastructure", ("rollup", "layer 2", "bridge", "node", "rpc", "protocol")), ("DeFi", ("defi", "lending", "liquidity", "dex")), ("AI x Crypto", ("agent", "artificial intelligence", " ai ")), ("Gaming", ("game", "gaming")), ("Wallet", ("wallet", "account abstraction")), ("Developer Tools", ("developer", "sdk", "tooling"))]:
        if any(k in t for k in keys): return category
    return "Unclassified"


def infer_stage(text: str) -> tuple[str, str]:
    t = text.lower()
    if "waitlist" in t or "wait list" in t: return "Waitlist", "Waitlist mentioned; verify on official project page."
    if "testnet" in t or "devnet" in t: return "Testnet", "Testnet/devnet mentioned; verify current availability."
    if "points" in t or "quest" in t or "airdrop" in t: return "Participation", "Points/quest/airdrop mentioned; participation is not verified."
    if "beta" in t or "early access" in t: return "Beta", "Beta/early access mentioned; verify eligibility."
    if "mainnet" in t: return "Mainnet", "Mainnet mentioned; verify product status."
    return "Discovered", "Early-stage signal detected; stage needs verification."


def project_name(title: str, description: str, website: str | None = None) -> str:
    # Prefer a host label for GitHub repository candidates, otherwise use a concise title prefix.
    if website:
        host = urllib.parse.urlparse(website).netloc.lower().removeprefix("www.")
        if host and host not in {"github.com", "reddit.com"}: return host.split(".")[0].replace("-", " ").title()
    title = clean_text(title)
    title = re.sub(r"^(new|introducing|announcing|launching|how|why)\s+", "", title, flags=re.I)
    title = re.split(r"\s+[|:–—-]\s+", title)[0]
    words = title.split()[:5]
    return " ".join(words).strip(" .,:;-") or "Unknown project"


def upsert_signal(title: str, description: str, url: str, source_name: str, published: str | None = None, website: str | None = None) -> tuple[bool, int | None]:
    raw_title, raw_description = title, description
    title, description = clean_text(title), clean_text(description)
    if not title or not url: return False, None
    if not any(t in (title + " " + description).lower() for t in TERMS): return False, None
    name = project_name(title, description, website)
    normalized = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    if len(normalized) < 2: return False, None
    stage, event = infer_stage(title + " " + description)
    timestamp = now()
    with connect() as db:
        source = db.execute("SELECT id FROM sources WHERE name=?", (source_name,)).fetchone()
        if not source: return False, None
        existing_link = db.execute("SELECT project_id FROM project_sources WHERE source_id=? AND url=?", (source["id"], url)).fetchone()
        any_link = db.execute("SELECT project_id FROM project_sources WHERE url=? ORDER BY discovered_at LIMIT 1", (url,)).fetchone()
        project = db.execute("SELECT * FROM projects WHERE id=?", (any_link["project_id"],)).fetchone() if any_link else None
        if not project:
            project = db.execute("SELECT * FROM projects WHERE normalized_name=?", (normalized,)).fetchone()
        if existing_link:
            pid = existing_link["project_id"]
            db.execute("INSERT OR IGNORE INTO raw_items(source_id,item_key,title,content,url,published_at,fetched_at,payload_json,project_id) VALUES(?,?,?,?,?,?,?,?,?)",
                       (source["id"], hashlib.sha256(f"{source['id']}:{url}".encode()).hexdigest(), title[:500], description[:100000], url, published, timestamp, json.dumps({"title": raw_title, "description": raw_description}, ensure_ascii=False)[:200000], pid))
            return False, pid
        if project:
            pid = project["id"]
            db.execute("UPDATE projects SET last_updated=?, description=CASE WHEN length(?)>length(description) THEN ? ELSE description END, stage=CASE WHEN ?!='Discovered' THEN ? ELSE stage END, category=CASE WHEN category='Unclassified' THEN ? ELSE category END WHERE id=?", (timestamp, description, description, stage, stage, infer_category(title + " " + description), pid))
            ev = "New source signal"
        else:
            cur = db.execute("INSERT INTO projects(name,normalized_name,website,description,category,stage,first_seen,last_updated,confidence,participation,cost) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (name, normalized, website, description[:1600], infer_category(title + " " + description), stage, timestamp, timestamp, 35, "Unknown — check official source", "Unknown"))
            pid, ev = cur.lastrowid, "Project discovered"
        db.execute("INSERT OR IGNORE INTO project_sources(project_id,source_id,title,url,published_at,discovered_at) VALUES(?,?,?,?,?,?)", (pid, source["id"], title[:500], url, published, timestamp))
        db.execute("INSERT OR IGNORE INTO raw_items(source_id,item_key,title,content,url,published_at,fetched_at,payload_json,project_id) VALUES(?,?,?,?,?,?,?,?,?)",
                   (source["id"], hashlib.sha256(f"{source['id']}:{url}".encode()).hexdigest(), title[:500], description[:100000], url, published, timestamp, json.dumps({"title": raw_title, "description": raw_description}, ensure_ascii=False)[:200000], pid))
        db.execute("INSERT OR IGNORE INTO project_reviews(project_id,updated_at) VALUES(?,?)", (pid, timestamp))
        if ev == "New source signal":
            db.execute("UPDATE project_reviews SET level1_status='PENDING',level1_reason='New source evidence needs screening.',updated_at=? WHERE project_id=?", (timestamp, pid))
        db.execute("INSERT INTO project_events(project_id,event_type,summary,evidence_url,created_at) VALUES(?,?,?,?,?)", (pid, ev, f"{event} Source: {source_name}.", url, timestamp))
        db.execute("UPDATE projects SET opportunity_score=MIN(100, 20 + (SELECT COUNT(*)*10 FROM project_sources WHERE project_id=?)) WHERE id=?", (pid, pid))
        return True, pid


def parse_date(raw: str | None) -> str | None:
    if not raw: return None
    try: return email.utils.parsedate_to_datetime(raw).isoformat()
    except (TypeError, ValueError): return raw[:80]


def collect_rss() -> dict:
    with connect() as db:
        rows = db.execute("SELECT id,name,url FROM sources WHERE kind='RSS' AND status='ACTIVE' AND enabled=1 AND url IS NOT NULL").fetchall()
    configured = [x.strip() for x in os.environ.get("BPI_RSS_FEEDS", "").split(",") if x.strip()]
    feeds = [(r["id"], r["name"], r["url"]) for r in rows]
    for url in configured:
        name = "Custom RSS " + hashlib.sha1(url.encode()).hexdigest()[:8]
        with connect() as db:
            db.execute("INSERT OR IGNORE INTO sources(name,kind,url,status,detail,source_group,cadence_minutes,enabled) VALUES(?, 'RSS', ?, 'ACTIVE', 'Configured with BPI_RSS_FEEDS.', 'Technical sources', 120, 1)", (name, url))
            sid = db.execute("SELECT id FROM sources WHERE name=?", (name,)).fetchone()[0]
        feeds.append((sid, name, url))
    counts, errors = 0, []
    for sid, name, url in feeds:
        try:
            root = ET.fromstring(fetch(url))
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                date = parse_date(item.findtext("pubDate"))
                counts += int(upsert_signal(title, desc, link, name, date)[0])
            # Atom fallback
            for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                link = next((el.attrib.get("href") for el in entry.findall("{http://www.w3.org/2005/Atom}link") if el.attrib.get("rel", "alternate") == "alternate"), None)
                desc = entry.findtext("{http://www.w3.org/2005/Atom}summary", "") or entry.findtext("{http://www.w3.org/2005/Atom}content", "") or ""
                date = entry.findtext("{http://www.w3.org/2005/Atom}updated")
                if link: counts += int(upsert_signal(title, desc, link, name, date)[0])
            with connect() as db: db.execute("UPDATE sources SET status='ACTIVE',last_checked=?,detail='Feed fetched successfully.' WHERE id=?", (now(), sid))
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            with connect() as db: db.execute("UPDATE sources SET status='ERROR',last_checked=?,detail=? WHERE id=?", (now(), str(exc)[:500], sid))
    return {"source_count": len(feeds), "new_projects_or_signals": counts, "errors": errors}


def collect_rss_source(source_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT id,name,url FROM sources WHERE id=? AND kind='RSS' AND status IN ('ACTIVE','NEEDS VALIDATION','ERROR') AND url IS NOT NULL", (source_id,)).fetchone()
    if not row:
        return {"source_count": 0, "new_projects_or_signals": 0, "errors": ["Source is not an enabled active RSS feed."]}
    sid, name, url = row["id"], row["name"], row["url"]
    counts = 0
    try:
        root = ET.fromstring(fetch(url))
        for item in root.findall(".//item"):
            counts += int(upsert_signal(item.findtext("title", ""), item.findtext("description", ""), item.findtext("link", ""), name, parse_date(item.findtext("pubDate")))[0])
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
            link = next((el.attrib.get("href") for el in entry.findall("{http://www.w3.org/2005/Atom}link") if el.attrib.get("rel", "alternate") == "alternate"), None)
            desc = entry.findtext("{http://www.w3.org/2005/Atom}summary", "") or entry.findtext("{http://www.w3.org/2005/Atom}content", "") or ""
            if link: counts += int(upsert_signal(title, desc, link, name, entry.findtext("{http://www.w3.org/2005/Atom}updated"))[0])
        with connect() as db: db.execute("UPDATE sources SET status='ACTIVE',last_checked=?,detail='Feed fetched successfully.' WHERE id=?", (now(), sid))
        return {"source_count": 1, "new_projects_or_signals": counts, "errors": []}
    except Exception as exc:
        with connect() as db: db.execute("UPDATE sources SET status='ERROR',last_checked=?,detail=? WHERE id=?", (now(), str(exc)[:500], sid))
        return {"source_count": 1, "new_projects_or_signals": counts, "errors": [f"{name}: {exc}"]}


def collect_github() -> dict:
    with connect() as db: source = db.execute("SELECT id FROM sources WHERE name='GitHub Repository Search'").fetchone()
    counts, errors = 0, []
    for query in GITHUB_QUERIES:
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": query + " pushed:>2025-01-01", "sort": "updated", "order": "desc", "per_page": 20})
        try:
            data = json.loads(fetch(url))
            for repo in data.get("items", []):
                desc = repo.get("description") or ""
                payload = f"{desc} {repo.get('full_name','')} {repo.get('topics',[])}"
                counts += int(upsert_signal(repo.get("name", ""), payload, repo.get("html_url", ""), "GitHub Repository Search", repo.get("updated_at"), repo.get("homepage"))[0])
        except Exception as exc: errors.append(f"{query}: {exc}")
    with connect() as db:
        db.execute("UPDATE sources SET status=?,last_checked=?,detail=? WHERE id=?", ("ERROR" if errors else "ACTIVE", now(), ("; ".join(errors)[:500] if errors else "Public repository search completed; unauthenticated rate limits apply."), source["id"]))
    return {"queries": len(GITHUB_QUERIES), "new_projects_or_signals": counts, "errors": errors}


def collect_all() -> dict:
    return {"rss": collect_rss(), "github": collect_github(), "checked_at": now()}
