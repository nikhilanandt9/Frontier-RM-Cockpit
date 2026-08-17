from __future__ import annotations

import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, parse, request

import jwt


ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api"
sys.path.insert(0, str(API_SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cards import build_knowledge_card  # noqa: E402
from bot_auth import connector_token, is_trusted_service_url, validate_bot_token  # noqa: E402
from providers import deterministic_answer  # noqa: E402


HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "3978"))
API_URL = os.environ.get("FRONTIER_API_URL", "http://127.0.0.1:8080").rstrip("/")
DATA_PATH = ROOT / "packages" / "demo-data" / "data.json"
MAX_ACTIVITY_BYTES = 64 * 1024
AUTH_MODE = os.environ.get("FRONTIER_BOT_AUTH_MODE", "playground").casefold()


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def clean_message_text(text: str) -> str:
    cleaned = " ".join(text.replace("<at>Frontier RM</at>", " ").split())
    return cleaned[:1000]


def query_knowledge(question: str) -> dict:
    payload = json.dumps({"question": question}).encode("utf-8")
    api_request = request.Request(
        f"{API_URL}/api/knowledge/query",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "frontier-rm-teams/0.1"},
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        result = deterministic_answer(question, load_data()["knowledge"])
        result["fallbackReason"] = "shared-api-unavailable"
        return result


def build_reply(activity: dict) -> dict:
    activity_type = activity.get("type")
    if activity_type == "conversationUpdate":
        return {
            "type": "message",
            "text": (
                "Frontier RM is ready. Ask an approved process question, such as "
                "what to check before a fixed deposit matures."
            ),
        }

    question = clean_message_text(str(activity.get("text", "")))
    if not question:
        question = "What can Frontier Knowledge help me with?"
    result = query_knowledge(question)
    return {
        "type": "message",
        "text": result["answer"],
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": build_knowledge_card(question, result),
            }
        ],
        "channelData": {
            "frontierProvider": result.get("provider", "deterministic-mock"),
            "escalationRequired": bool(result.get("escalationRequired")),
        },
    }


def callback_url(activity: dict) -> str | None:
    service_url = str(activity.get("serviceUrl", "")).rstrip("/")
    conversation_id = str(activity.get("conversation", {}).get("id", ""))
    activity_id = str(activity.get("id", ""))
    if not service_url or not conversation_id or not activity_id:
        return None

    if not is_trusted_service_url(service_url, playground=AUTH_MODE == "playground"):
        raise ValueError("Activity service URL is not trusted")
    return (
        f"{service_url}/v3/conversations/{parse.quote(conversation_id, safe='')}"
        f"/activities/{parse.quote(activity_id, safe='')}"
    )


def send_reply(activity: dict, reply: dict) -> bool:
    destination = callback_url(activity)
    if destination is None:
        return False
    headers = {"Content-Type": "application/json", "User-Agent": "frontier-rm-teams/0.2"}
    if AUTH_MODE == "botframework":
        headers["Authorization"] = f"Bearer {connector_token()}"
    callback = request.Request(
        destination,
        data=json.dumps(reply).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with request.urlopen(callback, timeout=10):
        return True


class TeamsBotHandler(BaseHTTPRequestHandler):
    server_version = "FrontierRMTeams/0.1"

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path in {"/health", "/api/messages"}:
            self.send_response(HTTPStatus.OK)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            return self._send_json(
                {
                    "status": "ok",
                    "service": "frontier-rm-teams",
                    "authMode": AUTH_MODE,
                    "sharedApi": API_URL,
                    "azureWritesEnabled": False,
                }
            )
        return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/messages":
            return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_ACTIVITY_BYTES:
                raise ValueError("Activity body must be between 1 and 65536 bytes")
            activity = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if activity.get("type") not in {"message", "conversationUpdate"}:
                return self._send_json({"status": "ignored"}, HTTPStatus.ACCEPTED)
            if AUTH_MODE == "botframework":
                validate_bot_token(self.headers.get("Authorization", ""), str(activity.get("serviceUrl", "")))
            reply = build_reply(activity)
            delivered = send_reply(activity, reply)
        except (ValueError, jwt.PyJWTError):
            return self._send_json({"error": "Unauthorized activity"}, HTTPStatus.UNAUTHORIZED)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except (error.URLError, TimeoutError):
            return self._send_json({"error": "Playground callback failed"}, HTTPStatus.BAD_GATEWAY)

        if delivered:
            return self._send_json({"status": "accepted"}, HTTPStatus.ACCEPTED)
        return self._send_json({"status": "local-response", "activity": reply})

    def log_message(self, message_format: str, *args) -> None:
        print(f"Teams adapter: {message_format % args}")


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), TeamsBotHandler)
    print(f"Frontier RM Teams adapter listening on http://{HOST}:{PORT}/api/messages")
    print(f"Shared API: {API_URL} | Auth: {AUTH_MODE} | Azure writes: disabled")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
