from __future__ import annotations

import argparse
import json
import random
import shutil
import tempfile
from pathlib import Path


DEFAULT_SEED = 20260812
SCHEMA_VERSION = "1.0"
GENERATED_AT = "2026-08-12T08:30:00+08:00"
DATASET_NAMES = (
    "relationship_managers",
    "customers",
    "households",
    "accounts",
    "holdings",
    "products",
    "transactions",
    "interactions",
    "compliance_profiles",
    "opportunities",
    "customer_events",
    "market_snapshots",
    "rm_actions",
    "client_advisory_profiles",
    "risk_profile_history",
    "client_investment_activity",
    "observed_behaviour_history",
    "cio_houseview_reports",
    "cio_houseview_sections",
    "regulatory_documents",
    "regulatory_rules",
)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "packages" / "fabric-data" / "generated"
HOUSEVIEW_SOURCE = ROOT / "packages" / "demo-data" / "houseview" / "houseviews.json"
REGULATORY_SOURCE = ROOT / "packages" / "demo-data" / "regulatory" / "faa_n16_control_pack.json"


STABLE_CLIENTS = (
    {
        "customer_id": "client-lim",
        "household_id": "household-lim",
        "full_name": "Daniel Lim",
        "segment": "Premier Private Client",
        "risk_profile": "Balanced Growth",
        "contact_preference": "Secure message, then call",
        "consent_status": "Current",
        "relationship_value": 4_800_000,
        "kyc_status": "CURRENT",
        "kyc_due_date": "2027-03-18",
    },
    {
        "customer_id": "client-tan",
        "household_id": "household-tan",
        "full_name": "Mei Tan",
        "segment": "Premier Banking",
        "risk_profile": "Moderate",
        "contact_preference": "Phone",
        "consent_status": "Current",
        "relationship_value": 2_300_000,
        "kyc_status": "REFRESH_DUE",
        "kyc_due_date": "2026-09-02",
    },
    {
        "customer_id": "client-ng",
        "household_id": "household-ng",
        "full_name": "Jonathan Ng",
        "segment": "Premier Banking",
        "risk_profile": "Conservative",
        "contact_preference": "Email",
        "consent_status": "Current",
        "relationship_value": 1_700_000,
        "kyc_status": "CURRENT",
        "kyc_due_date": "2026-11-20",
    },
    {
        "customer_id": "client-lee",
        "household_id": "household-lee",
        "full_name": "Priya Lee",
        "segment": "Premier Banking",
        "risk_profile": "Growth",
        "contact_preference": "Secure message",
        "consent_status": "Do not call before 10:00",
        "relationship_value": 3_100_000,
        "kyc_status": "CURRENT",
        "kyc_due_date": "2027-07-16",
    },
)

FICTIONAL_NAMES = (
    "Adrian Koh",
    "Sofia Raman",
    "Marcus Teo",
    "Alicia Goh",
    "Ethan Chua",
    "Nadia Wong",
    "Ryan Ho",
    "Leona Yeo",
    "Caleb Ong",
    "Maya Low",
    "Isaac Quek",
    "Tara Sim",
    "Noah Tay",
    "Elena Seah",
    "Lucas Toh",
    "Anika Foo",
)

PRODUCTS = (
    ("product-current-sgd", "Current Account", "DEPOSIT", "CASH"),
    ("product-savings-sgd", "Premier Savings", "DEPOSIT", "CASH"),
    ("product-fixed-deposit-sgd", "Fixed Deposit", "TERM_DEPOSIT", "FIXED_INCOME"),
    ("product-investment-sgd", "Investment Portfolio", "INVESTMENT", "MULTI_ASSET"),
    ("product-unit-trust-sgd", "Unit Trust Portfolio", "INVESTMENT", "MULTI_ASSET"),
    ("product-mortgage-sgd", "Residential Mortgage", "LENDING", "PROPERTY"),
    ("product-multicurrency-sgd", "Multi-Currency Account", "DEPOSIT", "CASH"),
    ("product-card-sgd", "Premier Card", "CARD", "CREDIT"),
)


