import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import database
from app.main import app
from app.discovery import upsert_signal


class IntelligenceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_data, self.old_db = database.DATA_DIR, database.DB_PATH
        database.DATA_DIR = Path(self.temp.name)
        database.DB_PATH = database.DATA_DIR / "api-test.sqlite3"
        database.init_db()
        _, self.project_id = upsert_signal("Nova testnet", "Nova testnet is live", "https://example.org/nova", "Ethereum Blog RSS")
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        database.DATA_DIR, database.DB_PATH = self.old_data, self.old_db
        self.temp.cleanup()

    def test_registry_screen_translation_and_dossier(self):
        sources = self.client.get("/api/sources").json()
        self.assertTrue(any(source["name"] == "Telegram" and source["status"] == "API REQUIRED" for source in sources))
        self.assertEqual(self.client.post("/api/review/screen").status_code, 200)
        self.assertEqual(self.client.post(f"/api/projects/{self.project_id}/translation", json={"translated_description":"Тестовая сеть Nova"}).json()["saved"], True)
        dossier = self.client.get(f"/api/projects/{self.project_id}").json()
        self.assertEqual(dossier["review"]["translated_description"], "Тестовая сеть Nova")
        self.assertEqual(dossier["signals"][0]["url"], "https://example.org/nova")
        self.assertEqual(self.client.get("/api/my-top-projects").json(), [])

    def test_unimplemented_source_cannot_be_enabled(self):
        sources = self.client.get("/api/sources").json()
        telegram = next(source for source in sources if source["name"] == "Telegram")
        response = self.client.patch(f"/api/sources/{telegram['id']}", json={"enabled":True})
        self.assertEqual(response.status_code, 422)

    def test_deep_review_cannot_be_completed_without_evidence(self):
        response = self.client.patch(f"/api/projects/{self.project_id}/review", json={"level2_status":"COMPLETE"})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
