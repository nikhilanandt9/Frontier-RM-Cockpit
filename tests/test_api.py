import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from providers import deterministic_general_artifact, deterministic_journey_artifact, deterministic_recommendation  # noqa: E402
from agent_catalog import list_agents  # noqa: E402
from server import answer_question, list_agent_runs, load_agent_run, load_data, load_source, load_sources  # noqa: E402
from advisory import build_advisory_context  # noqa: E402


class ApiTests(unittest.TestCase):
    def test_dashboard_uses_twenty_customer_fabric_snapshot(self):
        dashboard = load_data()

        self.assertEqual(len(dashboard["clients"]), 20)
        self.assertEqual(len(dashboard["opportunities"]), 20)
        self.assertEqual(dashboard["dataSource"]["kind"], "fabric-snapshot")
        self.assertEqual(dashboard["dataSource"]["customerCount"], 20)
        self.assertIn("Adrian Koh", {client["name"] for client in dashboard["clients"]})
        self.assertTrue(all(client["signals"] for client in dashboard["clients"]))
        self.assertEqual(len(dashboard["houseviews"]), 2)
        self.assertTrue(dashboard["regulatoryRules"])
        self.assertTrue(all(client["advisoryProfile"] for client in dashboard["clients"]))

    def test_grounded_answer_has_citation(self):
        result = answer_question("What should I check before a fixed deposit matures?")

        self.assertFalse(result["escalationRequired"])
        self.assertEqual(result["citations"][0]["id"], "KNOW-FD-008")
        self.assertEqual(result["provider"], "deterministic-mock")

    def test_unknown_question_escalates(self):
        result = answer_question("What will the Straits Times Index close at tomorrow?")

        self.assertTrue(result["escalationRequired"])
        self.assertEqual(result["citations"], [])
        self.assertIn("cannot answer", result["answer"])

    def test_recommendation_has_visible_evidence_stages(self):
        data = __import__("server").load_data()
        result = deterministic_recommendation(data["clients"][0], data["opportunities"][0])

        self.assertEqual(result["clientId"], "client-lim")
        self.assertEqual(len(result["evidenceStages"]), 4)
        self.assertEqual(result["provider"], "deterministic-mock")
        self.assertTrue(result["checks"])
        self.assertTrue(result["meetingObjective"])
        self.assertEqual(len(result["talkTrack"]), 4)
        self.assertTrue(result["discoveryQuestions"])
        self.assertTrue(result["allocationThemes"])
        self.assertEqual(result["suitabilityChecks"], result["checks"])
        self.assertTrue(result["unresolvedItems"])
        self.assertTrue(result["followUpActions"])
        self.assertNotIn("fund name", json.dumps(result).casefold())

    def test_agent_run_contract_is_ordered_and_transparent(self):
        run = load_agent_run("run-daniel-lim-rehearsal")

        self.assertIsNotNone(run)
        self.assertEqual(run["run"]["mode"], "deterministic-rehearsal")
        self.assertEqual(len(run["agents"]), 4)
        self.assertEqual(
            [event["sequence"] for event in run["events"]],
            list(range(1, len(run["events"]) + 1)),
        )
        self.assertNotIn("chainOfThought", json.dumps(run))
        self.assertEqual(run["outcome"]["verificationStatus"], "verified")

    def test_agent_run_listing_and_invalid_id(self):
        runs = list_agent_runs()

        self.assertTrue(any(run["id"] == "run-daniel-lim-rehearsal" for run in runs))
        self.assertEqual(runs[0]["id"], "run-daniel-lim-live-20260812173016-success")
        self.assertEqual(runs[0]["mode"], "captured-live")
        self.assertEqual(runs[0]["verificationStatus"], "verified")
        self.assertEqual(runs[0]["displayLabel"], "Captured live · Verified")
        self.assertIsNone(load_agent_run("../data"))

    def test_agent_catalog_is_safe_and_complete(self):
        agents = list_agents()
        serialized = json.dumps(agents).casefold()

        self.assertEqual(len(agents), 4)
        self.assertEqual({agent["id"] for agent in agents}, {
            "orchestrator",
            "customer-intelligence",
            "market-context",
            "meeting-preparation",
        })
        for agent in agents:
            self.assertTrue(agent["objective"])
            self.assertTrue(agent["runtimeTaskPrompt"])
            self.assertTrue(agent["systemInstructions"])
            self.assertTrue(agent["sharedConstraints"])
            self.assertTrue(agent["inputContext"])
            self.assertTrue(agent["structuredOutput"])
            self.assertTrue(agent["workflowHandoff"])
        self.assertNotIn("access_token", serialized)
        self.assertNotIn("chainofthought", serialized)

    def test_source_catalog_is_client_scoped_and_allowlisted(self):
        data = load_data()
        sources = load_sources()
        client_ids = {client["id"] for client in data["clients"]}

        self.assertEqual(len(sources), 6)
        self.assertEqual(len({source["id"] for source in sources}), len(sources))
        self.assertTrue(all(source["clientId"] in client_ids for source in sources))
        self.assertEqual({source["type"] for source in sources}, {"email", "document"})
        self.assertEqual(len(load_sources("client-lim")), 2)
        self.assertEqual(len(load_sources(source_type="email")), 3)
        self.assertEqual(load_source("email-daniel-maturity-01")["clientId"], "client-lim")
        self.assertIsNone(load_source("../sources"))
        self.assertIsNone(load_source("unknown-source"))

    def test_source_catalog_is_explicitly_fictional(self):
        serialized = json.dumps(load_sources()).casefold()

        self.assertIn("fictional authored", serialized)
        self.assertIn("@client.example", serialized)
        self.assertNotIn("@outlook.com", serialized)
        self.assertNotIn("@gmail.com", serialized)

    def test_three_stage_artifacts_share_safe_rationale_contract(self):
        data = load_data()
        client = next(item for item in data["clients"] if item["id"] == "client-lim")
        opportunity = next(item for item in data["opportunities"] if item["clientId"] == client["id"])
        sources = load_sources(client["id"])

        artifacts = {
            action: deterministic_journey_artifact(client, opportunity, action, sources)
            for action in ("briefing", "recommendation", "opportunity-draft")
        }
        for action, artifact in artifacts.items():
            with self.subTest(action=action):
                self.assertEqual(artifact["action"], action)
                self.assertEqual(artifact["clientId"], client["id"])
                self.assertEqual(len(artifact["sources"]), 2)
                self.assertTrue(artifact["checks"])
                self.assertTrue(artifact["unresolvedItems"])
                self.assertTrue(artifact["reasoning"]["evidenceUsed"])
                self.assertTrue(artifact["reasoning"]["decisionRules"])
                self.assertTrue(artifact["reasoning"]["whyThisFits"])
                self.assertTrue(artifact["reasoning"]["alternativesConsidered"])
                self.assertTrue(artifact["reasoning"]["assumptions"])
                self.assertTrue(artifact["reasoning"]["limitations"])
                self.assertNotIn("chainofthought", json.dumps(artifact).casefold())

        products = artifacts["recommendation"]["artifact"]["products"]
        self.assertTrue(all(product["fictional"] for product in products))
        self.assertTrue(all(product["risks"] for product in products))
        self.assertIn("Not an executable recommendation", artifacts["recommendation"]["artifact"]["disclaimer"])
        draft = artifacts["opportunity-draft"]["artifact"]
        self.assertEqual(draft["crm"]["approvalState"], "Not approved")
        self.assertIn("Draft only", draft["email"]["disclosures"][0])

    def test_daniel_activity_changes_observed_not_declared_profile(self):
        context = build_advisory_context(load_data(), "client-lim")
        risk = context["riskContext"]
        activity = context["activityEvidence"][0]

        self.assertEqual(risk["declaredScore"], 3)
        self.assertEqual(risk["previousObservedIndicator"], 3)
        self.assertEqual(risk["observedIndicator"], 2)
        self.assertFalse(risk["declaredProfileChangedByActivity"])
        self.assertEqual(risk["reviewStatus"], "REVIEW_SUGGESTED")
        self.assertEqual(activity["activity_type"], "SELL")
        self.assertEqual(activity["asset_class"], "EQUITY")
        self.assertEqual(activity["amount"], 320_000)
        self.assertTrue(context["retainedCandidates"])
        self.assertTrue(context["suppressedCandidates"])

    def test_retired_client_uses_enhanced_review_not_mas_default(self):
        context = build_advisory_context(load_data(), "client-tan")
        serialized = json.dumps(context)

        self.assertEqual(context["riskContext"]["retirementStatus"], "RETIRED")
        self.assertEqual(context["riskContext"]["declaredScore"], 2)
        self.assertEqual(context["retainedCandidates"], [])
        derivative = next(item for item in context["suppressedCandidates"] if item["complex"])
        self.assertTrue(any("Knowledge or experience" in reason for reason in derivative["reasons"]))
        self.assertTrue(any(item["ruleId"] == "INTERNAL-RETIREMENT-ENHANCED-REVIEW" for item in context["regulatoryControls"]))
        self.assertNotIn("MAS requires retirees", serialized)
        self.assertNotIn("MAS bans derivatives", serialized)
        self.assertNotIn("recommendation is compliant", serialized.casefold())

    def test_houseview_and_regulatory_ids_are_allowlisted(self):
        data = load_data()
        active = next(item for item in data["houseviews"] if item["status"] == "ACTIVE")
        context = build_advisory_context(data, "client-lim", active["houseview_id"])

        self.assertEqual(context["houseviewContext"]["reportId"], "houseview-2026-q4")
        self.assertTrue(all(section["houseview_section_id"].startswith("hv-q4-") for section in context["houseviewContext"]["sections"]))
        self.assertTrue(all(item["ruleId"].startswith(("FAA-N16-", "INTERNAL-")) for item in context["regulatoryControls"]))
        with self.assertRaises(ValueError):
            build_advisory_context(data, "client-lim", "../houseview")

    def test_recommendation_contains_houseview_activity_and_controls(self):
        data = load_data()
        client = next(item for item in data["clients"] if item["id"] == "client-lim")
        opportunity = next(item for item in data["opportunities"] if item["clientId"] == client["id"])
        context = build_advisory_context(data, client["id"])
        result = deterministic_journey_artifact(client, opportunity, "recommendation", load_sources(client["id"]), context)
        evidence_ids = {item["id"] for item in result["reasoning"]["evidenceUsed"]}

        self.assertEqual(result["houseviewContext"]["reportId"], "houseview-2026-q4")
        self.assertIn("investment-activity-01", evidence_ids)
        self.assertIn("hv-q4-income", evidence_ids)
        self.assertTrue(result["regulatoryControls"])
        self.assertTrue(result["suppressedCandidates"])
        self.assertTrue(result["artifact"]["products"])
        self.assertIn("Compliance-aware", result["artifact"]["disclaimer"])

    def test_general_mode_excludes_fabric_iq_grounding(self):
        data = load_data()
        client = next(item for item in data["clients"] if item["id"] == "client-lim")
        opportunity = next(item for item in data["opportunities"] if item["clientId"] == client["id"])
        iq = deterministic_journey_artifact(
            client,
            opportunity,
            "recommendation",
            load_sources(client["id"]),
            build_advisory_context(data, client["id"]),
        )
        general = deterministic_general_artifact(client, opportunity, "recommendation")

        self.assertTrue(iq["sources"])
        self.assertTrue(iq["houseviewContext"])
        self.assertTrue(iq["activityEvidence"])
        self.assertTrue(iq["regulatoryControls"])
        self.assertTrue(iq["suppressedCandidates"])
        self.assertEqual(general["groundingMode"], "general")
        self.assertEqual(general["groundingLabel"], "General AI draft")
        self.assertEqual(general["sources"], [])
        for field in ("houseviewContext", "activityEvidence", "regulatoryControls", "suppressedCandidates", "riskContext"):
            self.assertNotIn(field, general)
        self.assertEqual(len(general["artifact"]["products"]), 1)
        self.assertTrue(general["checks"])
        self.assertIn("Not an executable recommendation", general["artifact"]["disclaimer"])

    def test_general_mode_all_three_artifacts_remain_safe(self):
        data = load_data()
        client = next(item for item in data["clients"] if item["id"] == "client-lim")
        opportunity = next(item for item in data["opportunities"] if item["clientId"] == client["id"])

        for action in ("briefing", "recommendation", "opportunity-draft"):
            with self.subTest(action=action):
                artifact = deterministic_general_artifact(client, opportunity, action)
                serialized = json.dumps(artifact).casefold()
                self.assertEqual(artifact["groundingMode"], "general")
                self.assertTrue(artifact["checks"])
                self.assertIn("human review", serialized)
                self.assertNotIn("houseview-2026", serialized)
                self.assertNotIn("faa-n16", serialized)
                self.assertNotIn("investment-activity", serialized)
        draft = deterministic_general_artifact(client, opportunity, "opportunity-draft")
        self.assertEqual(draft["artifact"]["crm"]["evidenceIds"], [])
        self.assertEqual(draft["artifact"]["crm"]["approvalState"], "Not approved")


if __name__ == "__main__":
    unittest.main()