def timestamp(day: int, hour: int, minute: int = 0) -> str:
    return f"2026-08-{day:02d}T{hour:02d}:{minute:02d}:00+08:00"


def build_datasets(seed: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    datasets = {name: [] for name in DATASET_NAMES}
    rm_id = "rm-john-doe"
    datasets["relationship_managers"].append(
        {
            "rm_id": rm_id,
            "display_name": "John Doe",
            "initials": "JD",
            "role": "Premier Relationship Manager",
            "team": "Premier Banking, Singapore",
            "location": "Singapore",
            "active": True,
            "created_at": GENERATED_AT,
        }
    )

    for product_id, name, product_type, asset_class in PRODUCTS:
        datasets["products"].append(
            {
                "product_id": product_id,
                "product_name": name,
                "product_type": product_type,
                "asset_class": asset_class,
                "currency": "SGD",
                "synthetic": True,
                "effective_at": "2026-08-01T00:00:00+08:00",
            }
        )

    generated_clients = []
    for index, name in enumerate(FICTIONAL_NAMES, start=5):
        slug = f"synthetic-{index:02d}"
        generated_clients.append(
            {
                "customer_id": f"client-{slug}",
                "household_id": f"household-{slug}",
                "full_name": name,
                "segment": rng.choice(("Premier Banking", "Premier Banking", "Premier Private Client")),
                "risk_profile": rng.choice(("Conservative", "Moderate", "Balanced Growth", "Growth")),
                "contact_preference": rng.choice(("Phone", "Email", "Secure message")),
                "consent_status": "Current",
                "relationship_value": rng.randrange(900_000, 4_200_001, 25_000),
                "kyc_status": rng.choice(("CURRENT", "CURRENT", "REFRESH_DUE")),
                "kyc_due_date": f"2027-{rng.randint(1, 8):02d}-{rng.randint(10, 27):02d}",
            }
        )

    clients = [dict(item) for item in STABLE_CLIENTS] + generated_clients
    account_product_pairs = (
        ("operating", "product-current-sgd"),
        ("portfolio", "product-investment-sgd"),
    )

    for position, client in enumerate(clients, start=1):
        customer_id = client["customer_id"]
        household_id = client["household_id"]
        family_name = client["full_name"].split()[-1]
        datasets["customers"].append(
            {
                "customer_id": customer_id,
                "household_id": household_id,
                "rm_id": rm_id,
                "full_name": client["full_name"],
                "segment": client["segment"],
                "risk_profile": client["risk_profile"],
                "contact_preference": client["contact_preference"],
                "consent_status": client["consent_status"],
                "relationship_value": client["relationship_value"],
                "currency": "SGD",
                "country_code": "SG",
                "synthetic": True,
                "created_at": timestamp(1 + position % 10, 9, position % 60),
            }
        )
        datasets["households"].append(
            {
                "household_id": household_id,
                "household_name": f"{family_name} Household",
                "rm_id": rm_id,
                "primary_customer_id": customer_id,
                "member_count": 1,
                "relationship_value": client["relationship_value"],
                "currency": "SGD",
                "snapshot_at": GENERATED_AT,
            }
        )
        datasets["compliance_profiles"].append(
            {
                "compliance_profile_id": f"compliance-{customer_id}",
                "customer_id": customer_id,
                "kyc_status": client["kyc_status"],
                "kyc_due_date": client["kyc_due_date"],
                "aml_risk_rating": rng.choice(("LOW", "LOW", "STANDARD")),
                "suitability_status": "CURRENT" if client["kyc_status"] == "CURRENT" else "REVIEW_REQUIRED",
                "reviewed_at": timestamp(2 + position % 8, 10, position % 60),
            }
        )

        account_ids = []
        for account_kind, product_id in account_product_pairs:
            account_id = f"account-{position:02d}-{account_kind}"
            balance = (
                rng.randrange(80_000, 650_001, 5_000)
                if account_kind == "operating"
                else rng.randrange(350_000, 2_400_001, 10_000)
            )
            account_ids.append(account_id)
            datasets["accounts"].append(
                {
                    "account_id": account_id,
                    "customer_id": customer_id,
                    "household_id": household_id,
                    "product_id": product_id,
                    "account_type": account_kind.upper(),
                    "status": "OPEN",
                    "balance": balance,
                    "currency": "SGD",
                    "opened_at": timestamp(1 + position % 9, 8, position % 60),
                }
            )
            datasets["holdings"].append(
                {
                    "holding_id": f"holding-{position:02d}-{account_kind}",
                    "account_id": account_id,
                    "product_id": product_id,
                    "quantity": 1,
                    "market_value": balance,
                    "cost_value": round(balance * 0.94) if account_kind == "portfolio" else balance,
                    "currency": "SGD",
                    "valued_at": GENERATED_AT,
                }
            )

        for sequence in range(3):
            amount = rng.randrange(800, 35_001, 100)
            transaction_type = ("CREDIT", "DEBIT", "TRANSFER")[sequence]
            datasets["transactions"].append(
                {
                    "transaction_id": f"txn-{position:02d}-{sequence + 1:02d}",
                    "account_id": account_ids[sequence % len(account_ids)],
                    "customer_id": customer_id,
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "currency": "SGD",
                    "description": f"Synthetic {transaction_type.lower()} activity",
                    "booked_at": timestamp(6 + sequence, 11 + sequence, position % 60),
                }
            )

        interaction_channel = client["contact_preference"].split(",")[0].upper().replace(" ", "_")
        datasets["interactions"].append(
            {
                "interaction_id": f"interaction-{position:02d}",
                "customer_id": customer_id,
                "rm_id": rm_id,
                "channel": interaction_channel,
                "interaction_type": "REVIEW",
                "summary": "Discussed fictional relationship priorities and service needs.",
                "occurred_at": timestamp(3 + position % 7, 10 + position % 6, position % 60),
            }
        )

        priority = rng.choice(("THIS_WEEK", "THIS_MONTH", "MONITOR"))
        opportunity_type = rng.choice(("PORTFOLIO_REVIEW", "SERVICE_REVIEW", "LIQUIDITY_REVIEW"))
        opportunity_id = f"opportunity-{position:02d}"
        opportunity_value = rng.randrange(75_000, 550_001, 5_000)
        datasets["opportunities"].append(
            {
                "opportunity_id": opportunity_id,
                "customer_id": customer_id,
                "event_id": f"event-{position:02d}",
                "rm_id": rm_id,
                "opportunity_type": opportunity_type,
                "title": "Review current relationship priorities",
                "status": "OPEN",
                "priority": priority,
                "estimated_value": opportunity_value,
                "currency": "SGD",
                "confidence_score": rng.randint(65, 91),
                "created_at": timestamp(8, 7, position % 60),
            }
        )
        datasets["customer_events"].append(
            {
                "event_id": f"event-{position:02d}",
                "customer_id": customer_id,
                "account_id": account_ids[0],
                "event_type": "BALANCE_CHANGE",
                "event_value": rng.randrange(20_000, 180_001, 5_000),
                "currency": "SGD",
                "event_at": timestamp(10, 7, position % 60),
                "source": "synthetic-scenario-engine",
            }
        )
        datasets["rm_actions"].append(
            {
                "rm_action_id": f"action-{position:02d}",
                "rm_id": rm_id,
                "customer_id": customer_id,
                "opportunity_id": opportunity_id,
                "action_type": "PREPARE_REVIEW",
                "status": "PLANNED",
                "due_at": timestamp(13 + position % 5, 9 + position % 7, 0),
                "created_at": GENERATED_AT,
            }
        )

    apply_stable_scenarios(datasets)
    add_market_snapshots(datasets)
    add_advisory_and_governance_data(datasets, clients, rng)
    return datasets


def replace_by_id(rows: list[dict], key: str, record_id: str, values: dict) -> None:
    row = next(item for item in rows if item[key] == record_id)
    row.update(values)


def apply_stable_scenarios(datasets: dict[str, list[dict]]) -> None:
    replace_by_id(
        datasets["holdings"],
        "holding_id",
        "holding-01-portfolio",
        {"product_id": "product-fixed-deposit-sgd", "market_value": 650_000, "cost_value": 650_000},
    )
    replace_by_id(
        datasets["opportunities"],
        "opportunity_id",
        "opportunity-01",
        {
            "opportunity_id": "opp-fd-maturity",
            "opportunity_type": "MATURITY_CONVERSATION",
            "title": "Prepare Daniel's maturity and portfolio review",
            "priority": "NOW",
            "estimated_value": 860_000,
            "confidence_score": 94,
        },
    )
    replace_by_id(
        datasets["rm_actions"],
        "rm_action_id",
        "action-01",
        {"opportunity_id": "opp-fd-maturity", "action_type": "PREPARE_MATURITY_REVIEW"},
    )
    replace_by_id(
        datasets["customer_events"],
        "event_id",
        "event-01",
        {
            "event_type": "FIXED_DEPOSIT_MATURITY",
            "event_value": 650_000,
            "event_at": "2026-08-12T08:24:00+08:00",
            "maturity_date": "2026-08-24",
        },
    )
    datasets["customer_events"].append(
        {
            "event_id": "event-daniel-idle-cash",
            "customer_id": "client-lim",
            "account_id": "account-01-operating",
            "event_type": "SUSTAINED_IDLE_CASH",
            "event_value": 210_000,
            "currency": "SGD",
            "event_at": "2026-08-12T08:20:00+08:00",
            "source": "synthetic-scenario-engine",
            "observation_days": 90,
        }
    )

    replace_by_id(
        datasets["opportunities"],
        "opportunity_id",
        "opportunity-02",
        {
            "opportunity_id": "opp-kyc-risk",
            "opportunity_type": "COMPLIANCE_REVIEW",
            "title": "Combine Mei's portfolio review with KYC refresh",
            "priority": "TODAY",
            "estimated_value": 2_300_000,
            "confidence_score": 88,
        },
    )
    replace_by_id(datasets["rm_actions"], "rm_action_id", "action-02", {"opportunity_id": "opp-kyc-risk", "action_type": "COMPLETE_KYC_REFRESH"})
    replace_by_id(
        datasets["customer_events"],
        "event_id",
        "event-02",
        {"event_type": "BENEFICIARY_CHANGE", "event_value": 0, "event_at": "2026-08-12T08:12:00+08:00"},
    )

    replace_by_id(
        datasets["opportunities"],
        "opportunity_id",
        "opportunity-03",
        {
            "opportunity_id": "opp-mortgage",
            "opportunity_type": "MORTGAGE_REPRICING",
            "title": "Contact Jonathan before his repricing window",
            "priority": "THIS_WEEK",
            "estimated_value": 1_100_000,
            "confidence_score": 82,
        },
    )
    replace_by_id(datasets["rm_actions"], "rm_action_id", "action-03", {"opportunity_id": "opp-mortgage", "action_type": "PREPARE_MORTGAGE_REVIEW"})
    replace_by_id(
        datasets["customer_events"],
        "event_id",
        "event-03",
        {
            "event_type": "MORTGAGE_REPRICING_WINDOW",
            "event_value": 1_100_000,
            "event_at": "2026-08-12T07:58:00+08:00",
            "window_opens_date": "2026-09-11",
        },
    )
    replace_by_id(
        datasets["interactions"],
        "interaction_id",
        "interaction-03",
        {"summary": "Completed a digital service request; no portfolio conversation in eight months."},
    )

    replace_by_id(
        datasets["opportunities"],
        "opportunity_id",
        "opportunity-04",
        {
            "opportunity_id": "opp-cross-border",
            "opportunity_type": "CROSS_BORDER_LIQUIDITY",
            "title": "Prepare Priya's cross-border liquidity conversation",
            "priority": "THIS_WEEK",
            "estimated_value": 540_000,
            "confidence_score": 76,
        },
    )
    replace_by_id(datasets["rm_actions"], "rm_action_id", "action-04", {"opportunity_id": "opp-cross-border", "action_type": "PREPARE_LIQUIDITY_REVIEW"})
    replace_by_id(
        datasets["customer_events"],
        "event_id",
        "event-04",
        {
            "event_type": "CROSS_BORDER_TRANSFER_INCREASE",
            "event_value": 540_000,
            "event_at": "2026-08-12T07:42:00+08:00",
        },
    )


def add_market_snapshots(datasets: dict[str, list[dict]]) -> None:
    for index, product_id in enumerate(
        ("product-fixed-deposit-sgd", "product-investment-sgd", "product-unit-trust-sgd"),
        start=1,
    ):
        datasets["market_snapshots"].append(
            {
                "market_snapshot_id": f"market-snapshot-{index:02d}",
                "product_id": product_id,
                "market_name": "Synthetic Singapore Market Reference",
                "reference_value": round(100 + index * 1.75, 2),
                "currency": "SGD",
                "captured_at": GENERATED_AT,
                "synthetic": True,
            }
        )


RISK_LABELS = {
    1: "Capital Preservation",
    2: "Cautious",
    3: "Balanced",
    4: "Growth",
    5: "Aggressive",
}


def add_advisory_and_governance_data(
    datasets: dict[str, list[dict]],
    clients: list[dict],
    rng: random.Random,
) -> None:
    stable_profiles = {
        "client-lim": {
            "employment_status": "EMPLOYED",
            "retirement_status": "NOT_RETIRED",
            "declared_risk_score": 3,
            "observed_behaviour_indicator": 2,
            "previous_behaviour_indicator": 3,
            "risk_review_status": "REVIEW_SUGGESTED",
            "profile_effective_at": "2026-05-18T12:15:00+08:00",
            "profile_review_due_at": "2027-05-18T12:15:00+08:00",
            "liquidity_horizon_months": 12,
            "income_complete": True,
            "commitments_complete": False,
            "knowledge_experience_status": "CURRENT",
            "cka_status": "NOT_APPLICABLE",
            "car_status": "NOT_APPLICABLE",
            "selected_client_status": "NOT_ASSESSED",
        },
        "client-tan": {
            "employment_status": "RETIRED",
            "retirement_status": "RETIRED",
            "declared_risk_score": 2,
            "observed_behaviour_indicator": 2,
            "previous_behaviour_indicator": 2,
            "risk_review_status": "REVIEW_REQUIRED",
            "profile_effective_at": "2025-09-02T10:00:00+08:00",
            "profile_review_due_at": "2026-09-02T10:00:00+08:00",
            "liquidity_horizon_months": 24,
            "income_complete": False,
            "commitments_complete": False,
            "knowledge_experience_status": "INCOMPLETE",
            "cka_status": "REQUIRED",
            "car_status": "REQUIRED",
            "selected_client_status": "NOT_ASSESSED",
        },
        "client-ng": {
            "employment_status": "EMPLOYED",
            "retirement_status": "NOT_RETIRED",
            "declared_risk_score": 1,
            "observed_behaviour_indicator": 1,
            "previous_behaviour_indicator": 1,
            "risk_review_status": "CURRENT",
            "profile_effective_at": "2026-02-20T10:00:00+08:00",
            "profile_review_due_at": "2027-02-20T10:00:00+08:00",
            "liquidity_horizon_months": 12,
            "income_complete": True,
            "commitments_complete": True,
            "knowledge_experience_status": "CURRENT",
            "cka_status": "NOT_APPLICABLE",
            "car_status": "NOT_APPLICABLE",
            "selected_client_status": "NOT_ASSESSED",
        },
        "client-lee": {
            "employment_status": "SELF_EMPLOYED",
            "retirement_status": "NOT_RETIRED",
            "declared_risk_score": 4,
            "observed_behaviour_indicator": 4,
            "previous_behaviour_indicator": 3,
            "risk_review_status": "CURRENT",
            "profile_effective_at": "2026-07-16T10:00:00+08:00",
            "profile_review_due_at": "2027-07-16T10:00:00+08:00",
            "liquidity_horizon_months": 9,
            "income_complete": True,
            "commitments_complete": True,
            "knowledge_experience_status": "CURRENT",
            "cka_status": "CURRENT",
            "car_status": "CURRENT",
            "selected_client_status": "NOT_ASSESSED",
        },
    }
    stable_activity = {
        "client-lim": ("SELL", "EQUITY", 320_000, "2026-08-09T14:20:00+08:00", "Material equity sale increased liquidity."),
        "client-tan": ("SELL", "EQUITY", 85_000, "2026-07-25T11:05:00+08:00", "Equity reduction is consistent with cautious positioning."),
        "client-ng": ("BUY", "FIXED_INCOME", 60_000, "2026-06-18T09:45:00+08:00", "High-quality bond purchase aligned with capital preservation."),
        "client-lee": ("BUY", "MULTI_ASSET", 140_000, "2026-08-05T15:10:00+08:00", "Diversified investment purchase increased observed risk activity."),
    }

    for position, client in enumerate(clients, start=1):
        customer_id = client["customer_id"]
        declared_score = rng.randint(1, 5)
        profile = stable_profiles.get(
            customer_id,
            {
                "employment_status": rng.choice(("EMPLOYED", "SELF_EMPLOYED", "RETIRED")),
                "retirement_status": "NOT_RETIRED",
                "declared_risk_score": declared_score,
                "observed_behaviour_indicator": declared_score,
                "previous_behaviour_indicator": declared_score,
                "risk_review_status": "CURRENT",
                "profile_effective_at": timestamp(2 + position % 8, 10, position % 60),
                "profile_review_due_at": f"2027-08-{10 + position % 17:02d}T10:00:00+08:00",
                "liquidity_horizon_months": rng.choice((6, 12, 24, 36)),
                "income_complete": True,
                "commitments_complete": True,
                "knowledge_experience_status": "CURRENT",
                "cka_status": "NOT_APPLICABLE",
                "car_status": "NOT_APPLICABLE",
                "selected_client_status": "NOT_ASSESSED",
            },
        )
        if profile["employment_status"] == "RETIRED" and customer_id not in stable_profiles:
            profile["retirement_status"] = "RETIRED"
        declared = profile["declared_risk_score"]
        observed = profile["observed_behaviour_indicator"]
        activity = stable_activity.get(
            customer_id,
            (
                rng.choice(("BUY", "SELL")),
                rng.choice(("FIXED_INCOME", "EQUITY", "MULTI_ASSET")),
                rng.randrange(20_000, 150_001, 5_000),
                timestamp(5 + position % 5, 13, position % 60),
                "Synthetic investment activity contributed to the observed behaviour indicator.",
            ),
        )
        activity_id = f"investment-activity-{position:02d}"
        datasets["client_advisory_profiles"].append(
            {
                "advisory_profile_id": f"advisory-{customer_id}",
                "customer_id": customer_id,
                **profile,
                "declared_risk_label": RISK_LABELS[declared],
                "observed_behaviour_label": RISK_LABELS[observed],
                "indicator_calculated_at": GENERATED_AT,
                "calculation_version": "frontier-behaviour-v1",
            }
        )
        datasets["risk_profile_history"].append(
            {
                "risk_history_id": f"risk-history-{position:02d}",
                "customer_id": customer_id,
                "declared_risk_score": declared,
                "declared_risk_label": RISK_LABELS[declared],
                "effective_at": profile["profile_effective_at"],
                "reviewed_by": "rm-john-doe",
                "reason": "Client-declared and adviser-confirmed investment risk profile.",
                "evidence_id": f"advisory-{customer_id}",
            }
        )
        datasets["client_investment_activity"].append(
            {
                "investment_activity_id": activity_id,
                "customer_id": customer_id,
                "account_id": f"account-{position:02d}-portfolio",
                "activity_type": activity[0],
                "asset_class": activity[1],
                "product_id": "product-investment-sgd",
                "amount": activity[2],
                "quantity": 1,
                "currency": "SGD",
                "activity_at": activity[3],
                "source": "synthetic-investment-ledger",
                "explanation": activity[4],
            }
        )
        datasets["observed_behaviour_history"].append(
            {
                "behaviour_history_id": f"behaviour-history-{position:02d}",
                "customer_id": customer_id,
                "previous_indicator": profile["previous_behaviour_indicator"],
                "observed_indicator": observed,
                "observed_label": RISK_LABELS[observed],
                "calculated_at": GENERATED_AT,
                "trigger_activity_id": activity_id,
                "calculation_version": "frontier-behaviour-v1",
                "risk_review_status": profile["risk_review_status"],
                "declared_profile_changed": False,
            }
        )

    houseviews = json.loads(HOUSEVIEW_SOURCE.read_text(encoding="utf-8"))
    for report in houseviews["reports"]:
        datasets["cio_houseview_reports"].append(
            {
                "houseview_id": report["id"],
                "title": report["title"],
                "as_of_date": report["asOf"],
                "status": report["status"].upper(),
                "cio_stance": report["cioStance"],
                "executive_summary": report["executiveSummary"],
                "document_path": f"Files/houseview/{report['id']}.pdf",
                "synthetic": True,
            }
        )
        for sequence, section in enumerate(report["sections"], start=1):
            datasets["cio_houseview_sections"].append(
                {
                    "houseview_section_id": section["id"],
                    "houseview_id": report["id"],
                    "sequence": sequence,
                    "title": section["title"],
                    "view": section["view"],
                    "positioning": section["positioning"],
                    "risks": " | ".join(section["risks"]),
                }
            )

    control_pack = json.loads(REGULATORY_SOURCE.read_text(encoding="utf-8"))
    document = control_pack["document"]
    datasets["regulatory_documents"].append(
        {
            "regulatory_document_id": document["id"],
            "title": document["title"],
            "source_title": document["sourceTitle"],
            "source_authority": document["sourceAuthority"],
            "source_issue_date": document["sourceIssueDate"],
            "source_last_updated": document["sourceLastUpdated"],
            "status": document["status"].upper().replace("-", "_"),
            "document_path": "Files/regulatory/frontier_faa_n16_demo_control_pack.pdf",
            "disclaimer": document["disclaimer"],
        }
    )
    for rule in control_pack["rules"]:
        datasets["regulatory_rules"].append(
            {
                "regulatory_rule_id": rule["id"],
                "regulatory_document_id": document["id"],
                "paragraph": rule["paragraph"],
                "title": rule["title"],
                "summary": rule["summary"],
                "applies_to": " | ".join(rule["appliesTo"]),
                "gate": rule["gate"],
            }
        )


def write_datasets(output_dir: Path, seed: int) -> dict:
    datasets = build_datasets(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    for child in output_dir.iterdir():
        if child.is_file() and (child.suffix == ".jsonl" or child.name == "manifest.json"):
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)

    row_counts = {}
    for name in DATASET_NAMES:
        rows = datasets[name]
        row_counts[name] = len(rows)
        path = output_dir / f"{name}.jsonl"
        content = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
        path.write_text(content, encoding="ascii", newline="\n")

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "seed": seed,
        "generatedAt": GENERATED_AT,
        "synthetic": True,
        "declaration": "Entirely fictional synthetic data for internal demonstration use only.",
        "rowCounts": row_counts,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
        newline="\n",
    )
    return manifest


def check_datasets(output_dir: Path, seed: int) -> None:
    expected_files = [f"{name}.jsonl" for name in DATASET_NAMES] + ["manifest.json"]
    with tempfile.TemporaryDirectory() as temporary:
        generated_dir = Path(temporary)
        write_datasets(generated_dir, seed)
        for filename in expected_files:
            checked_in = output_dir / filename
            if not checked_in.is_file() or checked_in.read_bytes() != (generated_dir / filename).read_bytes():
                raise SystemExit(f"Generated Fabric data is stale: {filename}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic Frontier RM Fabric datasets.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Verify checked-in outputs without rewriting them.")
    args = parser.parse_args()
    if args.check:
        check_datasets(args.output_dir.resolve(), args.seed)
        print(f"Fabric data is current in {args.output_dir.resolve()}")
        return
    manifest = write_datasets(args.output_dir.resolve(), args.seed)
    print(f"Generated {sum(manifest['rowCounts'].values())} rows in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()