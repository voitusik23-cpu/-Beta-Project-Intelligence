import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app import database
from app.discovery import infer_stage, upsert_signal
from app.screening import classify_project, screen_projects


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_data, self.old_db = database.DATA_DIR, database.DB_PATH
        database.DATA_DIR = Path(self.temp.name)
        database.DB_PATH = database.DATA_DIR / "test.sqlite3"
        database.init_db()

    def tearDown(self):
        database.DATA_DIR, database.DB_PATH = self.old_data, self.old_db
        self.temp.cleanup()

    def test_signal_creates_project_evidence_and_event(self):
        created, pid = upsert_signal("Introducing Nova Protocol", "Nova protocol testnet opens today", "https://example.org/nova", "Ethereum Blog RSS")
        self.assertTrue(created)
        with database.connect() as db:
            project = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
            self.assertEqual(project["stage"], "Testnet")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM project_sources WHERE project_id=?", (pid,)).fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM project_events WHERE project_id=?", (pid,)).fetchone()[0], 1)

    def test_duplicate_link_is_ignored(self):
        self.assertTrue(upsert_signal("Nova Protocol", "New protocol beta", "https://example.org/post", "Ethereum Blog RSS")[0])
        self.assertFalse(upsert_signal("Nova Protocol", "New protocol beta", "https://example.org/post", "Ethereum Blog RSS")[0])
        with database.connect() as db: self.assertEqual(db.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 1)

    def test_waitlist_stage_is_a_signal_to_verify(self):
        stage, note = infer_stage("Join the waitlist")
        self.assertEqual(stage, "Waitlist")
        self.assertIn("verify", note)

    def test_source_catalog_and_resumable_review_schema_exist(self):
        with database.connect() as db:
            names = {row[0] for row in db.execute("SELECT name FROM sources")}
            self.assertIn("Incrypted Airdrops (Telegram)", names)
            self.assertIn("DeFiLlama Raises", names)
            self.assertIn("Paradigm", names)
            statuses = {row[0] for row in db.execute("SELECT status FROM sources")}
            self.assertIn("API REQUIRED", statuses)
            self.assertIn("NEEDS VALIDATION", statuses)
            self.assertIsNotNone(db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_items'").fetchone())
            self.assertIsNotNone(db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_runs'").fetchone())

    def test_same_project_url_can_be_kept_from_multiple_sources(self):
        created, project_id = upsert_signal("Nova Protocol", "Nova protocol testnet opens today", "https://example.org/post", "Ethereum Blog RSS")
        self.assertTrue(created)
        with database.connect() as db:
            db.execute("INSERT INTO sources(name,kind,status) VALUES('Second test source','RSS','ACTIVE')")
        created_again, same_id = upsert_signal("Nova Protocol", "Nova protocol testnet opens today", "https://example.org/post", "Second test source")
        self.assertTrue(created_again)
        self.assertEqual(project_id, same_id)
        with database.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM project_sources WHERE project_id=?", (project_id,)).fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM raw_items WHERE project_id=?", (project_id,)).fetchone()[0], 2)

    def test_screening_keeps_evidence_and_rejects_airdrop_automation(self):
        signal, project_id = upsert_signal("Join Nova testnet", "Nova testnet is live; public participation is open", "https://example.org/nova", "Ethereum Blog RSS")
        self.assertTrue(signal)
        result = screen_projects(batch_size=1)
        self.assertEqual(result["total"], 1)
        with database.connect() as db:
            row = db.execute("SELECT level1_status FROM project_reviews WHERE project_id=?", (project_id,)).fetchone()
            self.assertEqual(row[0], "REVIEW")
        status, reason = classify_project({"name":"Airdrop bot","description":"Auto-claim bot multi-wallet airdrop bot", "website":None}, ["GitHub Repository Search"], 1)
        self.assertEqual(status, "REJECTED")
        self.assertIn("автоматизац", reason.lower())

    def test_screening_archives_stale_feed_noise_and_developer_tools(self):
        stale = (datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 3)).isoformat()
        status, reason = classify_project({"name":"Old Ethereum News", "description":"A general update", "website":None, "latest_published_at":stale}, ["Ethereum Blog RSS"], 1)
        self.assertEqual(status, "REJECTED")
        self.assertIn("Архивная", reason)
        status, _ = classify_project({"name":"Mina Explorer", "description":"Blockchain explorer", "website":"https://example.org"}, ["GitHub Repository Search"], 1)
        self.assertEqual(status, "REJECTED")
        status, _ = classify_project({"name":"Small Prototype", "description":"Prototype", "website":"https://small-app.vercel.app"}, ["GitHub Repository Search"], 1)
        self.assertEqual(status, "REVIEW")
        status, _ = classify_project({"name":"Project docs", "description":"Technical spec", "website":"https://github.com/person/project/blob/main/README.md"}, ["GitHub Repository Search"], 1)
        self.assertEqual(status, "REVIEW")


if __name__ == "__main__": unittest.main()
