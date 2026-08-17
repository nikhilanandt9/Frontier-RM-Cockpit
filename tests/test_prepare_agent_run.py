from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prepare_agent_run import response_evidence, sanitize_text, validate_bundle  # noqa: E402


class PrepareAgentRunTests(unittest.TestCase):
    def test_sanitizer_rejects_credentials_and_private_reasoning(self) -> None:
        for value in ("Authorization: secret", "Bearer abc.def", "access_token=abc", "hidden reasoning"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                sanitize_text(value)

    def test_sanitizer_normalizes_and_bounds_text(self) -> None:
        self.assertEqual(sanitize_text("  governed\n  facts  "), "governed facts")
        self.assertEqual(sanitize_text("abcdef", max_length=3), "abc")

    def test_response_evidence_rejects_empty_identifier(self) -> None:
        with self.assertRaises(ValueError):
            response_evidence("customer-intelligence", "...")

    def test_response_evidence_accepts_semantic_request_identifier(self) -> None:
        self.assertEqual(
            response_evidence("semantic-model", "request-123"),
            "foundry:semantic-model:request-123",
        )

    def test_bundle_validation_requires_contiguous_events_and_evidence_count(self) -> None:
        bundle = {
            "schemaVersion": "1.0",
            "run": {"mode": "captured-live"},
            "agents": [{}, {}, {}, {}],
            "events": [
                {"sequence": 1, "evidenceIds": ["fabric:1"]},
                {"sequence": 2, "evidenceIds": ["foundry:1"]},
            ],
            "outcome": {"evidenceCount": 2, "verificationStatus": "verified"},
        }
        validate_bundle(bundle, "verified")
        bundle["events"][1]["sequence"] = 3
        with self.assertRaises(ValueError):
            validate_bundle(bundle, "verified")


if __name__ == "__main__":
    unittest.main()