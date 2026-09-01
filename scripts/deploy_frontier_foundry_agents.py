from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FabricDataAgentToolParameters,
    MicrosoftFabricPreviewTool,
    PromptAgentDefinition,
    ToolProjectConnection,
)
from azure.identity import AzureCliCredential

from topology_config import require_resolved, resolve_or_placeholder


DEFAULT_ENDPOINT = resolve_or_placeholder("<FOUNDRY_PROJECT_ENDPOINT>")
DEFAULT_MODEL = "frontier-gpt-4-1-mini"
DEFAULT_FABRIC_CONNECTION_NAME = resolve_or_placeholder("<FOUNDRY_FABRIC_CONNECTION_NAME>")
CUSTOMER_INTELLIGENCE_NAME = "frontier-customer-intelligence"


@dataclass(frozen=True)
class AgentSpec:
    name: str
    role: str
    instructions: str
    requires_fabric: bool = False


AGENTS = (
    AgentSpec(
        name="frontier-rm-orchestrator",
        role="Plans, delegates, and verifies meeting preparation",
        instructions=(
            "You are the Frontier RM Orchestrator for a fictional internal banking demonstration. "
            "Plan work across Customer Intelligence, Market Context, and Meeting Preparation. "
            "Require evidence references for factual claims, preserve unresolved questions, and never "
            "present private chain-of-thought. Return concise plans, delegation events, and a final "
            "verification decision for John Doe's review. Treat all client facts as unavailable unless "
            "they are supplied in the request or returned by an attached tool. Never invent customer "
            "history, preferences, evidence IDs, or market conditions. Never provide financial advice "
            "or imply that an action was executed."
        ),
    ),
    AgentSpec(
        name=CUSTOMER_INTELLIGENCE_NAME,
        role="Retrieves governed relationship context from Fabric",
        requires_fabric=True,
        instructions=(
            "You are Frontier Customer Intelligence with access to the published Frontier RM Microsoft "
            "Fabric data agent. Always use the Fabric tool for customer, household, account, holding, "
            "compliance, opportunity, event, and relationship-manager facts. Report only values returned "
            "by the tool, identify missing fields explicitly, and preserve the source identifiers present "
            "in the result. Never invent evidence IDs, balances, preferences, consent, suitability, client "
            "intent, relationship links, or tool output. If the Fabric tool is unavailable or fails, state "
            "that governed customer data could not be retrieved and do not answer from model knowledge."
        ),
    ),
    AgentSpec(
        name="frontier-market-context",
        role="Frames relevant market considerations and boundaries",
        instructions=(
            "You are Frontier Market Context for a fictional internal banking demonstration. Given "
            "approved market and product facts, identify context relevant to a client conversation. "
            "Separate facts from considerations, avoid forecasts and guaranteed-return comparisons, "
            "and state when current approved information is unavailable. Do not create evidence IDs or "
            "cite a source unless that exact evidence ID or source was supplied in the request."
        ),
    ),
    AgentSpec(
        name="frontier-meeting-preparation",
        role="Builds a human-reviewed relationship meeting brief",
        instructions=(
            "You are Frontier Meeting Preparation. Synthesize supplied customer evidence, market "
            "context, consent, and mandatory checks into a needs-led meeting brief for John Doe. "
            "Include what changed, unresolved questions, recommended discussion actions, and an "
            "editable opening. If required evidence is not supplied, list only the missing evidence and "
            "do not draft a brief. Do not invent personal details, facts, evidence IDs, or sources; "
            "recommend a specific investment; or imply client communication occurred. Human review is "
            "always required."
        ),
    ),
)


def fabric_tool(connection_id: str) -> MicrosoftFabricPreviewTool:
    return MicrosoftFabricPreviewTool(
        fabric_dataagent_preview=FabricDataAgentToolParameters(
            project_connections=[ToolProjectConnection(project_connection_id=connection_id)]
        )
    )


def preview(endpoint: str, model: str, fabric_connection_id: str | None = None) -> dict:
    return {
        "projectEndpoint": endpoint,
        "model": model,
        "agents": [
            {
                "name": agent.name,
                "role": agent.role,
                "requiresFabricConnection": agent.requires_fabric,
            }
            for agent in AGENTS
        ],
        "fabricToolAttached": bool(fabric_connection_id),
        "fabricConnectionId": fabric_connection_id,
    }


def deploy(endpoint: str, model: str, fabric_connection_name: str) -> tuple[list[dict], str]:
    deployed = []
    with AzureCliCredential() as credential, AIProjectClient(
        endpoint=endpoint,
        credential=credential,
        allow_preview=True,
    ) as project:
        connection = project.connections.get(fabric_connection_name)
        for agent in (item for item in AGENTS if item.requires_fabric):
            tools = [fabric_tool(connection.id)]
            version = project.agents.create_version(
                agent_name=agent.name,
                definition=PromptAgentDefinition(
                    model=model,
                    instructions=agent.instructions,
                    tools=tools,
                ),
            )
            deployed.append(
                {
                    "id": version.id,
                    "name": version.name,
                    "version": version.version,
                    "requiresFabricConnection": True,
                    "fabricToolAttached": True,
                }
            )
    return deployed, connection.id


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or deploy Frontier RM Foundry prompt agents")
    parser.add_argument("--endpoint", default=os.environ.get("FOUNDRY_PROJECT_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--model", default=os.environ.get("FOUNDRY_MODEL_NAME", DEFAULT_MODEL))
    parser.add_argument(
        "--fabric-connection-name",
        default=os.environ.get("FABRIC_PROJECT_CONNECTION_NAME", DEFAULT_FABRIC_CONNECTION_NAME),
    )
    parser.add_argument("--fabric-connection-id", default=os.environ.get("FABRIC_PROJECT_CONNECTION_ID"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    proposal = preview(args.endpoint, args.model, args.fabric_connection_id)
    if not args.apply:
        print(json.dumps(proposal, indent=2))
        return

    require_resolved(endpoint=args.endpoint, fabric_connection_name=args.fabric_connection_name)
    result, connection_id = deploy(args.endpoint, args.model, args.fabric_connection_name)
    print(json.dumps({**preview(args.endpoint, args.model, connection_id), "deployed": result}, indent=2))


if __name__ == "__main__":
    main()