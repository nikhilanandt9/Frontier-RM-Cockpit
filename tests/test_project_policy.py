import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectPolicyTests(unittest.TestCase):
    def test_azure_provisioning_is_locked(self):
        config = json.loads((ROOT / "infra" / "environment.json").read_text(encoding="utf-8"))

        self.assertEqual(config["resourceGroup"], "<AZURE_RESOURCE_GROUP>")
        self.assertTrue(config["subscriptionConfirmationRequired"])
        self.assertTrue(config["azureWritesEnabled"])
        self.assertEqual(config["confirmedSubscription"]["id"], "<AZURE_SUBSCRIPTION_ID>")
        self.assertEqual(config["plannedLocation"], "eastus")
        self.assertEqual(config["fabricLocation"], "australiaeast")
        self.assertTrue(config["crossRegionDataPlane"])
        self.assertEqual(config["resourceGroupStatus"], "verified-existing-deployed")
        self.assertTrue(config["resourceGroupDeploymentValidated"])
        self.assertEqual(config["deployment"]["azureOpenAIDeployment"], "frontier-gpt-4-1-mini")
        self.assertEqual(config["deployment"]["apiImage"], "frontier-rm-api:0.8.3")
        self.assertEqual(
            config["deployment"]["apiImageDigest"],
            "sha256:b4e741093e83de6cf7f105381f87143163f3f14b376cb8df42350eeefeafb2bc",
        )
        self.assertEqual(config["deployment"]["apiRevision"], "<RM_CONTAINER_APP_NAME>--0000013")
        self.assertEqual(config["deployment"]["apiRevisionStatus"], "healthy-100-percent-traffic")
        self.assertEqual(config["deployment"]["teamsCatalogStatus"], "manual-sideload-required-missing-graph-scope")
        fabric = config["deployment"]["fabric"]
        self.assertEqual(fabric["capacitySku"], "F4")
        self.assertEqual(fabric["capacityState"], "Active")
        self.assertEqual(fabric["workspaceCapacityId"], fabric["capacityId"])
        self.assertEqual(fabric["workspaceName"], "<FABRIC_WORKSPACE_NAME>")
        self.assertEqual(fabric["lakehouseName"], "<FABRIC_LAKEHOUSE_NAME>")
        self.assertEqual(fabric["lakehouseStatus"], "medallion-built")
        self.assertEqual(fabric["bronzeFileCount"], 22)
        self.assertEqual(fabric["bronzeBytes"], 123908)
        self.assertEqual(fabric["dashboardDataSource"], "fabric-snapshot")
        self.assertEqual(fabric["dashboardCustomerCount"], 20)
        self.assertEqual(fabric["medallionNotebookName"], "01 Build Frontier RM Medallion")
        self.assertTrue(fabric["medallionNotebookId"])
        self.assertTrue(fabric["medallionJobInstanceId"])
        self.assertEqual(fabric["medallionJobStatus"], "Completed")
        self.assertEqual(fabric["bronzeTableCount"], 21)
        self.assertEqual(fabric["silverTableCount"], 21)
        self.assertEqual(fabric["goldTableCount"], 12)
        self.assertIn("meeting_context", fabric["goldTables"])
        self.assertEqual(fabric["semanticModelName"], "Frontier RM Semantic Model")
        self.assertEqual(fabric["semanticModelMode"], "DirectLake")
        self.assertEqual(fabric["semanticModelStatus"], "dax-validated")
        self.assertEqual(fabric["semanticModelTableCount"], 12)
        self.assertEqual(fabric["semanticModelMeasureCount"], 11)
        self.assertEqual(fabric["semanticModelValidatedValues"]["customers"], 20)
        self.assertEqual(fabric["semanticModelValidatedValues"]["opportunityPipeline"], 9_310_000)
        self.assertEqual(fabric["semanticModelValidatedValues"]["riskReviewsDue"], 2)
        self.assertEqual(fabric["semanticModelValidatedValues"]["materialActivities"], 20)
        self.assertEqual(fabric["semanticModelValidatedValues"]["activeHouseviewReports"], 1)
        self.assertEqual(fabric["ontologyEntityCount"], 15)
        self.assertEqual(fabric["ontologyRelationshipCount"], 13)
        self.assertEqual(fabric["ontologyDefinitionPartCount"], 58)
        self.assertEqual(fabric["houseviewReportCount"], 2)
        self.assertEqual(fabric["activeHouseviewId"], "houseview-2026-q4")
        self.assertEqual(fabric["activeHouseviewAsOf"], "2026-08-19")
        self.assertEqual(fabric["regulatoryRuleCount"], 15)
        self.assertEqual(fabric["agentRunMode"], "captured-live")
        self.assertEqual(fabric["dataAgentStatus"], "published-semantic-model-only")
        self.assertTrue(fabric["capturedLiveRunId"].endswith("-success"))
        self.assertEqual(
            set(config["requiredTags"]),
            {"workload", "environment", "owner", "expiry"},
        )

    def test_clean_room_provenance_exists(self):
        provenance = (ROOT / "docs" / "provenance.md").read_text(encoding="utf-8")

        self.assertIn("independently authored", provenance)
        self.assertIn("No third-party source code", provenance)


if __name__ == "__main__":
    unittest.main()