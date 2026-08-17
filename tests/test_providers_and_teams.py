import json
import os
import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "apps" / "teams" / "src"))

from cards import build_knowledge_card  # noqa: E402
from bot_auth import is_trusted_service_url  # noqa: E402
from bot_server import build_reply, callback_url, clean_message_text  # noqa: E402
from providers import AzureOpenAIKnowledgeProvider, DeterministicKnowledgeProvider, provider_from_environment  # noqa: E402


class ProviderAndTeamsTests(unittest.TestCase):
    @staticmethod
    def png_dimensions(path: Path) -> tuple[int, int]:
        with path.open("rb") as image:
            signature = image.read(24)
        if signature[:8] != b"\x89PNG\r\n\x1a\n":
            raise AssertionError(f"Not a PNG file: {path}")
        return struct.unpack(">II", signature[16:24])

    def test_mock_is_default_provider(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsInstance(provider_from_environment(), DeterministicKnowledgeProvider)

    def test_azure_mode_without_configuration_falls_back(self):
        with patch.dict(os.environ, {"FRONTIER_AI_MODE": "azure"}, clear=True):
            self.assertIsInstance(provider_from_environment(), DeterministicKnowledgeProvider)

    def test_azure_mode_requires_endpoint_and_deployment(self):
        environment = {
            "FRONTIER_AI_MODE": "azure",
            "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "frontier-model",
        }
        with patch.dict(os.environ, environment, clear=True):
            self.assertIsInstance(provider_from_environment(), AzureOpenAIKnowledgeProvider)

    def test_teams_card_preserves_backend_citation(self):
        result = {
            "answer": "Complete the client profile first.",
            "citations": [{"id": "KNOW-KYC-014", "source": "Fictional standard"}],
            "escalationRequired": False,
        }
        serialised = json.dumps(build_knowledge_card("Can I proceed?", result))

        self.assertIn("KNOW-KYC-014", serialised)
        self.assertIn("Complete the client profile first", serialised)

    def test_manifest_is_personal_scope_and_unresolved(self):
        manifest = json.loads((ROOT / "apps" / "teams" / "appPackage" / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["accentColor"], "#B00020")
        self.assertEqual(manifest["manifestVersion"], "1.26")
        self.assertEqual(manifest["bots"][0]["scopes"], ["personal"])
        self.assertEqual(manifest["id"], "${{TEAMS_APP_ID}}")

    def test_teams_icons_have_required_dimensions(self):
        package = ROOT / "apps" / "teams" / "appPackage"

        self.assertEqual(self.png_dimensions(package / "color.png"), (192, 192))
        self.assertEqual(self.png_dimensions(package / "outline.png"), (32, 32))

    def test_bot_reply_uses_shared_adaptive_card_contract(self):
        with patch("bot_server.query_knowledge") as query:
            query.return_value = {
                "answer": "Complete the profile first.",
                "citations": [{"id": "KNOW-KYC-014", "source": "Fictional standard"}],
                "escalationRequired": False,
                "provider": "deterministic-mock",
            }
            reply = build_reply({"type": "message", "text": "<at>Frontier RM</at> Can I proceed before KYC?"})

        self.assertEqual(clean_message_text("<at>Frontier RM</at>  hello"), "hello")
        self.assertEqual(reply["attachments"][0]["contentType"], "application/vnd.microsoft.card.adaptive")
        self.assertIn("KNOW-KYC-014", json.dumps(reply))

    def test_playground_callback_is_loopback_only(self):
        activity = {
            "serviceUrl": "http://127.0.0.1:56150",
            "conversation": {"id": "conversation 1"},
            "id": "activity/1",
        }
        self.assertEqual(
            callback_url(activity),
            "http://127.0.0.1:56150/v3/conversations/conversation%201/activities/activity%2F1",
        )
        with self.assertRaises(ValueError):
            callback_url({**activity, "serviceUrl": "https://example.com"})

    def test_cloud_service_url_allowlist(self):
        self.assertTrue(is_trusted_service_url("https://smba.trafficmanager.net/amer/", playground=False))
        self.assertTrue(is_trusted_service_url("https://example.botframework.com", playground=False))
        self.assertFalse(is_trusted_service_url("https://example.com", playground=False))
        self.assertFalse(is_trusted_service_url("http://smba.trafficmanager.net/amer/", playground=False))


if __name__ == "__main__":
    unittest.main()