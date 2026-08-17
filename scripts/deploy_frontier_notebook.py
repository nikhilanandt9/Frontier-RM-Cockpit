from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
FABRIC_API = "https://api.fabric.microsoft.com/v1"
FABRIC_RESOURCE = "https://api.fabric.microsoft.com"
SKILL_HEADER = "spark-authoring-cli"
DEFAULT_NOTEBOOK = ROOT / "fabric" / "notebooks" / "01_build_frontier_rm_medallion.ipynb"


def azure_cli() -> str:
    command = shutil.which("az") or shutil.which("az.cmd")
    if command:
        return command
    standard = Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd")
    if standard.is_file():
        return str(standard)
    raise FileNotFoundError("Azure CLI was not found")


def access_token() -> str:
    result = subprocess.run(
        [azure_cli(), "account", "get-access-token", "--resource", FABRIC_RESOURCE, "--query", "accessToken", "-o", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def call(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, dict, dict]:
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    http_request = request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-ms-fabric-skill": SKILL_HEADER,
        },
        method=method,
    )
    try:
        with request.urlopen(http_request, timeout=120) as response:
            content = response.read().decode("utf-8")
            return response.status, dict(response.headers), json.loads(content) if content else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc


def wait_for_operation(operation_id: str, token: str) -> None:
    for _ in range(120):
        _, _, operation = call("GET", f"{FABRIC_API}/operations/{operation_id}", token)
        status = operation.get("status")
        if status == "Succeeded":
            return
        if status in {"Failed", "Cancelled"}:
            raise RuntimeError(f"Notebook operation {status}: {json.dumps(operation.get('error'))}")
        time.sleep(5)
    raise TimeoutError(f"Notebook operation {operation_id} did not complete")


def update_notebook(workspace_id: str, notebook_id: str, notebook_path: Path, token: str) -> None:
    json.loads(notebook_path.read_text(encoding="utf-8"))
    body = {
        "definition": {
            "format": "ipynb",
            "parts": [
                {
                    "path": "notebook-content.ipynb",
                    "payload": base64.b64encode(notebook_path.read_bytes()).decode("ascii"),
                    "payloadType": "InlineBase64",
                }
            ],
        }
    }
    status, headers, _ = call(
        "POST",
        f"{FABRIC_API}/workspaces/{workspace_id}/notebooks/{notebook_id}/updateDefinition",
        token,
        body,
    )
    if status not in {200, 202}:
        raise RuntimeError(f"Unexpected notebook update status {status}")
    if status == 202:
        operation_id = headers.get("x-ms-operation-id") or headers.get("Operation-Id")
        if not operation_id:
            raise RuntimeError("Notebook update operation ID is missing")
        print(f"Notebook update operation: {operation_id}")
        wait_for_operation(operation_id, token)
    print(f"Notebook definition updated: {notebook_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update the Frontier RM Fabric medallion notebook")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--notebook-id", required=True)
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    args = parser.parse_args()
    update_notebook(args.workspace_id, args.notebook_id, args.notebook.resolve(), access_token())


if __name__ == "__main__":
    main()
