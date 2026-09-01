import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectPolicyTests(unittest.TestCase):
    def test_public_environment_example_contains_only_placeholders(self):
        config_path = ROOT / "infra" / "environment.example.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        serialized = json.dumps(config)

        self.assertEqual(config["project"], "frontier-rm-cockpit")
        for placeholder in (
            "<AZURE_SUBSCRIPTION_ID>",
            "<AZURE_TENANT_ID>",
            "<FABRIC_WORKSPACE_ID>",
            "<FABRIC_LAKEHOUSE_ID>",
            "<RM_SEMANTIC_MODEL_ID>",
            "<INSURANCE_DATA_AGENT_ID>",
        ):
            self.assertIn(placeholder, serialized)
        self.assertNotRegex(serialized, r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
        self.assertNotIn("azurecontainerapps.io", serialized)
        self.assertNotIn("datawarehouse.fabric.microsoft.com", serialized)

    def test_real_environment_inventory_is_local_only(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("infra/environment.local.json", ignore)
        self.assertFalse((ROOT / "infra" / "environment.json").exists())

    def test_clean_room_provenance_exists(self):
        provenance = (ROOT / "docs" / "provenance.md").read_text(encoding="utf-8")

        self.assertIn("independently authored", provenance)
        self.assertIn("No third-party source code", provenance)


if __name__ == "__main__":
    unittest.main()