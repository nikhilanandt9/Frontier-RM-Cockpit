# Frontier RM Cockpit

Frontier RM Cockpit is an independently authored internal EBC demonstration of a day in the life of a Premier relationship manager. It combines an operational web cockpit, a governed AI backend, deterministic synthetic banking scenarios, and a Microsoft Teams bot.

> Internal demonstration only. All clients, balances, products, rates, recommendations, and outcomes are fictional. The experience does not provide financial advice or execute transactions.

## Experience

- `Today`: portfolio pulse, daily priorities, service alerts, and compliance tasks
- `Clients`: individual Client 360, portfolio context, consent, and suitability for synthetic Premier clients
- `Opportunities`: briefing, fictional-product recommendations, and editable email/CRM drafts with evidence and required checks; a comparison control runs the same model with or without Fabric IQ grounding
- `Sources`: realistic fictional Outlook-style correspondence and SharePoint-style documents used as cited context
- `Operations`: service health, synthetic signals, and an accurate technology view
- `Houseview`: fictional CIO research, declared versus observed investment risk, recent activity, tailored positioning candidates, and cited advisory controls

Frontier Copilot is available as a persistent collapsible panel from every view. It retains the grounded knowledge contract, citations, and escalation boundaries without occupying a primary navigation tab.

The active Houseview is dated 19 August 2026. The Houseview storyline uses a client-declared **Investment Risk Profile Score** from 1–5 and a separate activity-derived **Observed Behaviour Indicator**. Buys and sells may trigger a profile review but never silently change the declared profile. Regulatory outputs are compliance-aware internal controls with FAA-N16 paragraph citations; they are not legal advice or proof of compliance.

The Opportunities comparison uses `gpt-4.1-mini` in both modes. **With Fabric IQ** adds governed Client 360, enterprise sources, Houseview, activity, relationships, provenance, and deterministic control evidence. **Without Fabric IQ** uses a deliberately shallow client and opportunity profile to produce a general AI draft. Neither mode makes a suitability determination, executes a transaction, sends a message, or commits a CRM record; mandatory human review remains explicit.

## Repository layout

```text
apps/web/          Responsive Frontier RM web cockpit
apps/teams/        Microsoft Teams bot and app package
services/api/      Python API with deterministic and Azure AI providers
packages/          Shared contracts and deterministic demo data
fabric/            Notebook, Direct Lake semantic model, and Ontology definitions
infra/             Azure templates and verified deployment inventory
docs/              Narration, presentations, provenance, specification, and runbook
tests/             Cross-project policy and integrity checks
```

## Azure provisioning gate

No Azure workload resource may be provisioned until the user confirms the subscription name and ID and the target resource group is verified. Every resource-group-capable demo resource must explicitly target that group.

Current status: subscription `<AZURE_SUBSCRIPTION_NAME>` (`<AZURE_SUBSCRIPTION_ID>`) and existing resource group `<AZURE_RESOURCE_GROUP>` in East US are verified. The Frontier RM foundation, live web/API, managed-identity Azure OpenAI model, and authenticated Teams bot have been deployed with owner and expiry tags.

Live cockpit: `https://<RM_CONTAINER_APP_HOST>`

Guided EBC story: add `?present=1` to launch the seven-scene presenter experience. It includes continuous signal motion, client context, visible evidence stages, live Azure AI recommendation generation, grounded governance, RM approval, and end-of-day outcomes. Arrow keys navigate, Space pauses/resumes, and Escape closes.

The Teams sideload ZIP is `apps/teams/appPackage/build/frontier-rm.dev.zip`. Automated catalog upload is blocked because the signed-in Graph token lacks `AppCatalog.Submit` or `AppCatalog.ReadWrite.All`; use Teams **Apps > Manage your apps > Upload an app > Upload a custom app**, or obtain one of those delegated scopes.

Local implementation and validation do not require Azure.

## Run locally

The current vertical slice has no third-party runtime dependency:

```powershell
cd $HOME\Documents\Frontier-RM-Cockpit
python services/api/server.py
```

Open `http://127.0.0.1:8080`. The web cockpit and knowledge API use the same deterministic data and citation contract.

Run the validation suite with:

```powershell
python -m unittest discover -s tests -v
node --check apps/web/app-v2.js
az bicep build --file infra/api-app.bicep --stdout
python fabric/ontology/build_definition.py --check
```

## Live provider configuration

Mock mode is the default. After Azure provisioning is explicitly approved and completed, live mode can use managed identity with:

```text
FRONTIER_AI_MODE=azure
AZURE_OPENAI_ENDPOINT=https://<approved-resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=<approved-deployment>
```

The backend verifies TLS, constrains the model to the checked-in fictional knowledge, validates citation IDs, and falls back to deterministic mode if the live provider fails.

## Current implementation status

- Six-tab responsive cockpit plus persistent Frontier Copilot
- Seven-scene EBC presenter mode with continuous motion and direct scene controls
- Deterministic 20-client Fabric snapshot with four primary Singapore Premier story personas
- Schema-enabled Lakehouse with 21 Bronze, 21 Silver, and 12 Gold tables
- Direct Lake semantic model with 12 tables and 11 validated measures
- Fabric IQ Ontology definition with 15 entities, 13 relationships, and 15 bindings
- Published semantic-model-only Fabric Data Agent and four Microsoft Foundry agents
- Managed-identity Azure OpenAI generation with deterministic rehearsal fallback
- With Fabric IQ versus Without Fabric IQ artifact comparison
- CIO Houseview, activity evidence, candidate suppression, and paragraph-cited controls
- Authenticated Teams bot and captured agent-run transparency
- Production web/API image `frontier-rm-api:0.8.3`

The workstation currently cannot establish TLS with `registry.npmjs.org`. React/Vite and Agents Toolkit package scaffolding remain blocked; TLS verification has not been disabled. The current web implementation uses browser modules so product work and local validation can continue without unsafe network changes.
