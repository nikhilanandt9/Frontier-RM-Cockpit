from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "infra" / "environment.local.json"


def _get(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        current = current[part]
    return current


def load_local_environment(path: Path | None = None) -> dict[str, Any]:
    config_path = path or Path(os.environ.get("FRONTIER_ENVIRONMENT_FILE", DEFAULT_CONFIG))
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Local topology file not found: {config_path}. Copy infra/environment.example.json "
            "to infra/environment.local.json and populate it before deployment."
        )
    return json.loads(config_path.read_text(encoding="utf-8"))


def topology_values(environment: dict[str, Any] | None = None) -> dict[str, str]:
    config = environment or load_local_environment()
    deployment = config["deployment"]
    fabric = deployment["fabric"]
    insurance = deployment.get("insurance", {})
    insurance_fabric = insurance.get("fabric", {})
    foundry = deployment["foundry"]
    return {
        "<AZURE_SUBSCRIPTION_ID>": _get(config, "confirmedSubscription.id"),
        "<AZURE_SUBSCRIPTION_NAME>": _get(config, "confirmedSubscription.name"),
        "<AZURE_TENANT_ID>": _get(config, "confirmedSubscription.tenantId"),
        "<AZURE_RESOURCE_GROUP>": config["resourceGroup"],
        "<DEPLOYMENT_OWNER>": _get(config, "plannedTags.owner"),
        "<FABRIC_CAPACITY_ID>": fabric["capacityId"],
        "<FABRIC_WORKSPACE_NAME>": fabric["workspaceName"],
        "<FABRIC_WORKSPACE_ID>": fabric["workspaceId"],
        "<FABRIC_LAKEHOUSE_NAME>": fabric["lakehouseName"],
        "<FABRIC_LAKEHOUSE_ID>": fabric["lakehouseId"],
        "<FABRIC_SQL_ENDPOINT_ID>": fabric["sqlEndpointId"],
        "<FABRIC_SQL_ENDPOINT_HOST>": fabric["sqlEndpoint"],
        "<RM_SEMANTIC_MODEL_ID>": fabric["semanticModelId"],
        "<RM_ONTOLOGY_ID>": fabric["ontologyId"],
        "<RM_DATA_AGENT_ID>": fabric["dataAgentArtifactId"],
        "<RM_NOTEBOOK_ID>": fabric["medallionNotebookId"],
        "<RM_NOTEBOOK_JOB_ID>": fabric["medallionJobInstanceId"],
        "<RM_ONTOLOGY_GRAPH_MODEL_ID>": fabric.get("ontologyGraphModelId", ""),
        "<RM_ONTOLOGY_GRAPH_LAKEHOUSE_ID>": fabric.get("ontologyGraphLakehouseId", ""),
        "<INSURANCE_SEMANTIC_MODEL_ID>": insurance_fabric.get("semanticModelId", ""),
        "<INSURANCE_ONTOLOGY_ID>": insurance_fabric.get("ontologyId", ""),
        "<INSURANCE_DATA_AGENT_ID>": insurance_fabric.get("dataAgentId", ""),
        "<INSURANCE_NOTEBOOK_ID>": insurance_fabric.get("notebookId", ""),
        "<INSURANCE_NOTEBOOK_JOB_ID>": insurance_fabric.get("notebookJobInstanceId", ""),
        "<FOUNDRY_ACCOUNT_NAME>": foundry["accountName"],
        "<FOUNDRY_PROJECT_NAME>": foundry["projectName"],
        "<FOUNDRY_PROJECT_ENDPOINT>": foundry["projectEndpoint"],
        "<FOUNDRY_MODEL_DEPLOYMENT>": foundry["modelDeployment"],
        "<FOUNDRY_FABRIC_CONNECTION_NAME>": foundry["fabricConnectionName"],
    }


def render_text(text: str, environment: dict[str, Any] | None = None) -> str:
    if environment is None and not Path(os.environ.get("FRONTIER_ENVIRONMENT_FILE", DEFAULT_CONFIG)).is_file():
        return text
    rendered = text
    for placeholder, value in topology_values(environment).items():
        if placeholder in rendered:
            if not value:
                raise ValueError(f"Local topology value is missing for {placeholder}")
            rendered = rendered.replace(placeholder, value)
    unresolved = sorted({part.split(">", 1)[0] + ">" for part in rendered.split("<") [1:] if ">" in part})
    unresolved = [f"<{item}" for item in unresolved if item.replace("_", "").replace("-", "").replace(">", "").isalnum()]
    if unresolved:
        raise ValueError(f"Unresolved topology placeholders: {unresolved}")
    return rendered


def render_bytes(content: bytes, environment: dict[str, Any] | None = None) -> bytes:
    return render_text(content.decode("utf-8"), environment).encode("utf-8")


def resolve_or_placeholder(value: str) -> str:
    try:
        return render_text(value)
    except FileNotFoundError:
        return value


def require_resolved(**values: str) -> None:
    unresolved = [name for name, value in values.items() if "<" in value or ">" in value]
    if unresolved:
        raise RuntimeError(
            "Local topology configuration is required for: " + ", ".join(sorted(unresolved))
        )


def require_local_environment() -> dict[str, Any]:
    return load_local_environment()
