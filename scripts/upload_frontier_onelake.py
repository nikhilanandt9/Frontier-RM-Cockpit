from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from urllib import error, parse, request

from topology_config import require_resolved, resolve_or_placeholder


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_ID = resolve_or_placeholder("<FABRIC_WORKSPACE_ID>")
DEFAULT_LAKEHOUSE_ID = resolve_or_placeholder("<FABRIC_LAKEHOUSE_ID>")


def azure_cli() -> str:
    command = shutil.which("az") or shutil.which("az.cmd")
    if command:
        return command
    standard = Path(r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd")
    if standard.is_file():
        return str(standard)
    raise FileNotFoundError("Azure CLI was not found")


def storage_token() -> str:
    result = subprocess.run(
        [
            azure_cli(),
            "account",
            "get-access-token",
            "--resource",
            "https://storage.azure.com/",
            "--query",
            "accessToken",
            "--output",
            "tsv",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def call(method: str, url: str, token: str, body: bytes | None = None) -> None:
    http_request = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "x-ms-version": "2023-11-03",
            "Content-Type": "application/octet-stream",
        },
        method=method,
    )
    try:
        with request.urlopen(http_request, timeout=120):
            return
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} OneLake request failed with HTTP {exc.code}: {detail}") from exc


def base_url(workspace_id: str, lakehouse_id: str, path: str) -> str:
    encoded = "/".join(parse.quote(part, safe="") for part in path.split("/"))
    return f"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/{encoded}"


def ensure_directory(workspace_id: str, lakehouse_id: str, path: str, token: str) -> None:
    url = f"{base_url(workspace_id, lakehouse_id, path)}?resource=directory"
    try:
        call("PUT", url, token)
    except RuntimeError as exc:
        if "HTTP 409" not in str(exc):
            raise


def upload_file(workspace_id: str, lakehouse_id: str, local: Path, remote: str, token: str) -> dict:
    payload = local.read_bytes()
    url = base_url(workspace_id, lakehouse_id, remote)
    call("PUT", f"{url}?resource=file", token)
    if payload:
        call("PATCH", f"{url}?action=append&position=0", token, payload)
    call("PATCH", f"{url}?action=flush&position={len(payload)}", token)
    return {"local": str(local), "remote": remote, "bytes": len(payload)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload Frontier RM deterministic data and research documents to OneLake")
    parser.add_argument("--workspace-id", default=DEFAULT_WORKSPACE_ID)
    parser.add_argument("--lakehouse-id", default=DEFAULT_LAKEHOUSE_ID)
    args = parser.parse_args()
    require_resolved(workspace_id=args.workspace_id, lakehouse_id=args.lakehouse_id)

    generated = ROOT / "packages" / "fabric-data" / "generated"
    landing = "Files/bronze/landing/seed=20260812"
    files = [(path, f"{landing}/{path.name}") for path in sorted(generated.glob("*.jsonl"))]
    files.extend(
        [
            (ROOT / "packages" / "demo-data" / "houseview" / "houseview-2026-h2.pdf", "Files/houseview/houseview-2026-h2.pdf"),
            (ROOT / "packages" / "demo-data" / "houseview" / "houseview-2026-q4.pdf", "Files/houseview/houseview-2026-q4.pdf"),
            (
                ROOT / "packages" / "demo-data" / "regulatory" / "frontier_faa_n16_demo_control_pack.pdf",
                "Files/regulatory/frontier_faa_n16_demo_control_pack.pdf",
            ),
        ]
    )
    if any(not local.is_file() for local, _ in files):
        missing = [str(local) for local, _ in files if not local.is_file()]
        raise FileNotFoundError(f"Required upload files are missing: {missing}")

    token = storage_token()
    for directory in ("Files", "Files/bronze", "Files/bronze/landing", landing, "Files/houseview", "Files/regulatory"):
        ensure_directory(args.workspace_id, args.lakehouse_id, directory, token)
    uploaded = [upload_file(args.workspace_id, args.lakehouse_id, local, remote, token) for local, remote in files]
    print(json.dumps({"uploaded": len(uploaded), "bytes": sum(item["bytes"] for item in uploaded), "files": uploaded}, indent=2))


if __name__ == "__main__":
    main()