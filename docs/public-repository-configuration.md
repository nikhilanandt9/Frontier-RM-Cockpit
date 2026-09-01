# Public repository configuration

This repository contains portable source templates only. Tenant-specific Azure and Microsoft Fabric topology must not be committed.

## Local environment inventory

1. Copy `infra/environment.example.json` to `infra/environment.local.json`.
2. Populate the local file with the target subscription, tenant, resource group, Fabric item IDs, and service endpoints.
3. Keep `infra/environment.local.json` local. It is ignored by Git.

Deployment scripts use `scripts/topology_config.py` to replace placeholders in memory immediately before encoding notebook, semantic-model, Ontology, and Data Agent payloads. Checked-in definitions therefore remain tenant-neutral.

Set `FRONTIER_ENVIRONMENT_FILE` when the local inventory is stored outside the default path:

```powershell
$env:FRONTIER_ENVIRONMENT_FILE = 'C:\secure-config\frontier.environment.json'
```

## Deployment parameters

Environment-specific Bicep values are required parameters. Supply them from the ignored local inventory or a secure CI variable store. Do not commit generated parameter files.

For the Insurance Container App, provide at least:

- `owner`
- `expiry`
- `foundryAccountName`
- `foundryProjectEndpoint`
- `fabricWorkspaceName`
- `insuranceDataAgentId`

## Validation

Run before every public push:

```powershell
python -m unittest tests.test_public_security -v
python -m unittest discover -s tests -q
git diff --cached --check
```

The public-security tests reject concrete tenant-specific Azure/Fabric hostnames. When `infra/environment.local.json` exists, they also ensure its sensitive topology values do not appear in any tracked or untracked Git candidate file.

GitHub secret scanning, push protection, Dependabot vulnerability alerts, and automated security fixes should remain enabled.
