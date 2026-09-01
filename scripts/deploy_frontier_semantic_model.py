from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib import error, request

from topology_config import render_bytes, require_local_environment


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = ROOT / "fabric" / "semantic-model" / "FrontierRM.SemanticModel"
GENERATED = ROOT / "packages" / "fabric-data" / "generated"
MODEL_NAME = "Frontier RM Semantic Model"
FABRIC_RESOURCE = "https://api.fabric.microsoft.com"
POWER_BI_RESOURCE = "https://analysis.windows.net/powerbi/api"
FABRIC_API = "https://api.fabric.microsoft.com/v1"
POWER_BI_API = "https://api.powerbi.com/v1.0/myorg"
SKILL_HEADER = "semantic-model-authoring"


def azure_cli() -> str:
    configured = os.environ.get("AZURE_CLI_PATH")
    if configured:
        return configured
    discovered = shutil.which("az") or shutil.which("az.cmd")
    if discovered:
        return discovered
    standard_windows_path = Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd")
    if standard_windows_path.is_file():
        return str(standard_windows_path)
    raise FileNotFoundError("Azure CLI was not found; set AZURE_CLI_PATH to az or az.cmd")


def access_token(resource: str) -> str:
    result = subprocess.run(
        [azure_cli(), "account", "get-access-token", "--resource", resource, "--query", "accessToken", "--output", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def call(
    method: str,
    url: str,
    token: str,
    body: dict | None = None,
    skill_header: str = SKILL_HEADER,
) -> tuple[int, dict, dict]:
    encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if url.startswith(FABRIC_API):
        headers["x-ms-fabric-skill"] = skill_header
    if encoded is not None:
        headers["Content-Type"] = "application/json"
    http_request = request.Request(url, data=encoded, headers=headers, method=method)
    try:
        with request.urlopen(http_request, timeout=60) as response:
            content = response.read().decode("utf-8")
            return response.status, dict(response.headers), json.loads(content) if content else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc


def definition_parts(model_dir: Path) -> list[dict]:
    paths = [model_dir / "definition.pbism", *sorted((model_dir / "definition").rglob("*.tmdl"))]
    if not paths or any(not path.is_file() for path in paths):
        raise FileNotFoundError("Semantic-model definition is incomplete")
    return [
        {
            "path": path.relative_to(model_dir).as_posix(),
            "payload": base64.b64encode(render_bytes(path.read_bytes())).decode("ascii"),
            "payloadType": "InlineBase64",
        }
        for path in paths
    ]


def list_models(workspace_id: str, token: str) -> list[dict]:
    _, _, payload = call("GET", f"{FABRIC_API}/workspaces/{workspace_id}/semanticModels", token)
    return [item for item in payload.get("value", []) if item.get("displayName") == MODEL_NAME]


def wait_for_operation(operation_id: str, token: str) -> None:
    for _ in range(90):
        _, _, operation = call("GET", f"{FABRIC_API}/operations/{operation_id}", token)
        status = operation.get("status")
        if status == "Succeeded":
            return
        if status in {"Failed", "Cancelled"}:
            raise RuntimeError(f"Fabric operation {status}: {json.dumps(operation.get('error'))}")
        time.sleep(4)
    raise TimeoutError(f"Fabric operation {operation_id} did not complete")


def create_model(workspace_id: str, model_dir: Path, token: str) -> str:
    matches = list_models(workspace_id, token)
    if len(matches) > 1:
        raise RuntimeError(f"Multiple semantic models named {MODEL_NAME!r} exist; resolve duplicates before deployment")
    if matches:
        print(f"Semantic model already exists: {matches[0]['id']}")
        return matches[0]["id"]

    body = {
        "displayName": MODEL_NAME,
        "description": "Direct Lake model for fictional Frontier RM customer, opportunity and meeting-preparation analytics.",
        "definition": {"format": "TMDL", "parts": definition_parts(model_dir)},
    }
    status, headers, _ = call("POST", f"{FABRIC_API}/workspaces/{workspace_id}/semanticModels", token, body)
    if status not in {201, 202}:
        raise RuntimeError(f"Unexpected semantic-model create status {status}")
    operation_id = headers.get("x-ms-operation-id") or headers.get("Operation-Id")
    if status == 202:
        if not operation_id:
            raise RuntimeError("Semantic-model create operation ID is missing")
        print(f"Semantic-model create operation: {operation_id}")
        wait_for_operation(operation_id, token)

    matches = list_models(workspace_id, token)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one deployed semantic model, found {len(matches)}")
    print(f"Semantic model deployed: {matches[0]['id']}")
    return matches[0]["id"]


def update_model(workspace_id: str, model_id: str, model_dir: Path, token: str) -> None:
    body = {"definition": {"format": "TMDL", "parts": definition_parts(model_dir)}}
    status, headers, _ = call(
        "POST",
        f"{FABRIC_API}/workspaces/{workspace_id}/semanticModels/{model_id}/updateDefinition",
        token,
        body,
    )
    if status not in {200, 202}:
        raise RuntimeError(f"Unexpected semantic-model update status {status}")
    if status == 202:
        operation_id = headers.get("x-ms-operation-id") or headers.get("Operation-Id")
        if not operation_id:
            raise RuntimeError("Semantic-model update operation ID is missing")
        print(f"Semantic-model update operation: {operation_id}")
        wait_for_operation(operation_id, token)
    print(f"Semantic model definition updated: {model_id}")


def refresh_model(workspace_id: str, model_id: str, token: str) -> None:
    status, headers, _ = call(
        "POST",
        f"{POWER_BI_API}/groups/{workspace_id}/datasets/{model_id}/refreshes",
        token,
        {"notifyOption": "NoNotification", "type": "Full", "commitMode": "transactional"},
    )
    if status != 202:
        raise RuntimeError(f"Unexpected semantic-model refresh status {status}")
    request_id = headers.get("x-ms-request-id")
    if not request_id:
        raise RuntimeError("Semantic-model refresh request ID is missing")
    print(f"Semantic-model refresh request: {request_id}")
    for _ in range(90):
        _, _, history = call(
            "GET",
            f"{POWER_BI_API}/groups/{workspace_id}/datasets/{model_id}/refreshes?$top=10",
            token,
        )
        match = next((item for item in history.get("value", []) if item.get("requestId") == request_id), None)
        if match and match.get("status") == "Completed":
            print("Semantic-model refresh completed")
            return
        if match and match.get("status") == "Failed":
            raise RuntimeError(f"Semantic-model refresh failed: {match.get('serviceExceptionJson')}")
        time.sleep(4)
    raise TimeoutError(f"Semantic-model refresh {request_id} did not complete")


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (GENERATED / f"{name}.jsonl").read_text(encoding="ascii").splitlines()]


def expected_values() -> dict[str, int | float]:
    customers = load_jsonl("customers")
    opportunities = load_jsonl("opportunities")
    profiles = load_jsonl("compliance_profiles")
    holdings = load_jsonl("holdings")
    events = load_jsonl("customer_events")
    advisory_profiles = load_jsonl("client_advisory_profiles")
    investment_activity = load_jsonl("client_investment_activity")
    houseviews = load_jsonl("cio_houseview_reports")
    return {
        "Customers": len(customers),
        "DanielAssets": next(item["relationship_value"] for item in customers if item["customer_id"] == "client-lim"),
        "OpenOpportunities": sum(item["status"] == "OPEN" for item in opportunities),
        "OpportunityPipeline": sum(item["estimated_value"] for item in opportunities),
        "ComplianceReviews": sum(
            item["kyc_status"] != "CURRENT" or item["suitability_status"] != "CURRENT" for item in profiles
        ),
        "PortfolioValue": sum(item["market_value"] for item in holdings),
        "MaturingValue": sum(item["event_value"] for item in events if item["event_type"] == "FIXED_DEPOSIT_MATURITY"),
        "RiskReviewsDue": sum(item["risk_review_status"] != "CURRENT" for item in advisory_profiles),
        "MaterialActivities": len(investment_activity),
        "ActiveHouseviewReports": sum(item["status"] == "ACTIVE" for item in houseviews),
    }


def validate_model(workspace_id: str, model_id: str, token: str) -> dict:
    query = """EVALUATE
ROW(
    \"Customers\", Customer[# Customers],
    \"DanielAssets\", CALCULATE(Customer[Assets Under Care], Customer[Customer Name] = \"Daniel Lim\"),
    \"OpenOpportunities\", Opportunities[# Open Opportunities],
    \"OpportunityPipeline\", Opportunities[Opportunity Pipeline],
    \"ComplianceReviews\", 'Compliance Due'[# Compliance Reviews],
    \"PortfolioValue\", 'Portfolio Exposure'[Portfolio Market Value],
    \"MaturingValue\", 'Maturity Watchlist'[Maturing Value]
    ,"RiskReviewsDue", 'Advisory Profile'[# Risk Reviews Due]
    ,"MaterialActivities", 'Activity Evidence'[# Material Activities]
    ,"ActiveHouseviewReports", 'Houseview Documents'[# Active Houseview Reports]
)"""
    _, _, result = call(
        "POST",
        f"{POWER_BI_API}/groups/{workspace_id}/datasets/{model_id}/executeQueries",
        token,
        {"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}},
    )
    rows = result.get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])
    query_error = result.get("results", [{}])[0].get("error")
    if query_error:
        raise RuntimeError(f"Semantic-model DAX validation failed: {json.dumps(query_error)}")
    if len(rows) != 1:
        raise RuntimeError(f"Semantic-model validation returned {len(rows)} rows")
    actual = {key.rsplit("[", 1)[-1].rstrip("]"): value for key, value in rows[0].items()}
    expected = expected_values()
    if actual != expected:
        raise RuntimeError(f"Semantic-model validation mismatch: actual={actual}, expected={expected}")
    print(f"Semantic-model DAX validation passed: {json.dumps(actual, sort_keys=True)}")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy and validate the Frontier RM Direct Lake semantic model")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--update", action="store_true", help="Replace the complete definition of the one existing model.")
    parser.add_argument("--model-id")
    args = parser.parse_args()

    fabric_token = access_token(FABRIC_RESOURCE)
    power_bi_token = access_token(POWER_BI_RESOURCE)
    if args.validate_only:
        if not args.model_id:
            raise SystemExit("--model-id is required with --validate-only")
        model_id = args.model_id
    elif args.update:
        require_local_environment()
        matches = list_models(args.workspace_id, fabric_token)
        if len(matches) != 1:
            raise SystemExit(f"--update requires exactly one {MODEL_NAME!r} model, found {len(matches)}")
        model_id = matches[0]["id"]
        update_model(args.workspace_id, model_id, args.model_dir.resolve(), fabric_token)
        refresh_model(args.workspace_id, model_id, power_bi_token)
    else:
        require_local_environment()
        model_id = create_model(args.workspace_id, args.model_dir.resolve(), fabric_token)
        refresh_model(args.workspace_id, model_id, power_bi_token)
    validate_model(args.workspace_id, model_id, power_bi_token)
    print(json.dumps({"semanticModelId": model_id, "displayName": MODEL_NAME}))


if __name__ == "__main__":
    main()
