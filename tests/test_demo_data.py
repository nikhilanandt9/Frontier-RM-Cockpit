import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "packages" / "demo-data" / "data.json").read_text(encoding="utf-8"))


class DemoDataTests(unittest.TestCase):
    def test_rm_persona_is_john_doe(self):
        self.assertEqual(DATA["rm"]["name"], "John Doe")
        self.assertEqual(DATA["rm"]["initials"], "JD")

    def test_relationships_and_ids_are_consistent(self):
        client_ids = {client["id"] for client in DATA["clients"]}
        opportunity_ids = {opportunity["id"] for opportunity in DATA["opportunities"]}

        self.assertEqual(len(client_ids), len(DATA["clients"]))
        self.assertEqual(len(opportunity_ids), len(DATA["opportunities"]))
        self.assertTrue(all(opportunity["clientId"] in client_ids for opportunity in DATA["opportunities"]))
        self.assertTrue(all(item["clientId"] in client_ids for item in DATA["agenda"] if item["clientId"]))

    def test_singapore_locale_and_fictional_knowledge(self):
        serialised = json.dumps(DATA, ensure_ascii=False)

        self.assertIn("S$", serialised)
        self.assertIn("Singapore", serialised)
        self.assertNotIn("€", serialised)
        self.assertTrue(all(entry["id"].startswith("KNOW-") for entry in DATA["knowledge"]))
        self.assertTrue(all("Fictional" in entry["source"] for entry in DATA["knowledge"]))


if __name__ == "__main__":
    unittest.main()
