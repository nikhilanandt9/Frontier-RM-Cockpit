from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path


FABRIC_DATASETS = (
    "customers",
    "households",
    "accounts",
    "products",
    "interactions",
    "compliance_profiles",
    "opportunities",
    "customer_events",
    "client_advisory_profiles",
    "risk_profile_history",
    "client_investment_activity",
    "observed_behaviour_history",
    "cio_houseview_reports",
    "cio_houseview_sections",
    "regulatory_documents",
    "regulatory_rules",
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="ascii").splitlines() if line]


def format_sgd(value: int | float) -> str:
    if value >= 1_000_000:
        return f"S${value / 1_000_000:.2f}M".replace(".00M", "M").replace("0M", "M")
    if value >= 1_000:
        return f"S${value / 1_000:.0f}K"
    return f"S${value:,.0f}"


def title_case_code(value: str) -> str:
    return value.replace("_", " ").title()


def initials(name: str) -> str:
    return "".join(part[0] for part in name.split()[:2]).upper()


def kyc_label(profile: dict) -> str:
    due = date.fromisoformat(profile["kyc_due_date"])
    if profile["kyc_status"] == "CURRENT":
        return f"Current to {due.strftime('%b %Y')}"
    return f"Refresh due {due.strftime('%d %b %Y')}"


def event_signal(event: dict) -> str:
    event_type = event["event_type"]
    value = format_sgd(event.get("event_value", 0))
    if event_type == "FIXED_DEPOSIT_MATURITY":
        return f"{value} fixed deposit matures on {event['maturity_date']}"
    if event_type == "SUSTAINED_IDLE_CASH":
        return f"{value} idle cash observed for {event['observation_days']} days"
    if event_type == "MORTGAGE_REPRICING_WINDOW":
        return f"Mortgage repricing window opens on {event['window_opens_date']}"
    if event_type == "CROSS_BORDER_TRANSFER_INCREASE":
        return f"Cross-border transfer activity increased to {value}"
    if event_type == "BENEFICIARY_CHANGE":
        return "Recent beneficiary change requires review"
    return f"Balance change of {value} crossed the review threshold"


def generic_opportunity(record: dict, client: dict, signals: list[str]) -> dict:
    opportunity_type = title_case_code(record["opportunity_type"])
    channel = client["contactPreference"].split(",")[0]
    return {
        "id": record["opportunity_id"],
        "clientId": record["customer_id"],
        "type": opportunity_type,
        "priority": title_case_code(record["priority"]),
        "title": record["title"],
        "summary": (
            f"Review {client['name']}'s latest relationship signal, current profile and "
            "account context before the next needs-led conversation."
        ),
        "confidence": record["confidence_score"],
        "value": f"{format_sgd(record['estimated_value'])} conversation scope",
        "channel": channel,
        "time": "This week",
        "evidence": signals[:3],
        "checks": [
            "Confirm the client's current objective and liquidity needs",
            "Reconfirm profile and consent before personalised discussion",
            "Use only current approved product and service information",
        ],
        "opening": (
            f"{client['name'].split()[0]}, I have brought together the recent changes "
            "across your relationship so we can review what needs attention next."
        ),
    }


