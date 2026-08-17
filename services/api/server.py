from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from providers import (  # noqa: E402
    GROUNDING_MODES,
    JOURNEY_ACTIONS,
    deterministic_answer,
    deterministic_general_artifact,
    deterministic_journey_artifact,
    provider_from_environment,
)
from dashboard import build_fabric_dashboard  # noqa: E402
from agent_catalog import list_agents  # noqa: E402
from advisory import build_advisory_context  # noqa: E402

DATA_PATH = ROOT / "packages" / "demo-data" / "data.json"
SOURCES_PATH = ROOT / "packages" / "demo-data" / "sources.json"
FABRIC_DATA_PATH = ROOT / "packages" / "fabric-data" / "generated"
AGENT_RUNS_PATH = ROOT / "packages" / "demo-data" / "agent-runs"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))
RUN_ID = re.compile(r"^run-[a-z0-9-]+$")
SOURCE_ID = re.compile(r"^(email|document)-[a-z0-9-]+$")
HOUSEVIEW_ID = re.compile(r"^houseview-[a-z0-9-]+$")
CLIENT_ID = re.compile(r"^client-[a-z0-9-]+$")
RULE_ID = re.compile(r"^(FAA-N16-[A-Z0-9-]+|INTERNAL-[A-Z0-9-]+)$")


def load_data() -> dict:
    base = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not (FABRIC_DATA_PATH / "manifest.json").is_file():
        return base
    return build_fabric_dashboard(base, FABRIC_DATA_PATH)


def answer_question(question: str, data: dict | None = None) -> dict:
    dataset = data or load_data()
    return deterministic_answer(question, dataset["knowledge"])


def load_sources(client_id: str | None = None, source_type: str | None = None) -> list[dict]:
    catalog = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))["sources"]
    if client_id:
        catalog = [item for item in catalog if item["clientId"] == client_id]
    if source_type:
        catalog = [item for item in catalog if item["type"] == source_type]
    return sorted(catalog, key=lambda item: item["timestamp"], reverse=True)


def load_source(source_id: str) -> dict | None:
    if not SOURCE_ID.fullmatch(source_id):
        return None
    return next((item for item in load_sources() if item["id"] == source_id), None)


def load_agent_run(run_id: str) -> dict | None:
    if not RUN_ID.fullmatch(run_id):
        return None
    path = AGENT_RUNS_PATH / f"{run_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_agent_runs() -> list[dict]:
    summaries = []
    for path in sorted(AGENT_RUNS_PATH.glob("run-*.json")):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        run = bundle["run"]
        verification = bundle["outcome"]["verificationStatus"]
        mode_label = "Captured live" if run["mode"] == "captured-live" else "Rehearsal"
        summaries.append(
            {
                **run,
                "verificationStatus": verification,
                "displayLabel": f"{mode_label} · {verification.replace('-', ' ').title()}",
            }
        )
    return sorted(summaries, key=lambda item: item["startedAt"], reverse=True)


