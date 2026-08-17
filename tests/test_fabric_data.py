import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "packages" / "fabric-data" / "generated"
sys.path.insert(0, str(ROOT / "scripts"))

from generate_rm_fabric_data import DATASET_NAMES, DEFAULT_SEED, write_datasets  # noqa: E402


def load_jsonl(name: str, directory: Path = GENERATED) -> list[dict]:
    return [json.loads(line) for line in (directory / f"{name}.jsonl").read_text(encoding="ascii").splitlines()]


class FabricDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {name: load_jsonl(name) for name in DATASET_NAMES}
        cls.manifest = json.loads((GENERATED / "manifest.json").read_text(encoding="ascii"))

    def test_regeneration_is_byte_for_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_dir = Path(first)
            second_dir = Path(second)
            write_datasets(first_dir, DEFAULT_SEED)
            write_datasets(second_dir, DEFAULT_SEED)

            expected_files = [f"{name}.jsonl" for name in DATASET_NAMES] + ["manifest.json"]
            for filename in expected_files:
                with self.subTest(filename=filename):
                    first_bytes = (first_dir / filename).read_bytes()
                    self.assertEqual(first_bytes, (second_dir / filename).read_bytes())
                    self.assertEqual(first_bytes, (GENERATED / filename).read_bytes())

    def test_has_twenty_customers_and_unique_primary_keys(self):
        self.assertEqual(len(self.tables["customers"]), 20)
        primary_keys = {
            "relationship_managers": "rm_id",
            "customers": "customer_id",
            "households": "household_id",
            "accounts": "account_id",
            "holdings": "holding_id",
            "products": "product_id",
            "transactions": "transaction_id",
            "interactions": "interaction_id",
            "compliance_profiles": "compliance_profile_id",
            "opportunities": "opportunity_id",
            "customer_events": "event_id",
            "market_snapshots": "market_snapshot_id",
            "rm_actions": "rm_action_id",
            "client_advisory_profiles": "advisory_profile_id",
            "risk_profile_history": "risk_history_id",
            "client_investment_activity": "investment_activity_id",
            "observed_behaviour_history": "behaviour_history_id",
            "cio_houseview_reports": "houseview_id",
            "cio_houseview_sections": "houseview_section_id",
            "regulatory_documents": "regulatory_document_id",
            "regulatory_rules": "regulatory_rule_id",
        }
        for table, primary_key in primary_keys.items():
            values = [row[primary_key] for row in self.tables[table]]
            with self.subTest(table=table):
                self.assertTrue(values)
                self.assertEqual(len(values), len(set(values)))

    def test_required_foreign_keys_resolve(self):
        ids = {
            "rm": {row["rm_id"] for row in self.tables["relationship_managers"]},
            "customer": {row["customer_id"] for row in self.tables["customers"]},
            "household": {row["household_id"] for row in self.tables["households"]},
            "account": {row["account_id"] for row in self.tables["accounts"]},
            "product": {row["product_id"] for row in self.tables["products"]},
            "opportunity": {row["opportunity_id"] for row in self.tables["opportunities"]},
            "event": {row["event_id"] for row in self.tables["customer_events"]},
        }
        contracts = {
            "customers": (("rm_id", "rm"), ("household_id", "household")),
            "households": (("rm_id", "rm"), ("primary_customer_id", "customer")),
            "accounts": (("customer_id", "customer"), ("household_id", "household"), ("product_id", "product")),
            "holdings": (("account_id", "account"), ("product_id", "product")),
            "transactions": (("account_id", "account"), ("customer_id", "customer")),
            "interactions": (("customer_id", "customer"), ("rm_id", "rm")),
            "compliance_profiles": (("customer_id", "customer"),),
            "opportunities": (("customer_id", "customer"), ("event_id", "event"), ("rm_id", "rm")),
            "customer_events": (("customer_id", "customer"), ("account_id", "account")),
            "market_snapshots": (("product_id", "product"),),
            "rm_actions": (("rm_id", "rm"), ("customer_id", "customer"), ("opportunity_id", "opportunity")),
            "client_advisory_profiles": (("customer_id", "customer"),),
            "risk_profile_history": (("customer_id", "customer"),),
            "client_investment_activity": (("customer_id", "customer"), ("account_id", "account"), ("product_id", "product")),
            "observed_behaviour_history": (("customer_id", "customer"),),
        }
        for table, foreign_keys in contracts.items():
            for row in self.tables[table]:
                for field, target in foreign_keys:
                    with self.subTest(table=table, field=field, value=row[field]):
                        self.assertIn(row[field], ids[target])

    def test_stable_clients_are_assigned_to_john_doe(self):
        managers = {row["rm_id"]: row for row in self.tables["relationship_managers"]}
        customers = {row["customer_id"]: row for row in self.tables["customers"]}

        self.assertEqual(managers["rm-john-doe"]["display_name"], "John Doe")
        self.assertEqual(managers["rm-john-doe"]["initials"], "JD")
        expected = {
            "client-lim": "Daniel Lim",
            "client-tan": "Mei Tan",
            "client-ng": "Jonathan Ng",
            "client-lee": "Priya Lee",
        }
        for customer_id, name in expected.items():
            with self.subTest(customer_id=customer_id):
                self.assertEqual(customers[customer_id]["full_name"], name)
                self.assertEqual(customers[customer_id]["rm_id"], "rm-john-doe")

    def test_stable_client_scenarios_are_preserved(self):
        opportunities = {row["customer_id"]: row for row in self.tables["opportunities"]}
        compliance = {row["customer_id"]: row for row in self.tables["compliance_profiles"]}
        events = self.tables["customer_events"]

        daniel_events = {row["event_type"]: row for row in events if row["customer_id"] == "client-lim"}
        self.assertEqual(daniel_events["FIXED_DEPOSIT_MATURITY"]["event_value"], 650_000)
        self.assertEqual(daniel_events["FIXED_DEPOSIT_MATURITY"]["maturity_date"], "2026-08-24")
        self.assertEqual(daniel_events["SUSTAINED_IDLE_CASH"]["event_value"], 210_000)
        self.assertEqual(daniel_events["SUSTAINED_IDLE_CASH"]["observation_days"], 90)
        self.assertEqual(opportunities["client-lim"]["opportunity_id"], "opp-fd-maturity")
        self.assertEqual(opportunities["client-lim"]["event_id"], "event-01")

        mei_event = next(row for row in events if row["customer_id"] == "client-tan")
        self.assertEqual(compliance["client-tan"]["kyc_status"], "REFRESH_DUE")
        self.assertEqual(compliance["client-tan"]["kyc_due_date"], "2026-09-02")
        self.assertEqual(mei_event["event_type"], "BENEFICIARY_CHANGE")
        self.assertEqual(opportunities["client-tan"]["event_id"], "event-02")

        jonathan_event = next(row for row in events if row["customer_id"] == "client-ng")
        self.assertEqual(jonathan_event["event_type"], "MORTGAGE_REPRICING_WINDOW")
        self.assertEqual(jonathan_event["window_opens_date"], "2026-09-11")
        self.assertEqual(opportunities["client-ng"]["opportunity_id"], "opp-mortgage")
        self.assertEqual(opportunities["client-ng"]["event_id"], "event-03")

        priya_event = next(row for row in events if row["customer_id"] == "client-lee")
        self.assertEqual(priya_event["event_type"], "CROSS_BORDER_TRANSFER_INCREASE")
        self.assertEqual(priya_event["event_value"], 540_000)
        self.assertEqual(opportunities["client-lee"]["opportunity_id"], "opp-cross-border")
        self.assertEqual(opportunities["client-lee"]["event_id"], "event-04")

    def test_sgd_amounts_and_singapore_timestamps(self):
        amount_fields = {
            "relationship_value",
            "balance",
            "market_value",
            "cost_value",
            "amount",
            "estimated_value",
            "event_value",
            "reference_value",
        }
        checked_amounts = 0
        checked_timestamps = 0
        for table, rows in self.tables.items():
            for row in rows:
                for field, value in row.items():
                    if field in amount_fields:
                        checked_amounts += 1
                        self.assertIsInstance(value, (int, float), f"{table}.{field}")
                        self.assertEqual(row["currency"], "SGD", f"{table}.{field}")
                    if field.endswith("_at"):
                        checked_timestamps += 1
                        self.assertTrue(value.endswith("+08:00"), f"{table}.{field}={value}")
        self.assertGreater(checked_amounts, 0)
        self.assertGreater(checked_timestamps, 0)

    def test_manifest_matches_generated_rows(self):
        self.assertEqual(self.manifest["schemaVersion"], "1.0")
        self.assertEqual(self.manifest["seed"], DEFAULT_SEED)
        self.assertEqual(self.manifest["generatedAt"], "2026-08-12T08:30:00+08:00")
        self.assertTrue(self.manifest["synthetic"])
        self.assertIn("fictional synthetic data", self.manifest["declaration"])
        self.assertEqual(
            self.manifest["rowCounts"],
            {name: len(rows) for name, rows in self.tables.items()},
        )

    def test_declared_profile_and_observed_behaviour_are_separate(self):
        profiles = {row["customer_id"]: row for row in self.tables["client_advisory_profiles"]}
        history = {row["customer_id"]: row for row in self.tables["risk_profile_history"]}
        behaviour = {row["customer_id"]: row for row in self.tables["observed_behaviour_history"]}
        activities = {row["investment_activity_id"]: row for row in self.tables["client_investment_activity"]}

        for customer_id, profile in profiles.items():
            with self.subTest(customer_id=customer_id):
                self.assertIn(profile["declared_risk_score"], range(1, 6))
                self.assertIn(profile["observed_behaviour_indicator"], range(1, 6))
                self.assertEqual(history[customer_id]["declared_risk_score"], profile["declared_risk_score"])
                self.assertFalse(behaviour[customer_id]["declared_profile_changed"])
                self.assertIn(behaviour[customer_id]["trigger_activity_id"], activities)

        daniel = profiles["client-lim"]
        daniel_behaviour = behaviour["client-lim"]
        daniel_activity = activities[daniel_behaviour["trigger_activity_id"]]
        self.assertEqual(daniel["declared_risk_score"], 3)
        self.assertEqual(daniel["observed_behaviour_indicator"], 2)
        self.assertEqual(daniel_behaviour["previous_indicator"], 3)
        self.assertEqual(daniel_activity["activity_type"], "SELL")
        self.assertEqual(daniel_activity["asset_class"], "EQUITY")
        self.assertEqual(daniel_activity["amount"], 320_000)

    def test_retirement_triggers_review_without_overwriting_risk(self):
        profiles = {row["customer_id"]: row for row in self.tables["client_advisory_profiles"]}
        mei = profiles["client-tan"]

        self.assertEqual(mei["employment_status"], "RETIRED")
        self.assertEqual(mei["declared_risk_score"], 2)
        self.assertEqual(mei["risk_review_status"], "REVIEW_REQUIRED")
        self.assertFalse(mei["income_complete"])
        self.assertFalse(mei["commitments_complete"])
        self.assertEqual(mei["knowledge_experience_status"], "INCOMPLETE")

    def test_houseview_and_regulatory_citations_are_complete(self):
        reports = {row["houseview_id"]: row for row in self.tables["cio_houseview_reports"]}
        sections = self.tables["cio_houseview_sections"]
        documents = {row["regulatory_document_id"]: row for row in self.tables["regulatory_documents"]}
        rules = self.tables["regulatory_rules"]

        self.assertEqual(len(reports), 2)
        self.assertEqual(sum(row["status"] == "ACTIVE" for row in reports.values()), 1)
        self.assertTrue(all(section["houseview_id"] in reports for section in sections))
        self.assertTrue(all(rule["regulatory_document_id"] in documents for rule in rules))
        self.assertTrue(all(rule["regulatory_rule_id"].startswith("FAA-N16-") for rule in rules))
        self.assertIn("Not the official MAS notice", next(iter(documents.values()))["disclaimer"])


if __name__ == "__main__":
    unittest.main()