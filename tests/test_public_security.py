from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_ENVIRONMENT = ROOT / "infra" / "environment.local.json"


def candidate_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def get_path(value: dict, path: str):
    current = value
    for part in path.split("."):
        current = current[part]
    return current


class PublicSecurityTests(unittest.TestCase):
    def test_public_files_have_no_concrete_tenant_hosts(self):
        patterns = (
            re.compile(r"https://[a-z0-9.-]+\.azurecontainerapps\.io", re.IGNORECASE),
            re.compile(r"https://[a-z0-9.-]+\.services\.ai\.azure\.com", re.IGNORECASE),
            re.compile(r"[a-z0-9-]+\.azurecr\.io", re.IGNORECASE),
            re.compile(r"[a-z0-9-]+\.datawarehouse\.fabric\.microsoft\.com", re.IGNORECASE),
        )
        findings = []
        for path in candidate_files():
            if path == LOCAL_ENVIRONMENT or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if any(pattern.search(text) for pattern in patterns):
                findings.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(findings, [])

    @unittest.skipUnless(LOCAL_ENVIRONMENT.is_file(), "local topology inventory is unavailable")
    def test_public_files_do_not_repeat_local_topology(self):
        environment = json.loads(LOCAL_ENVIRONMENT.read_text(encoding="utf-8"))
        sensitive_paths = (
            "resourceGroup",
            "confirmedSubscription.name",
            "confirmedSubscription.id",
            "confirmedSubscription.tenantId",
            "plannedTags.owner",
            "deployment.apiUrl",
            "deployment.teamsBotUrl",
            "deployment.azureOpenAIAccount",
            "deployment.registry",
            "deployment.apiRevision",
            "deployment.insurance.apiUrl",
            "deployment.insurance.containerApp",
            "deployment.insurance.revision",
            "deployment.insurance.fabric.notebookId",
            "deployment.insurance.fabric.notebookJobInstanceId",
            "deployment.insurance.fabric.semanticModelId",
            "deployment.insurance.fabric.ontologyId",
            "deployment.insurance.fabric.dataAgentId",
            "deployment.insurance.fabric.foundryConnectionId",
            "deployment.fabric.capacityName",
            "deployment.fabric.capacityArmId",
            "deployment.fabric.capacityId",
            "deployment.fabric.workspaceName",
            "deployment.fabric.workspaceId",
            "deployment.fabric.lakehouseName",
            "deployment.fabric.lakehouseId",
            "deployment.fabric.sqlEndpointId",
            "deployment.fabric.sqlEndpoint",
            "deployment.fabric.medallionNotebookId",
            "deployment.fabric.medallionJobInstanceId",
            "deployment.fabric.semanticModelId",
            "deployment.fabric.ontologyId",
            "deployment.fabric.ontologyGraphModelId",
            "deployment.fabric.ontologyGraphLakehouseId",
            "deployment.fabric.dataAgentArtifactId",
            "deployment.foundry.accountName",
            "deployment.foundry.accountId",
            "deployment.foundry.projectName",
            "deployment.foundry.projectId",
            "deployment.foundry.projectEndpoint",
            "deployment.foundry.fabricConnectionName",
            "deployment.foundry.fabricConnectionId",
            "deployment.foundry.fabricAggregateValidationResponseId",
        )
        sensitive = {
            label: str(get_path(environment, label))
            for label in sensitive_paths
            if get_path(environment, label)
        }
        findings: dict[str, list[str]] = {}
        for path in candidate_files():
            if path == LOCAL_ENVIRONMENT or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for label, value in sensitive.items():
                if value in text:
                    findings.setdefault(label, []).append(path.relative_to(ROOT).as_posix())
        self.assertEqual(findings, {})


if __name__ == "__main__":
    unittest.main()