class FrontierHandler(SimpleHTTPRequestHandler):
    server_version = "FrontierRM/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, title: str, content: str) -> None:
        body = (
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width'><title>{title}</title>"
            "<style>body{font:16px Segoe UI,sans-serif;max-width:760px;margin:64px auto;"
            "padding:0 24px;color:#242124}h1{color:#b00020}p{line-height:1.6}</style>"
            f"</head><body><h1>{title}</h1>{content}</body></html>"
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.path = "/apps/web/index.html"
            return super().do_GET()
        if path == "/api/health":
            provider = provider_from_environment()
            runs = list_agent_runs()
            dashboard = load_data()
            return self._send_json(
                {
                    "status": "ok",
                    "service": "frontier-rm-api",
                    "provider": provider.name,
                    "azureWritesEnabled": False,
                    "resourceGroup": "<AZURE_RESOURCE_GROUP>",
                    "fabricCapacity": "F4",
                    "fabricWorkspace": "<FABRIC_WORKSPACE_NAME>",
                    "fabricDataPlaneRegion": "Australia East",
                    "dashboardDataSource": dashboard.get("dataSource", {}).get("kind", "demo-data"),
                    "dashboardCustomerCount": len(dashboard["clients"]),
                    "agentRunMode": runs[0]["mode"] if runs else "unavailable",
                }
            )
        if path == "/api/dashboard":
            return self._send_json(load_data())
        if path == "/api/agents":
            return self._send_json({"agents": list_agents()})
        if path == "/api/houseview":
            return self._send_json({"reports": load_data().get("houseviews", [])})
        houseview_match = re.fullmatch(r"/api/houseview/([a-z0-9-]+)", path)
        if houseview_match:
            report_id = houseview_match.group(1)
            if not HOUSEVIEW_ID.fullmatch(report_id):
                return self._send_json({"error": "Houseview report not found"}, HTTPStatus.NOT_FOUND)
            report = next((item for item in load_data().get("houseviews", []) if item["houseview_id"] == report_id), None)
            if report is None:
                return self._send_json({"error": "Houseview report not found"}, HTTPStatus.NOT_FOUND)
            return self._send_json({"report": report})
        advisory_match = re.fullmatch(r"/api/clients/(client-[a-z0-9-]+)/advisory-context", path)
        if advisory_match:
            client_id = advisory_match.group(1)
            if not CLIENT_ID.fullmatch(client_id):
                return self._send_json({"error": "Client advisory context not found"}, HTTPStatus.NOT_FOUND)
            from urllib.parse import parse_qs

            houseview_id = parse_qs(parsed.query).get("houseviewId", [None])[0]
            try:
                context = build_advisory_context(load_data(), client_id, houseview_id)
            except ValueError as exc:
                return self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            return self._send_json({"context": context})
        if path == "/api/regulatory-controls":
            data = load_data()
            return self._send_json({"documents": data.get("regulatoryDocuments", []), "rules": data.get("regulatoryRules", [])})
        rule_match = re.fullmatch(r"/api/regulatory-controls/([A-Z0-9-]+)", path)
        if rule_match:
            rule_id = rule_match.group(1)
            if not RULE_ID.fullmatch(rule_id):
                return self._send_json({"error": "Regulatory control not found"}, HTTPStatus.NOT_FOUND)
            rule = next((item for item in load_data().get("regulatoryRules", []) if item["regulatory_rule_id"] == rule_id), None)
            if rule is None:
                return self._send_json({"error": "Regulatory control not found"}, HTTPStatus.NOT_FOUND)
            return self._send_json({"rule": rule})
        if path == "/api/sources":
            from urllib.parse import parse_qs

            query = parse_qs(parsed.query)
            client_id = query.get("clientId", [None])[0]
            source_type = query.get("type", [None])[0]
            if source_type not in {None, "email", "document"}:
                return self._send_json({"error": "Source type must be email or document"}, HTTPStatus.BAD_REQUEST)
            return self._send_json({"sources": load_sources(client_id, source_type)})
        source_match = re.fullmatch(r"/api/sources/([a-z0-9-]+)", path)
        if source_match:
            source = load_source(source_match.group(1))
            if source is None:
                return self._send_json({"error": "Source not found"}, HTTPStatus.NOT_FOUND)
            return self._send_json({"source": source})
        if path == "/api/meeting-preparation/runs":
            return self._send_json({"runs": list_agent_runs()})
        run_match = re.fullmatch(r"/api/meeting-preparation/runs/(run-[a-z0-9-]+)(/events)?", path)
        if run_match:
            bundle = load_agent_run(run_match.group(1))
            if bundle is None:
                return self._send_json({"error": "Agent run not found"}, HTTPStatus.NOT_FOUND)
            if run_match.group(2):
                return self._send_json({"runId": bundle["run"]["id"], "events": bundle["events"]})
            return self._send_json({
                "run": bundle["run"],
                "agents": bundle["agents"],
                "outcome": bundle["outcome"],
            })
        if path == "/privacy":
            return self._send_html(
                "Frontier RM Demo Privacy",
                "<p>This internal demonstration uses only fictional client records. "
                "It does not intentionally collect or store personal customer data.</p>",
            )
        if path == "/terms":
            return self._send_html(
                "Frontier RM Demo Terms",
                "<p>Internal EBC demonstration only. Outputs require human review and must not be "
                "treated as financial advice, client communication, or transaction instructions.</p>",
            )
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {"/api/knowledge/query", "/api/opportunities/generate"}:
            return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("Request body must be between 1 and 16384 bytes")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if path == "/api/knowledge/query":
                question = str(payload.get("question", "")).strip()
                if not question or len(question) > 1_000:
                    raise ValueError("Question must be between 1 and 1000 characters")
            else:
                client_id = str(payload.get("clientId", "")).strip()
                if not client_id or len(client_id) > 100:
                    raise ValueError("A valid clientId is required")
                action = str(payload.get("action", "briefing")).strip()
                if action not in JOURNEY_ACTIONS:
                    raise ValueError("Action must be briefing, recommendation, or opportunity-draft")
                houseview_id = str(payload.get("houseviewId", "")).strip() or None
                if houseview_id and not HOUSEVIEW_ID.fullmatch(houseview_id):
                    raise ValueError("A valid houseviewId is required")
                grounding_mode = str(payload.get("groundingMode", "fabric-iq")).strip()
                if grounding_mode not in GROUNDING_MODES:
                    raise ValueError("groundingMode must be fabric-iq or general")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        provider = provider_from_environment()
        dataset = load_data()
        if path == "/api/knowledge/query":
            try:
                result = provider.answer(question, dataset["knowledge"])
            except RuntimeError:
                result = answer_question(question, dataset)
                result["fallbackReason"] = "live-provider-unavailable"
        else:
            client = next((item for item in dataset["clients"] if item["id"] == client_id), None)
            opportunity = next((item for item in dataset["opportunities"] if item["clientId"] == client_id), None)
            if client is None or opportunity is None:
                return self._send_json({"error": "Client recommendation not found"}, HTTPStatus.NOT_FOUND)
            sources = load_sources(client_id) if grounding_mode == "fabric-iq" else []
            advisory_context = None
            if grounding_mode == "fabric-iq":
                try:
                    advisory_context = build_advisory_context(dataset, client_id, houseview_id)
                except ValueError as exc:
                    return self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            try:
                recommend = getattr(provider, "recommend")
                result = recommend(client, opportunity, action, sources, advisory_context, grounding_mode)
            except (AttributeError, RuntimeError):
                result = (
                    deterministic_journey_artifact(client, opportunity, action, sources, advisory_context)
                    if grounding_mode == "fabric-iq"
                    else deterministic_general_artifact(client, opportunity, action)
                )
                result["fallbackReason"] = "live-provider-unavailable"
            result["groundingMode"] = grounding_mode
            result.setdefault("groundingLabel", "Fabric IQ grounded" if grounding_mode == "fabric-iq" else "General AI draft")
        return self._send_json(result)

    def end_headers(self) -> None:
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        super().end_headers()

    def guess_type(self, path: str) -> str:
        return mimetypes.guess_type(path)[0] or "application/octet-stream"


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), FrontierHandler)
    print(f"Frontier RM Cockpit listening on http://{HOST}:{PORT}")
    print("Provider: deterministic-mock | Azure writes: disabled")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
