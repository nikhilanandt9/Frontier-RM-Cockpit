from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

try:
    from deploy_frontier_semantic_model import POWER_BI_API, POWER_BI_RESOURCE, access_token, call
except ModuleNotFoundError:
    from scripts.deploy_frontier_semantic_model import POWER_BI_API, POWER_BI_RESOURCE, access_token, call


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "packages" / "demo-data" / "agent-runs"
MANIFEST_PATH = ROOT / "packages" / "fabric-data" / "generated" / "manifest.json"
DEFAULT_ENDPOINT = "https://ai-frontier-rm-kqo7o4bg.services.ai.azure.com/api/projects/frontier-rm-agents"
DATA_AGENT_ARTIFACT_ID = "ffb990f5-ea48-43fb-82b4-bc9c91a056c1"
WORKSPACE_ID = "67764587-fefa-43e9-ad2e-66b47e7ea18d"
SEMANTIC_MODEL_ID = "bc44b3b5-5275-4810-93a7-251f76cc9235"
AGENT_NAMES = {
    "orchestrator": "frontier-rm-orchestrator",
    "customer-intelligence": "frontier-customer-intelligence",
    "market-context": "frontier-market-context",
    "meeting-preparation": "frontier-meeting-preparation",
}
SENSITIVE_PATTERN = re.compile(
    r"bearer\s+[a-z0-9._-]+|authorization\s*:|access[_ -]?token|client[_ -]?secret|"
    r"chain[- ]of[- ]thought|hidden reasoning|private reasoning",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sanitize_text(value: str, max_length: int = 2_000) -> str:
    text = " ".join(str(value).split())
    if SENSITIVE_PATTERN.search(text):
        raise ValueError("Captured output contains sensitive or private-reasoning content")
    return text[:max_length]


def response_evidence(agent_id: str, response_id: str) -> str:
    safe_response_id = re.sub(r"[^a-zA-Z0-9_-]", "", response_id)
    if not safe_response_id:
        raise ValueError("A valid Foundry response ID is required")
    return f"foundry:{agent_id}:{safe_response_id}"


def invoke_agent(openai, agent_name: str, prompt: str, require_tool: bool = False):
    options = {
        "input": prompt,
        "extra_body": {"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    }
    if require_tool:
        options["tool_choice"] = "required"
    response = openai.responses.create(**options)
    if response.status != "completed" or not response.output_text.strip():
        raise RuntimeError(f"Agent {agent_name} did not return a completed response")
    return response


def query_semantic_evidence() -> tuple[dict, str]:
    query = """EVALUATE
ROW(
    "CustomerName", CALCULATE(SELECTEDVALUE('Meeting Context'[Customer Name]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "OpportunityID", CALCULATE(SELECTEDVALUE('Meeting Context'[Opportunity ID]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "EventID", CALCULATE(SELECTEDVALUE('Meeting Context'[Event ID]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "OpportunityTitle", CALCULATE(SELECTEDVALUE('Meeting Context'[Opportunity Title]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "EventTypes", CALCULATE(SELECTEDVALUE('Meeting Context'[Event Types]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "ConsentStatus", CALCULATE(SELECTEDVALUE('Meeting Context'[Consent Status]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "KYCStatus", CALCULATE(SELECTEDVALUE('Meeting Context'[KYC Status]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "RelationshipManagerID", CALCULATE(SELECTEDVALUE('Meeting Context'[Relationship Manager ID]), 'Meeting Context'[Customer Name] = "Daniel Lim"),
    "DanielAssets", CALCULATE(Customer[Assets Under Care], Customer[Customer Name] = "Daniel Lim"),
    "DanielOpportunityValue", CALCULATE(Opportunities[Opportunity Pipeline], Customer[Customer Name] = "Daniel Lim"),
    "CustomerCount", Customer[# Customers],
    "OpportunityPipeline", Opportunities[Opportunity Pipeline],
    "ComplianceReviews", 'Compliance Due'[# Compliance Reviews],
    "PortfolioValue", 'Portfolio Exposure'[Portfolio Market Value],
    "MaturingValue", 'Maturity Watchlist'[Maturing Value]
)"""
    token = access_token(POWER_BI_RESOURCE)
    _, headers, result = call(
        "POST",
        f"{POWER_BI_API}/groups/{WORKSPACE_ID}/datasets/{SEMANTIC_MODEL_ID}/executeQueries",
        token,
        {"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}},
    )
    query_result = result.get("results", [{}])[0]
    if query_result.get("error"):
        raise RuntimeError(f"Semantic evidence query failed: {json.dumps(query_result['error'])}")
    rows = query_result.get("tables", [{}])[0].get("rows", [])
    if len(rows) != 1:
        raise RuntimeError(f"Semantic evidence query returned {len(rows)} rows")
    evidence = {key.rsplit("[", 1)[-1].rstrip("]"): value for key, value in rows[0].items()}
    required = {
        "CustomerName",
        "OpportunityID",
        "EventID",
        "ConsentStatus",
        "KYCStatus",
        "DanielAssets",
        "DanielOpportunityValue",
    }
    if required - evidence.keys() or any(evidence.get(key) in {None, ""} for key in required):
        raise RuntimeError("Semantic evidence is missing required Daniel fields")
    request_id = headers.get("x-ms-request-id") or headers.get("request-id") or "execute-query"
    return evidence, request_id


def validate_bundle(bundle: dict, expected_verification: str) -> None:
    if bundle.get("schemaVersion") != "1.0":
        raise ValueError("Unsupported run schema version")
    if bundle["run"]["mode"] != "captured-live":
        raise ValueError("Captured runs must use captured-live mode")
    if len(bundle["agents"]) != 4:
        raise ValueError("Captured runs require four agents")
    sequences = [event["sequence"] for event in bundle["events"]]
    if sequences != list(range(1, len(sequences) + 1)):
        raise ValueError("Run event sequence is not contiguous")
    evidence = {
        evidence_id
        for event in bundle["events"]
        for evidence_id in event.get("evidenceIds", [])
    }
    if bundle["outcome"]["evidenceCount"] != len(evidence):
        raise ValueError("Outcome evidence count differs from retained evidence")
    if bundle["outcome"]["verificationStatus"] != expected_verification:
        raise ValueError("Verifier outcome does not match the requested capture path")
    serialized = json.dumps(bundle)
    if SENSITIVE_PATTERN.search(serialized):
        raise ValueError("Run bundle contains prohibited sensitive content")


def capture(endpoint: str, revision: bool) -> dict:
    started_at = utc_now()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="ascii"))
    semantic_evidence, semantic_request_id = query_semantic_evidence()
    with AzureCliCredential() as credential, AIProjectClient(
        endpoint=endpoint,
        credential=credential,
        allow_preview=True,
    ) as project, project.get_openai_client() as openai:
        customer = invoke_agent(
            openai,
            AGENT_NAMES["customer-intelligence"],
            (
                "Use the Microsoft Fabric tool and only Frontier RM Semantic Model. Return a concise "
                "categorical profile for Daniel Lim with customer name, household, risk profile, contact "
                "preference, consent, KYC and suitability state, opportunity title and priority, and event "
                "types. Do not return monetary values or technical identifiers. Do not include other "
                "customers. State missing visible fields explicitly and do not provide recommendations."
            ),
            require_tool=True,
        )
        customer_text = sanitize_text(customer.output_text)
        semantic_text = sanitize_text(json.dumps(semantic_evidence, sort_keys=True))
        downstream_customer_text = f"Data Agent context: {customer_text} Validated DAX evidence: {semantic_text}"
        if revision:
            revision_evidence = {key: value for key, value in semantic_evidence.items() if key != "ConsentStatus"}
            downstream_customer_text = (
                "Data Agent retrieval completed, but its natural-language response is withheld from "
                "downstream agents for this controlled verifier test. Validated DAX evidence excluding "
                f"consent: {sanitize_text(json.dumps(revision_evidence, sort_keys=True))}. Consent evidence "
                "is intentionally withheld and must be treated as unresolved."
            )

        market = invoke_agent(
            openai,
            AGENT_NAMES["market-context"],
            (
                "Using only the supplied governed facts, state conversation boundaries relevant to a "
                "fixed-deposit maturity and idle-cash discussion. Do not invent evidence IDs, rates, "
                f"forecasts, or market conditions. Governed facts: {downstream_customer_text}"
            ),
        )
        market_text = sanitize_text(market.output_text)

        meeting = invoke_agent(
            openai,
            AGENT_NAMES["meeting-preparation"],
            (
                "Prepare a concise human-reviewed meeting brief using only these supplied outputs. If "
                "required evidence is missing, list the missing evidence instead of claiming readiness. "
                f"Customer Intelligence: {downstream_customer_text} Market Context: {market_text}"
            ),
        )
        meeting_text = sanitize_text(meeting.output_text)

        verifier = invoke_agent(
            openai,
            AGENT_NAMES["orchestrator"],
            (
                "Verify whether this meeting brief is grounded and ready for John Doe's review. Return "
                "a first line containing exactly VERIFIED or REVISION-REQUESTED, followed by a concise "
                "public explanation. Require customer facts, event/opportunity linkage, consent, "
                "compliance, and no unsupported market claims. If the supplied evidence explicitly says "
                "that consent is withheld, missing, or unresolved, you MUST return REVISION-REQUESTED as "
                "the first line even if every other evidence category is present. "
                f"Customer Intelligence: {downstream_customer_text} Market Context: {market_text} "
                f"Meeting Preparation: {meeting_text}"
            ),
        )
        verifier_text = sanitize_text(verifier.output_text)

    expected_verification = "revision-requested" if revision else "verified"
    observed_verification = (
        "revision-requested" if verifier_text.upper().startswith("REVISION-REQUESTED") else "verified"
    )
    response_ids = {
        "customer-intelligence": customer.id,
        "market-context": market.id,
        "meeting-preparation": meeting.id,
        "orchestrator": verifier.id,
    }
    evidence_ids = {
        agent_id: response_evidence(agent_id, response_id)
        for agent_id, response_id in response_ids.items()
    }
    semantic_evidence_id = response_evidence("semantic-model", semantic_request_id)
    completed_at = utc_now()
    suffix = "revision" if revision else "success"
    run_id = f"run-daniel-lim-live-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{suffix}"
    event_specs = [
        ("Run.Status", "orchestrator", "Controlled meeting-preparation capture started.", None),
        ("Agent.Plan", "orchestrator", "Planned governed retrieval, context, preparation, and verification.", None),
        ("Agent.Delegation", "orchestrator", "Delegated governed customer retrieval to Customer Intelligence.", None),
        ("Agent.ToolCall", "customer-intelligence", "Invoked the published Microsoft Fabric Data Agent.", [f"fabric-data-agent:{DATA_AGENT_ARTIFACT_ID}"]),
        ("Agent.Evidence", "customer-intelligence", "Retrieved Daniel Lim visible relationship, event, opportunity, consent, and compliance context.", [evidence_ids["customer-intelligence"]]),
        ("Agent.Evidence", "customer-intelligence", "Validated hidden identifiers, causal event linkage, and monetary values with direct DAX.", [semantic_evidence_id]),
        ("Agent.Delegation", "orchestrator", "Delegated bounded context framing to Market Context.", None),
        ("Agent.Output", "market-context", "Produced conversation boundaries without forecasts or guarantees.", [evidence_ids["market-context"]]),
        ("Agent.Delegation", "orchestrator", "Delegated supplied evidence to Meeting Preparation.", None),
        ("Agent.Output", "meeting-preparation", "Produced a human-review meeting brief or missing-evidence response.", [evidence_ids["meeting-preparation"]]),
        ("Agent.Status", "orchestrator", "Verified evidence coverage and mandatory safeguards.", [evidence_ids["orchestrator"]]),
        ("Run.Status", "orchestrator", f"Capture completed with status {observed_verification}.", None),
    ]
    events = [
        {
            "sequence": index,
            "timestamp": completed_at,
            "type": event_type,
            "agentId": agent_id,
            "summary": summary,
            **({"evidenceIds": ids} if ids else {}),
        }
        for index, (event_type, agent_id, summary, ids) in enumerate(event_specs, start=1)
    ]
    unique_evidence = {
        evidence_id
        for event in events
        for evidence_id in event.get("evidenceIds", [])
    }
    bundle = {
        "schemaVersion": "1.0",
        "run": {
            "id": run_id,
            "clientId": "client-lim",
            "clientName": "Daniel Lim",
            "status": "revision-requested" if revision else "completed",
            "mode": "captured-live",
            "startedAt": started_at,
            "completedAt": completed_at,
            "dataSnapshotAt": manifest["generatedAt"],
            "provider": "microsoft-foundry+fabric-data-agent",
            "traceId": verifier.id,
        },
        "agents": [
            {"id": agent_id, "name": name, "role": role, "status": "completed"}
            for agent_id, name, role in (
                ("orchestrator", "RM Orchestrator", "Plans, delegates and verifies"),
                ("customer-intelligence", "Customer Intelligence", "Retrieves governed relationship context"),
                ("market-context", "Market Context", "Frames relevant market considerations"),
                ("meeting-preparation", "Meeting Preparation", "Builds the human-reviewed brief"),
            )
        ],
        "events": events,
        "outcome": {
            "verificationStatus": observed_verification,
            "evidenceCount": len(unique_evidence),
            "meetingBrief": meeting_text,
            "unresolvedQuestions": (
                ["Consent evidence was intentionally withheld for verifier validation."] if revision else []
            ),
            "recommendedActions": [
                "Review the captured brief and retained evidence before client communication.",
                "Resolve every listed evidence gap before personalised discussion.",
            ],
        },
    }
    validate_bundle(bundle, expected_verification)
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a controlled Fabric-grounded Foundry agent run")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--revision", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Write the validated bundle to agent-runs.")
    args = parser.parse_args()

    if not args.apply:
        print(json.dumps({"endpoint": args.endpoint, "mode": "revision" if args.revision else "success", "writes": False}, indent=2))
        return
    bundle = capture(args.endpoint, args.revision)
    output_path = RUNS_ROOT / f"{bundle['run']['id']}.json"
    output_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runId": bundle["run"]["id"], "path": str(output_path), "verificationStatus": bundle["outcome"]["verificationStatus"]}))


if __name__ == "__main__":
    main()