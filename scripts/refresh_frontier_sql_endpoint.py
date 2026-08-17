from __future__ import annotations

import argparse
import json
import time

from deploy_frontier_semantic_model import FABRIC_RESOURCE, access_token, call


SKILL_HEADER = "sqldw-consumption-cli"
FABRIC_API = "https://api.fabric.microsoft.com/v1"


def refresh(workspace_id: str, endpoint_id: str) -> list[dict]:
    token = access_token(FABRIC_RESOURCE)
    status, headers, payload = call(
        "POST",
        f"{FABRIC_API}/workspaces/{workspace_id}/sqlEndpoints/{endpoint_id}/refreshMetadata",
        token,
        {"timeout": {"timeUnit": "Minutes", "value": 5}},
        skill_header=SKILL_HEADER,
    )
    if status == 200:
        return payload.get("value", [])
    if status != 202:
        raise RuntimeError(f"Unexpected SQL endpoint metadata refresh status {status}")
    location = headers.get("Location") or headers.get("location")
    if not location:
        raise RuntimeError("SQL endpoint metadata refresh Location header is missing")
    for _ in range(90):
        _, _, operation = call("GET", location, token, skill_header=SKILL_HEADER)
        operation_status = operation.get("status")
        if operation_status == "Succeeded":
            result_url = operation.get("resultUrl") or f"{location}/result"
            _, _, result = call("GET", result_url, token, skill_header=SKILL_HEADER)
            return result.get("value", [])
        if operation_status in {"Failed", "Cancelled"}:
            raise RuntimeError(f"SQL endpoint metadata refresh {operation_status}: {json.dumps(operation.get('error'))}")
        time.sleep(5)
    raise TimeoutError("SQL endpoint metadata refresh did not complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh Frontier RM Lakehouse SQL endpoint metadata")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--endpoint-id", required=True)
    args = parser.parse_args()
    rows = refresh(args.workspace_id, args.endpoint_id)
    print(json.dumps({"tables": rows, "failed": [row for row in rows if row.get("status") == "Failed"]}, indent=2))


if __name__ == "__main__":
    main()
