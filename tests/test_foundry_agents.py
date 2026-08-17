from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from deploy_frontier_foundry_agents import (  # noqa: E402
    AGENTS,
    CUSTOMER_INTELLIGENCE_NAME,
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    fabric_tool,
    preview,
)
from unittest.mock import MagicMock, patch


class FoundryAgentTests(unittest.TestCase):
    def test_agent_topology_is_complete_and_unique(self) -> None:
        names = [agent.name for agent in AGENTS]
        self.assertEqual(
            names,
            [
                "frontier-rm-orchestrator",
                "frontier-customer-intelligence",
                "frontier-market-context",
                "frontier-meeting-preparation",
            ],
        )
        self.assertEqual(len(names), len(set(names)))

    def test_only_customer_intelligence_requires_fabric(self) -> None:
        fabric_agents = [agent.name for agent in AGENTS if agent.requires_fabric]
        self.assertEqual(fabric_agents, ["frontier-customer-intelligence"])

    def test_grounding_contract_blocks_known_failure_modes(self) -> None:
        instructions = {agent.name: agent.instructions for agent in AGENTS}
        self.assertIn("Always use the Fabric tool", instructions[CUSTOMER_INTELLIGENCE_NAME])
        self.assertIn("do not answer from model knowledge", instructions[CUSTOMER_INTELLIGENCE_NAME])
        self.assertIn("Do not create evidence IDs", instructions["frontier-market-context"])
        self.assertIn("Never invent customer history", instructions["frontier-rm-orchestrator"])
        self.assertIn("do not draft a brief", instructions["frontier-meeting-preparation"])

    def test_preview_reports_fabric_tool_as_unattached(self) -> None:
        proposal = preview(DEFAULT_ENDPOINT, DEFAULT_MODEL)
        self.assertEqual(proposal["projectEndpoint"], DEFAULT_ENDPOINT)
        self.assertEqual(proposal["model"], DEFAULT_MODEL)
        self.assertFalse(proposal["fabricToolAttached"])
        self.assertIsNone(proposal["fabricConnectionId"])
        self.assertEqual(len(proposal["agents"]), 4)

    def test_preview_reports_resolved_fabric_connection(self) -> None:
        connection_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/a/projects/p/connections/frontier-rm-fabric"
        proposal = preview(DEFAULT_ENDPOINT, DEFAULT_MODEL, connection_id)
        self.assertTrue(proposal["fabricToolAttached"])
        self.assertEqual(proposal["fabricConnectionId"], connection_id)

    def test_fabric_tool_serializes_expected_connection(self) -> None:
        connection_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/a/projects/p/connections/frontier-rm-fabric"
        payload = fabric_tool(connection_id).as_dict()
        self.assertEqual(payload["type"], "fabric_dataagent_preview")
        self.assertEqual(
            payload["fabric_dataagent_preview"]["project_connections"][0]["project_connection_id"],
            connection_id,
        )

    @patch("deploy_frontier_foundry_agents.AzureCliCredential")
    @patch("deploy_frontier_foundry_agents.AIProjectClient")
    def test_deploy_creates_only_customer_intelligence_version(self, project_type, credential_type) -> None:
        from deploy_frontier_foundry_agents import deploy

        credential_type.return_value.__enter__.return_value = MagicMock()
        project = project_type.return_value.__enter__.return_value
        project.connections.get.return_value.id = "connection-id"
        project.agents.create_version.return_value.id = f"{CUSTOMER_INTELLIGENCE_NAME}:3"
        project.agents.create_version.return_value.name = CUSTOMER_INTELLIGENCE_NAME
        project.agents.create_version.return_value.version = "3"

        deployed, connection_id = deploy(DEFAULT_ENDPOINT, DEFAULT_MODEL, "frontier-rm-fabric")

        self.assertEqual(connection_id, "connection-id")
        self.assertEqual([item["name"] for item in deployed], [CUSTOMER_INTELLIGENCE_NAME])
        self.assertEqual(project.agents.create_version.call_count, 1)

    def test_environment_records_live_fabric_agent_and_graph_blocker(self) -> None:
        environment = json.loads((ROOT / "infra" / "environment.json").read_text(encoding="utf-8"))
        foundry = environment["deployment"]["foundry"]
        self.assertEqual(foundry["agentsStatus"], "customer-intelligence-v3-live-semantic-model-only")
        self.assertEqual(
            set(foundry["agents"].values()),
            {
                "frontier-rm-orchestrator:2",
                "frontier-customer-intelligence:3",
                "frontier-market-context:2",
                "frontier-meeting-preparation:2",
            },
        )
        self.assertEqual(foundry["fabricConnectionStatus"], "verified")
        self.assertEqual(foundry["fabricAggregateValidationStatus"], "completed-20-customers")
        self.assertEqual(foundry["fabricDetailValidationStatus"], "semantic-model-and-direct-dax-validated")
        self.assertEqual(foundry["ontologyRoutingStatus"], "disabled-pending-graph-repair")
        self.assertEqual(foundry["capturedLiveRunId"], "run-daniel-lim-live-20260812173016-success")
        self.assertEqual(
            environment["deployment"]["fabric"]["ontologyGraphValidationStatus"],
            "blocked-graph-model-not-ready",
        )


if __name__ == "__main__":
    unittest.main()