def build_fabric_dashboard(base: dict, fabric_dir: Path) -> dict:
    manifest = json.loads((fabric_dir / "manifest.json").read_text(encoding="ascii"))
    tables = {name: load_jsonl(fabric_dir / f"{name}.jsonl") for name in FABRIC_DATASETS}
    if manifest["rowCounts"]["customers"] != len(tables["customers"]):
        raise ValueError("Fabric customer snapshot does not match its manifest")

    stable_clients = {client["id"]: client for client in base["clients"]}
    stable_opportunities = {item["clientId"]: item for item in base["opportunities"]}
    households = {row["household_id"]: row for row in tables["households"]}
    profiles = {row["customer_id"]: row for row in tables["compliance_profiles"]}
    interactions = {row["customer_id"]: row for row in tables["interactions"]}
    products = {row["product_id"]: row["product_name"] for row in tables["products"]}
    account_products: dict[str, list[str]] = defaultdict(list)
    for account in tables["accounts"]:
        name = products[account["product_id"]]
        if name not in account_products[account["customer_id"]]:
            account_products[account["customer_id"]].append(name)
    events: dict[str, list[dict]] = defaultdict(list)
    for event in tables["customer_events"]:
        events[event["customer_id"]].append(event)
    advisory_profiles = {row["customer_id"]: row for row in tables["client_advisory_profiles"]}
    risk_history: dict[str, list[dict]] = defaultdict(list)
    for row in tables["risk_profile_history"]:
        risk_history[row["customer_id"]].append(row)
    investment_activity: dict[str, list[dict]] = defaultdict(list)
    for row in tables["client_investment_activity"]:
        investment_activity[row["customer_id"]].append(row)
    behaviour_history: dict[str, list[dict]] = defaultdict(list)
    for row in tables["observed_behaviour_history"]:
        behaviour_history[row["customer_id"]].append(row)

    clients = []
    for row in tables["customers"]:
        customer_id = row["customer_id"]
        if customer_id in stable_clients:
            clients.append(
                {
                    **stable_clients[customer_id],
                    "advisoryProfile": advisory_profiles[customer_id],
                    "riskHistory": sorted(risk_history[customer_id], key=lambda item: item["effective_at"], reverse=True),
                    "investmentActivity": sorted(investment_activity[customer_id], key=lambda item: item["activity_at"], reverse=True),
                    "behaviourHistory": sorted(behaviour_history[customer_id], key=lambda item: item["calculated_at"], reverse=True),
                }
            )
            continue
        profile = profiles[customer_id]
        event_signals = [event_signal(event) for event in events[customer_id]]
        profile_signal = (
            f"KYC refresh due {profile['kyc_due_date']}"
            if profile["kyc_status"] != "CURRENT"
            else f"Profile current to {profile['kyc_due_date']}"
        )
        clients.append(
            {
                "id": customer_id,
                "name": row["full_name"],
                "initials": initials(row["full_name"]),
                "segment": row["segment"],
                "household": households[row["household_id"]]["household_name"],
                "assets": format_sgd(row["relationship_value"]),
                "riskProfile": row["risk_profile"],
                "kycStatus": kyc_label(profile),
                "contactPreference": row["contact_preference"],
                "consent": row["consent_status"],
                "nextMeeting": "No meeting booked",
                "products": account_products[customer_id],
                "signals": [*event_signals, profile_signal, "Relationship review opportunity is open"][:3],
                "recentInteraction": interactions[customer_id]["summary"],
                "advisoryProfile": advisory_profiles[customer_id],
                "riskHistory": sorted(risk_history[customer_id], key=lambda item: item["effective_at"], reverse=True),
                "investmentActivity": sorted(investment_activity[customer_id], key=lambda item: item["activity_at"], reverse=True),
                "behaviourHistory": sorted(behaviour_history[customer_id], key=lambda item: item["calculated_at"], reverse=True),
            }
        )

    client_by_id = {client["id"]: client for client in clients}
    opportunities = []
    for record in tables["opportunities"]:
        customer_id = record["customer_id"]
        if customer_id in stable_opportunities:
            opportunities.append(stable_opportunities[customer_id])
        else:
            opportunities.append(generic_opportunity(record, client_by_id[customer_id], client_by_id[customer_id]["signals"]))

    return {
        **base,
        "clients": clients,
        "opportunities": opportunities,
        "houseviews": [
            {
                **report,
                "sections": sorted(
                    [section for section in tables["cio_houseview_sections"] if section["houseview_id"] == report["houseview_id"]],
                    key=lambda item: item["sequence"],
                ),
            }
            for report in sorted(tables["cio_houseview_reports"], key=lambda item: item["as_of_date"], reverse=True)
        ],
        "regulatoryDocuments": tables["regulatory_documents"],
        "regulatoryRules": tables["regulatory_rules"],
        "dataSource": {
            "kind": "fabric-snapshot",
            "workspace": "<FABRIC_WORKSPACE_NAME>",
            "lakehouse": "<FABRIC_LAKEHOUSE_NAME>",
            "snapshotAt": manifest["generatedAt"],
            "schemaVersion": manifest["schemaVersion"],
            "customerCount": len(clients),
            "synthetic": manifest["synthetic"],
        },
    }
