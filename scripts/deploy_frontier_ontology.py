from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_ROOT = ROOT / "fabric" / "ontology"
DEFINITION_ROOT = ONTOLOGY_ROOT / "definition"
ONTOLOGY_NAME = "Frontier_RM_Ontology"
FABRIC_API = "https://api.fabric.microsoft.com/v1"
SKILL_HEADER = "fabriciq-ontology-cli"
sys.path.insert(0, str(ROOT / "scripts"))

from deploy_frontier_semantic_model import FABRIC_RESOURCE, access_token, call as shared_call  # noqa: E402


def call(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, dict, dict]:
    return shared_call(method, url, token, body, skill_header=SKILL_HEADER)


def wait_for_operation(operation_id: str, token: str) -> None:
    for _ in range(90):
        _, _, operation = call("GET", f"{FABRIC_API}/operations/{operation_id}", token)
        status = operation.get("status")
        if status == "Succeeded":
            return
        if status in {"Failed", "Cancelled"}:
            raise RuntimeError(f"Ontology operation {status}: {json.dumps(operation.get('error'))}")
        time.sleep(4)
    raise TimeoutError(f"Ontology operation {operation_id} did not complete")


def definition_parts() -> list[dict]:
    files = sorted(path for path in DEFINITION_ROOT.rglob("*") if path.is_file())
    spec = json.loads((ONTOLOGY_ROOT / "spec.json").read_text(encoding="ascii"))
    expected = 2 + (2 * len(spec["entityTypes"])) + (2 * len(spec["relationshipTypes"]))
    if len(files) != expected:
        raise RuntimeError(f"Expected {expected} Ontology definition parts, found {len(files)}")
    return [
        {
            "path": path.relative_to(DEFINITION_ROOT).as_posix(),
            "payload": base64.b64encode(path.read_bytes()).decode("ascii"),
            "payloadType": "InlineBase64",
        }
        for path in files
    ]


def list_ontologies(workspace_id: str, token: str) -> list[dict]:
    _, _, payload = call(
        "GET",
        f"{FABRIC_API}/workspaces/{workspace_id}/items?type=Ontology",
        token,
    )
    return [item for item in payload.get("value", []) if item.get("displayName") == ONTOLOGY_NAME]


def definition_result(workspace_id: str, ontology_id: str, token: str) -> dict:
    status, headers, payload = call(
        "POST",
        f"{FABRIC_API}/workspaces/{workspace_id}/items/{ontology_id}/getDefinition",
        token,
        {},
    )
    if status == 200:
        return payload
    if status != 202:
        raise RuntimeError(f"Unexpected Ontology getDefinition status {status}")
    operation_id = headers.get("x-ms-operation-id") or headers.get("Operation-Id")
    if not operation_id:
        raise RuntimeError("Ontology getDefinition operation ID is missing")
    wait_for_operation(operation_id, token)
    _, _, result = call("GET", f"{FABRIC_API}/operations/{operation_id}/result", token)
    return result


def verify_definition(workspace_id: str, ontology_id: str, token: str) -> None:
    result = definition_result(workspace_id, ontology_id, token)
    paths = {part["path"] for part in result.get("definition", {}).get("parts", [])}
    expected = {part["path"] for part in definition_parts()}
    if paths != expected:
        raise RuntimeError(f"Ontology readback paths differ: missing={sorted(expected - paths)}, extra={sorted(paths - expected)}")
    print(f"Ontology definition readback passed: {len(paths)} parts")


def create_ontology(workspace_id: str, token: str) -> str:
    existing = list_ontologies(workspace_id, token)
    if len(existing) > 1:
        raise RuntimeError(f"Multiple Ontologies named {ONTOLOGY_NAME!r} exist; resolve duplicates first")
    if existing:
        ontology_id = existing[0]["id"]
        body = {"definition": {"parts": definition_parts()}}
        status, headers, _ = call(
            "POST",
            f"{FABRIC_API}/workspaces/{workspace_id}/items/{ontology_id}/updateDefinition",
            token,
            body,
        )
        if status not in {200, 202}:
            raise RuntimeError(f"Unexpected Ontology update status {status}")
        if status == 202:
            operation_id = headers.get("x-ms-operation-id") or headers.get("Operation-Id")
            if not operation_id:
                raise RuntimeError("Ontology update operation ID is missing")
            print(f"Ontology update operation: {operation_id}")
            wait_for_operation(operation_id, token)
        print(f"Ontology definition updated: {ontology_id}")
        return ontology_id

    body = {
        "displayName": ONTOLOGY_NAME,
        "type": "Ontology",
        "definition": {"parts": definition_parts()},
    }
    status, headers, _ = call("POST", f"{FABRIC_API}/workspaces/{workspace_id}/items", token, body)
    if status not in {201, 202}:
        raise RuntimeError(f"Unexpected Ontology create status {status}")
    if status == 202:
        operation_id = headers.get("x-ms-operation-id") or headers.get("Operation-Id")
        if not operation_id:
            raise RuntimeError("Ontology create operation ID is missing")
        print(f"Ontology create operation: {operation_id}")
        wait_for_operation(operation_id, token)

    existing = list_ontologies(workspace_id, token)
    if len(existing) != 1:
        raise RuntimeError(f"Expected one deployed Ontology, found {len(existing)}")
    print(f"Ontology deployed: {existing[0]['id']}")
    return existing[0]["id"]


def preview() -> dict:
    spec = json.loads((ONTOLOGY_ROOT / "spec.json").read_text(encoding="ascii"))
    return {
        "displayName": spec["displayName"],
        "entities": len(spec["entityTypes"]),
        "relationships": len(spec["relationshipTypes"]),
        "bindings": len(spec["entityTypes"]),
        "parts": len(definition_parts()),
        "sourceSchema": spec["sourceSchema"],
        "sourceTables": [item["sourceTableName"] for item in spec["entityTypes"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or deploy the Frontier RM Fabric IQ Ontology")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Required with --apply after the chat preview is confirmed.")
    args = parser.parse_args()

    if not args.apply:
        print(json.dumps(preview(), indent=2))
        return
    if not args.yes:
        raise SystemExit("Ontology apply requires --yes after explicit preview confirmation")

    token = access_token(FABRIC_RESOURCE)
    ontology_id = create_ontology(args.workspace_id, token)
    verify_definition(args.workspace_id, ontology_id, token)
    print(json.dumps({"ontologyId": ontology_id, "displayName": ONTOLOGY_NAME}))


if __name__ == "__main__":
    main()
