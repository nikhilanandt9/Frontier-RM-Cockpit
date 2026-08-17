import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendStorytellingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.javascript = (ROOT / "apps" / "web" / "app-v2.js").read_text(encoding="utf-8")
        cls.styles = (ROOT / "apps" / "web" / "styles.css").read_text(encoding="utf-8")
        cls.html = (ROOT / "apps" / "web" / "index.html").read_text(encoding="utf-8")

    def test_today_exposes_three_stage_journey_and_metric_reports(self):
        for label in (
            "Prepare the client briefing",
            "Shape custom recommendations",
            "Create the opportunity draft",
        ):
            self.assertIn(label, self.javascript)
        self.assertIn('data-metric-report="${id}"', self.javascript)
        self.assertIn('role="dialog"', self.javascript)
        self.assertIn("openMetricReport", self.javascript)
        self.assertIn(".report-table", self.styles)

    def test_shell_uses_sources_and_persistent_copilot(self):
        self.assertIn("['sources', 'Sources']", self.javascript)
        self.assertNotIn("['knowledge', 'Knowledge']", self.javascript)
        self.assertIn('id="copilot-toggle"', self.html)
        self.assertIn('id="copilot-panel"', self.html)
        self.assertIn("renderCopilot", self.javascript)
        self.assertIn(".copilot-panel", self.styles)
        self.assertIn("@media (max-width: 760px)", self.styles)

    def test_clients_present_client_360_only(self):
        self.assertIn("CLIENT 360", self.javascript)
        self.assertNotIn("HOUSEHOLD 360", self.javascript)
        self.assertNotIn("Search households", self.javascript)
        self.assertNotIn("Household context, engagement history", self.javascript)

    def test_opportunity_workspace_has_three_safe_artifacts(self):
        for action in ("briefing", "recommendation", "opportunity-draft"):
            self.assertIn(action, self.javascript)
        self.assertIn("Fictional product candidates", self.javascript)
        self.assertIn("Client email draft", self.javascript)
        self.assertIn("Opportunity record", self.javascript)
        self.assertIn("Not sent · Not committed to CRM", self.javascript)
        self.assertNotIn(">Send<", self.javascript)
        self.assertNotIn("Create in CRM", self.javascript)

    def test_sources_and_public_rationale_are_clickable(self):
        self.assertIn("renderSources", self.javascript)
        self.assertIn("data-source-citation", self.javascript)
        self.assertIn("Why this? View evidence and rationale", self.javascript)
        self.assertIn("Private model reasoning is not exposed", self.javascript)
        self.assertIn(".source-explorer", self.styles)
        self.assertIn(".rationale-modal", self.styles)

    def test_operations_distinguishes_replay_from_demo_telemetry(self):
        self.assertIn("Agent events below replay the selected operator capture", self.javascript)
        self.assertIn("Synthetic signal telemetry", self.javascript)
        self.assertIn("data-run-select", self.javascript)
        self.assertIn("data-agent-detail", self.javascript)
        self.assertIn("Runtime Task Prompt", self.javascript)
        self.assertIn("Structured Output", self.javascript)
        self.assertIn("Workflow Handoff", self.javascript)

    def test_houseview_is_secondary_story_after_operations(self):
        operations = self.javascript.index("['operations', 'Operations']")
        houseview = self.javascript.index("['houseview', 'Houseview']")

        self.assertGreater(houseview, operations)
        self.assertIn("renderHouseview", self.javascript)
        self.assertIn("Tailor positioning in Opportunity studio", self.javascript)
        self.assertIn(".houseview-layout", self.styles)
        self.assertIn(".houseview-reader", self.styles)

    def test_client_risk_profile_is_separate_from_observed_activity(self):
        self.assertIn("Investment Risk Profile", self.javascript)
        self.assertIn("Observed behaviour", self.javascript)
        self.assertIn("does not silently change", self.javascript)
        self.assertIn("Latest activity evidence", self.javascript)
        self.assertNotIn("Credit Score", self.javascript)

    def test_recommendation_exposes_houseview_and_regulatory_gates(self):
        self.assertIn("GROUNDED POSITIONING", self.javascript)
        self.assertIn("candidates suppressed", self.javascript)
        self.assertIn("data-control-detail", self.javascript)
        self.assertIn("data-houseview-citation", self.javascript)
        self.assertIn("This is an internal safeguard", self.javascript)
        self.assertNotIn("MAS requires retirees", self.javascript)
        self.assertNotIn("MAS bans derivatives", self.javascript)
        self.assertNotIn("certified compliant", self.javascript.casefold())

    def test_opportunities_supports_fabric_iq_comparison_mode(self):
        self.assertIn("groundingMode: 'fabric-iq'", self.javascript)
        self.assertIn('data-grounding-mode="fabric-iq"', self.javascript)
        self.assertIn('data-grounding-mode="general"', self.javascript)
        self.assertIn("With Fabric IQ", self.javascript)
        self.assertIn("Without Fabric IQ", self.javascript)
        self.assertIn("gpt-4.1-mini · managed identity", self.javascript)
        self.assertIn("Fabric IQ grounded", self.javascript)
        self.assertIn("General AI draft", self.javascript)
        self.assertIn("No enterprise citations in general mode", self.javascript)
        self.assertIn(".iq-toggle", self.styles)

    def test_artifact_chains_are_isolated_by_grounding_mode(self):
        self.assertIn("state.generated[clientId]?.[groundingMode]?.[action]", self.javascript)
        self.assertIn("state.generated[clientId][groundingMode] ||= {}", self.javascript)
        self.assertIn("state.generated[clientId][groundingMode][action] = result", self.javascript)
        self.assertIn("Complete the previous artifact in this comparison mode first", self.javascript)
        self.assertIn("groundingMode: groundingMode", self.javascript)

    def test_general_mode_has_reduced_evidence_trace(self):
        self.assertIn("GENERAL AI PREPARATION", self.javascript)
        self.assertIn("Basic client facts", self.javascript)
        self.assertIn("Generic need framing", self.javascript)
        self.assertIn("FABRIC IQ EVIDENCE TRACE", self.javascript)
        self.assertIn("Enterprise sources and Houseview", self.javascript)


if __name__ == "__main__":
    unittest.main()