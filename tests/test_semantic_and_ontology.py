import json
import re
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "fabric" / "semantic-model" / "FrontierRM.SemanticModel"
DEFINITION = MODEL / "definition"
TABLES = DEFINITION / "tables"
ONTOLOGY = ROOT / "fabric" / "ontology"
ONTOLOGY_DEFINITION = ONTOLOGY / "definition"
sys.path.insert(0, str(ROOT / "scripts"))

from deploy_frontier_semantic_model import MODEL_NAME, azure_cli, definition_parts, expected_values  # noqa: E402
from deploy_frontier_ontology import definition_parts as ontology_parts, preview as ontology_preview  # noqa: E402


class SemanticAndOntologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology_spec = json.loads((ONTOLOGY / "spec.json").read_text(encoding="ascii"))
        cls.ontology_ids = json.loads((ONTOLOGY / "id-map.json").read_text(encoding="ascii"))
        cls.ontology_entities = {}
        cls.ontology_bindings = {}
        cls.ontology_relationships = {}
        cls.ontology_contextualizations = {}
        for path in (ONTOLOGY_DEFINITION / "EntityTypes").glob("*/definition.json"):
            entity = json.loads(path.read_text(encoding="ascii"))
            cls.ontology_entities[entity["name"]] = entity
            binding_path = next((path.parent / "DataBindings").glob("*.json"))
            cls.ontology_bindings[entity["name"]] = json.loads(binding_path.read_text(encoding="ascii"))
        for path in (ONTOLOGY_DEFINITION / "RelationshipTypes").glob("*/definition.json"):
            relationship = json.loads(path.read_text(encoding="ascii"))
            cls.ontology_relationships[relationship["name"]] = relationship
            contextualization_path = next((path.parent / "Contextualizations").glob("*.json"))
            cls.ontology_contextualizations[relationship["name"]] = json.loads(
                contextualization_path.read_text(encoding="ascii")
            )

    def test_direct_lake_model_has_complete_source_tree(self):
        settings = json.loads((MODEL / "definition.pbism").read_text(encoding="utf-8"))
        self.assertTrue(settings["settings"]["qnaEnabled"])
        self.assertIn("compatibilityLevel: 1702", (DEFINITION / "database.tmdl").read_text(encoding="utf-8"))

        expression = (DEFINITION / "expressions.tmdl").read_text(encoding="utf-8")
        self.assertIn("67764587-fefa-43e9-ad2e-66b47e7ea18d", expression)
        self.assertIn("a86aee8e-0382-4105-bd78-457af69d8830", expression)

        expected_files = {
            "Customer.tmdl",
            "Opportunities.tmdl",
            "Portfolio Exposure.tmdl",
            "Maturity Watchlist.tmdl",
            "Engagement Gap.tmdl",
            "Compliance Due.tmdl",
            "Meeting Context.tmdl",
                    "Advisory Profile.tmdl",
                    "Activity Evidence.tmdl",
                    "Houseview Documents.tmdl",
                    "Regulatory Controls.tmdl",
                    "Recommendation Context.tmdl",
        }
        self.assertEqual({path.name for path in TABLES.glob("*.tmdl")}, expected_files)

        expected_entities = {
            "customer_360",
            "rm_opportunity_snapshot",
            "portfolio_exposure",
            "maturity_watchlist",
            "engagement_gap",
            "compliance_due",
            "meeting_context",
                    "client_advisory_context",
                    "client_activity_evidence",
                    "houseview_document_index",
                    "regulatory_control_register",
                    "recommendation_grounding_context",
        }
        entities = set()
        for path in TABLES.glob("*.tmdl"):
            content = path.read_text(encoding="utf-8")
            self.assertIn("mode: directLake", content, path.name)
            self.assertIn("schemaName: gold", content, path.name)
            self.assertIn("expressionSource: 'DirectLake - FrontierRMLakehouse'", content, path.name)
            self.assertNotRegex(content, r"dataType:\s+double", path.name)
            entities.update(re.findall(r"entityName:\s+([^\s]+)", content))
        self.assertEqual(entities, expected_entities)

    def test_model_has_business_measures_and_relationships(self):
        all_tables = "\n".join(path.read_text(encoding="utf-8") for path in TABLES.glob("*.tmdl"))
        for measure in (
            "# Customers",
            "Assets Under Care",
            "Opportunity Pipeline",
            "# Open Opportunities",
            "Average Confidence",
            "Portfolio Market Value",
            "Maturing Value",
            "# Compliance Reviews",
                    "# Risk Reviews Due",
                    "# Material Activities",
                    "# Active Houseview Reports",
        ):
            self.assertIn(f"measure '{measure}'", all_tables)
        self.assertNotRegex(all_tables, r"(?:'[^']+'|[A-Za-z]+)\.'[^']+'")

        model = (DEFINITION / "model.tmdl").read_text(encoding="utf-8")
        self.assertIn("discourageImplicitMeasures", model)
        self.assertEqual(model.count("ref table"), 12)

        relationships = (DEFINITION / "relationships.tmdl").read_text(encoding="utf-8")
        self.assertEqual(relationships.count("relationship '"), 9)
        self.assertEqual(relationships.count("toColumn: Customer.'Customer ID'"), 9)

        opportunities = (TABLES / "Opportunities.tmdl").read_text(encoding="utf-8")
        meeting_context = (TABLES / "Meeting Context.tmdl").read_text(encoding="utf-8")
        self.assertIn("sourceColumn: event_id", opportunities)
        self.assertIn("sourceColumn: event_id", meeting_context)

    def test_technical_keys_and_aggregated_values_are_hidden(self):
        all_tables = "\n".join(path.read_text(encoding="utf-8") for path in TABLES.glob("*.tmdl"))
        for column in ("Customer ID", "Relationship Manager ID", "Opportunity ID", "Event ID"):
            pattern = rf"column '{re.escape(column)}'[\s\S]*?isHidden"
            self.assertRegex(all_tables, pattern)

        for measure in re.findall(r"measure '[^']+'[^\n]*", all_tables):
            start = all_tables.index(measure)
            block = all_tables[start : start + 220]
            self.assertIn("formatString:", block, measure)

    def test_opportunity_event_foreign_key_is_complete(self):
        generated = ROOT / "packages" / "fabric-data" / "generated"
        events = {
            json.loads(line)["event_id"]
            for line in (generated / "customer_events.jsonl").read_text(encoding="ascii").splitlines()
        }
        opportunities = [
            json.loads(line)
            for line in (generated / "opportunities.jsonl").read_text(encoding="ascii").splitlines()
        ]
        self.assertTrue(all(item["event_id"] in events for item in opportunities))
        self.assertEqual(len({item["event_id"] for item in opportunities}), len(opportunities))

    def test_deployment_envelope_contains_every_model_part(self):
        parts = definition_parts(MODEL)
        paths = {part["path"] for part in parts}
        self.assertEqual(MODEL_NAME, "Frontier RM Semantic Model")
        self.assertIn("definition.pbism", paths)
        self.assertIn("definition/database.tmdl", paths)
        self.assertIn("definition/model.tmdl", paths)
        self.assertIn("definition/expressions.tmdl", paths)
        self.assertIn("definition/relationships.tmdl", paths)
        self.assertEqual(len([path for path in paths if path.startswith("definition/tables/")]), 12)
        self.assertTrue(all(part["payloadType"] == "InlineBase64" for part in parts))

    def test_expected_dax_values_come_from_generated_snapshot(self):
        expected = expected_values()
        self.assertEqual(expected["Customers"], 20)
        self.assertEqual(expected["DanielAssets"], 4_800_000)
        self.assertEqual(expected["OpenOpportunities"], 20)
        self.assertGreater(expected["OpportunityPipeline"], 0)
        self.assertEqual(expected["MaturingValue"], 650_000)
        self.assertGreater(expected["RiskReviewsDue"], 0)
        self.assertEqual(expected["MaterialActivities"], 20)
        self.assertEqual(expected["ActiveHouseviewReports"], 1)

    def test_azure_cli_can_be_resolved_for_deployment(self):
        self.assertTrue(Path(azure_cli()).is_file())

    def test_ontology_has_exact_platform_and_expected_definition_parts(self):
        platform = json.loads((ONTOLOGY_DEFINITION / ".platform").read_text(encoding="ascii"))
        self.assertEqual(
            platform,
            {"metadata": {"type": "Ontology", "displayName": "Frontier_RM_Ontology"}},
        )
        self.assertEqual((ONTOLOGY_DEFINITION / "definition.json").read_bytes(), b"{}")
        self.assertEqual(len(self.ontology_entities), 15)
        self.assertEqual(len(self.ontology_relationships), 13)
        self.assertEqual(set(self.ontology_entities), {item["name"] for item in self.ontology_spec["entityTypes"]})
        self.assertEqual(
            set(self.ontology_relationships),
            {item["name"] for item in self.ontology_spec["relationshipTypes"]},
        )
        paths = [path.relative_to(ONTOLOGY_DEFINITION).as_posix() for path in ONTOLOGY_DEFINITION.rglob("*") if path.is_file()]
        self.assertEqual(len(paths), 58)
        self.assertTrue(all("\\" not in path for path in paths))

    def test_ontology_ids_are_globally_unique_positive_and_deterministic(self):
        numeric_ids = []
        property_names = []
        for entity in self.ontology_entities.values():
            numeric_ids.append(entity["id"])
            numeric_ids.extend(prop["id"] for prop in entity["properties"])
            property_names.extend(prop["name"] for prop in entity["properties"])
        numeric_ids.extend(relationship["id"] for relationship in self.ontology_relationships.values())
        self.assertEqual(len(numeric_ids), len(set(numeric_ids)))
        self.assertTrue(all(identifier.isdigit() and 15 <= len(identifier) <= 18 and int(identifier) > 0 for identifier in numeric_ids))
        self.assertEqual(len(property_names), len(set(property_names)))

        mapped_ids = []
        for entity in self.ontology_ids["entityTypes"].values():
            mapped_ids.append(entity["id"])
            mapped_ids.extend(entity["properties"].values())
        mapped_ids.extend(item["id"] for item in self.ontology_ids["relationshipTypes"].values())
        self.assertEqual(set(mapped_ids), set(numeric_ids))

    def test_ontology_binding_guids_are_unique_and_sources_match_silver_tables(self):
        workspace_id = "67764587-fefa-43e9-ad2e-66b47e7ea18d"
        lakehouse_id = "a86aee8e-0382-4105-bd78-457af69d8830"
        all_guids = list(self.ontology_ids["bindings"].values())
        all_guids.extend(item["contextualizationId"] for item in self.ontology_ids["relationshipTypes"].values())
        self.assertEqual(len(all_guids), len(set(all_guids)))
        self.assertTrue(all(str(uuid.UUID(value)) == value for value in all_guids))

        specs = {item["name"]: item for item in self.ontology_spec["entityTypes"]}
        generated = ROOT / "packages" / "fabric-data" / "generated"
        for entity_name, binding in self.ontology_bindings.items():
            spec = specs[entity_name]
            configuration = binding["dataBindingConfiguration"]
            source = configuration["sourceTableProperties"]
            rows = [json.loads(line) for line in (generated / f"{spec['sourceTableName']}.jsonl").read_text(encoding="ascii").splitlines()]
            source_columns = set().union(*(row.keys() for row in rows))
            property_ids = {prop["id"] for prop in self.ontology_entities[entity_name]["properties"]}
            self.assertEqual(configuration["dataBindingType"], "NonTimeSeries")
            self.assertEqual(source["sourceType"], "LakehouseTable")
            self.assertEqual(source["workspaceId"], workspace_id)
            self.assertEqual(source["itemId"], lakehouse_id)
            self.assertEqual(source["sourceSchema"], "silver")
            self.assertEqual(source["sourceTableName"], spec["sourceTableName"])
            self.assertEqual({item["sourceColumnName"] for item in configuration["propertyBindings"]}, {item["sourceColumnName"] for item in spec["properties"]})
            self.assertTrue(all(item["sourceColumnName"] in source_columns for item in configuration["propertyBindings"]))
            self.assertTrue(all(item["targetPropertyId"] in property_ids for item in configuration["propertyBindings"]))

    def test_ontology_keys_and_relationship_contextualizations_are_valid(self):
        entities_by_id = {entity["id"]: entity for entity in self.ontology_entities.values()}
        generated = ROOT / "packages" / "fabric-data" / "generated"
        for entity in self.ontology_entities.values():
            properties = {prop["id"]: prop for prop in entity["properties"]}
            self.assertTrue(all(properties[key]["valueType"] in {"String", "BigInt"} for key in entity["entityIdParts"]))

        for relationship_name, relationship in self.ontology_relationships.items():
            source_id = relationship["source"]["entityTypeId"]
            target_id = relationship["target"]["entityTypeId"]
            self.assertIn(source_id, entities_by_id)
            self.assertIn(target_id, entities_by_id)
            self.assertNotEqual(source_id, target_id)

            contextualization = self.ontology_contextualizations[relationship_name]
            table = contextualization["dataBindingTable"]
            rows = [json.loads(line) for line in (generated / f"{table['sourceTableName']}.jsonl").read_text(encoding="ascii").splitlines()]
            table_columns = set().union(*(row.keys() for row in rows))
            source_keys = set(entities_by_id[source_id]["entityIdParts"])
            target_keys = set(entities_by_id[target_id]["entityIdParts"])
            self.assertEqual(table["sourceSchema"], "silver")
            self.assertTrue(all(item["sourceColumnName"] in table_columns for item in contextualization["sourceKeyRefBindings"]))
            self.assertTrue(all(item["sourceColumnName"] in table_columns for item in contextualization["targetKeyRefBindings"]))
            self.assertTrue(all(item["targetPropertyId"] in source_keys for item in contextualization["sourceKeyRefBindings"]))
            self.assertTrue(all(item["targetPropertyId"] in target_keys for item in contextualization["targetKeyRefBindings"]))

    def test_opportunities_include_event_id_in_generated_data_and_ontology(self):
        generated = ROOT / "packages" / "fabric-data" / "generated" / "opportunities.jsonl"
        opportunities = [json.loads(line) for line in generated.read_text(encoding="ascii").splitlines()]
        self.assertTrue(opportunities)
        self.assertTrue(all(item.get("event_id") for item in opportunities))
        opportunity_binding = self.ontology_bindings["Opportunity"]["dataBindingConfiguration"]["propertyBindings"]
        self.assertIn("event_id", {item["sourceColumnName"] for item in opportunity_binding})

    def test_ontology_deployment_envelope_and_preview_are_complete(self):
        parts = ontology_parts()
        paths = {part["path"] for part in parts}
        summary = ontology_preview()
        self.assertEqual(len(parts), 58)
        self.assertEqual(summary["displayName"], "Frontier_RM_Ontology")
        self.assertEqual(summary["entities"], 15)
        self.assertEqual(summary["relationships"], 13)
        self.assertEqual(summary["bindings"], 15)
        self.assertEqual(summary["parts"], 58)
        self.assertEqual(summary["sourceSchema"], "silver")
        self.assertIn(".platform", paths)
        self.assertIn("definition.json", paths)
        self.assertTrue(all("\\" not in path for path in paths))
        self.assertTrue(all(part["payloadType"] == "InlineBase64" for part in parts))


if __name__ == "__main__":
    unittest.main()
