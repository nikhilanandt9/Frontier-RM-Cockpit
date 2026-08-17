# Deployment runbook

## Verified Azure context

- Subscription: `ME-MngEnvMCAP242401-taner-1`
- Subscription ID: `7ad80d1b-c23b-46cf-baa5-64c6d6bccbbe`
- Resource group: `Nikhil-FabricIQ`
- Region: East US
- Fabric data-plane region: Australia East
- Owner tag: `fsi-ebc-nikhil-frontier-rm`
- Expiry tag: `2026-09-12`

## Live endpoints

- Cockpit and API: `https://ca-frontier-rm-api-kqo7o4bgpiiay.greensea-544a6a70.eastus.azurecontainerapps.io`
- Guided story: append `?present=1`
- Direct rehearsal scene: append `?present=1&scene=3` for the AI evidence scene
- API health: `/api/health`
- Privacy: `/privacy`
- Terms: `/terms`
- Teams bot health: `https://ca-frm-teams-kqo7o4bg.greensea-544a6a70.eastus.azurecontainerapps.io/health`
- Teams messaging endpoint: `https://ca-frm-teams-kqo7o4bg.greensea-544a6a70.eastus.azurecontainerapps.io/api/messages`

## Fabric estate

- Capacity: `fcfrontierrmebckqo7o4bg`
- SKU/state: F4 / Active
- Fabric capacity ID: `f75073ec-d316-468f-a4e1-6e41485ee1d8`
- Workspace: `Frontier-RM-EBC`
- Workspace ID: `67764587-fefa-43e9-ad2e-66b47e7ea18d`
- Lakehouse: `FrontierRMLakehouse` (schema-enabled)
- Lakehouse ID: `a86aee8e-0382-4105-bd78-457af69d8830`
- SQL endpoint ID: `2f79be46-0e91-46ef-9810-ffebab93b253`
- Bronze landing: `Files/bronze/landing/seed=20260812`
- Landed snapshot: 22 files, 123,908 bytes, 399 normalized rows
- Medallion notebook: `01 Build Frontier RM Medallion`
- Notebook ID: `264a5fb9-1c3e-4655-b21f-792049fdf121`
- Build job: `2e96cf00-4d18-4f2d-ba9b-ddab1f6a1e80` / Completed
- Delta tables: 21 Bronze, 21 Silver, 12 Gold
- Gold tables: `customer_360`, `portfolio_exposure`, `maturity_watchlist`, `engagement_gap`, `compliance_due`, `rm_opportunity_snapshot`, `meeting_context`, `client_advisory_context`, `client_activity_evidence`, `houseview_document_index`, `regulatory_control_register`, `recommendation_grounding_context`
- Semantic model: `Frontier RM Semantic Model`
- Semantic model ID: `bc44b3b5-5275-4810-93a7-251f76cc9235`
- Storage mode: Direct Lake
- Model validation: 12 tables, 11 measures, 20 customers, S$9.31M opportunity pipeline, 7 compliance reviews, 2 risk reviews, 20 material activities, 1 active Houseview, S$37.225M portfolio value, and S$650K maturing value

The portal dashboard serves the checked-in, byte-validated Fabric snapshot from `packages/fabric-data/generated`. This is the same normalized 20-customer dataset uploaded to the Lakehouse, adapted into the browser contract at API startup. It deliberately does not issue a live SQL query on every page load, so the EBC remains available when Fabric is paused or temporarily unavailable. Regenerate, validate, upload, and redeploy the snapshot when Fabric source data changes.

The web/API remains in East US. Fabric is in Australia East because this subscription had 0 CU East US quota and 508 CU available in Australia East when F4 was provisioned. Keep future Foundry/Fabric agent resources in Australia East where supported, and account for the cross-region application boundary.

## Agent run replay

Operations reads validated bundles from `packages/demo-data/agent-runs`. The newest Daniel Lim bundle is a **Captured live run** produced by an authenticated operator execution across the published Fabric Data Agent, direct semantic-model DAX validation, and four Foundry agents. The presenter can select this verified capture, a captured revision run proving the verifier rejects missing consent evidence, or the deterministic rehearsal fallback.

The selected agent run is a replay, not continuous execution. Service-health rows describe deployed components, while the animated signal stream is synthetic demonstration telemetry. Agent tiles expose only the presenter-safe catalog from `/api/agents`; never add raw runtime prompts, credentials, hidden reasoning, sensitive headers, or unrestricted source rows to that endpoint.

The Data Agent currently uses only `Frontier RM Semantic Model`. Ontology routing is disabled because the generated graph model isn't query-ready. The operator runner uses the Data Agent for visible categorical context and direct validated DAX for hidden identifiers, causal event linkage, and monetary values. This avoids relying on the Data Agent's known incorrect currency rendering while preserving governed Fabric provenance.

Displayed events may include plans, delegation, tool-call summaries, evidence IDs, outputs, statuses, and verification. Never include access tokens, raw prompts, hidden chain-of-thought, sensitive headers, or unrestricted source rows.

## Authored Microsoft 365-style sources

`packages/demo-data/sources.json` supplies read-only fictional Outlook-style correspondence and SharePoint-style documents for the Sources view and three-stage opportunity artifacts. `/api/sources` supports only list/filter reads, and `/api/sources/{id}` resolves allowlisted source IDs. There are no mailbox, Microsoft Graph, SharePoint, reply, send, upload, or document-write operations.

The global internal-demo banner and each item's provenance preserve the authored-data boundary. Keep realistic interaction design, but do not add live-connect claims, real email domains, tenant identifiers, or controls that imply a message was sent or a CRM record was committed.

## CIO Houseview and regulatory controls

- Canonical Houseview content: `packages/demo-data/houseview/houseviews.json`
- Readable PDFs: `Files/houseview/houseview-2026-h2.pdf` and `Files/houseview/houseview-2026-q4.pdf`
- Canonical regulatory controls: `packages/demo-data/regulatory/faa_n16_control_pack.json`
- Readable control pack: `Files/regulatory/frontier_faa_n16_demo_control_pack.pdf`

The active `houseview-2026-q4` report is dated `2026-08-19`; the Houseview header and Sources research library both derive from this canonical metadata after the Fabric snapshot is regenerated and deployed.

The PDFs and corresponding deterministic tables are authored fictional demonstration content. The control pack uses selected FAA-N16 paragraph IDs but does not reproduce official styling, use an MAS logo, provide legal advice, or certify compliance.

The deterministic advisory engine selects and suppresses candidates before Azure OpenAI wording. It keeps declared risk profile history separate from activity-derived observed behaviour. Retirement invokes `INTERNAL-RETIREMENT-ENHANCED-REVIEW`; this must never be described as an MAS automatic risk-score rule.

Read-only APIs:

- `/api/houseview` and `/api/houseview/{reportId}`
- `/api/clients/{clientId}/advisory-context`
- `/api/regulatory-controls` and `/api/regulatory-controls/{ruleId}`

There are no public score-update, report-upload, recommendation-execution, transaction, email-send or CRM-commit endpoints.

## Teams sideload

Package: `apps/teams/appPackage/build/frontier-rm.dev.zip`

SHA-256: `ED33CC3286E522610D14D5846DC973EA9C2FEEDD6A6392FE2EEA775B53247B86`

1. Open Microsoft Teams in the target tenant.
2. Select **Apps**, then **Manage your apps**.
3. Select **Upload an app** and **Upload a custom app**.
4. Choose `frontier-rm.dev.zip`.
5. Add **Frontier RM** to the personal scope and send a grounded process question.

If custom app upload is unavailable, a Teams administrator must enable the tenant custom-app policy or upload the package in Teams Admin Center. Automated Microsoft Graph upload requires delegated `AppCatalog.Submit` or `AppCatalog.ReadWrite.All`; the current Azure CLI token does not have either scope.

## Validation evidence

- Web page, privacy, and terms return HTTP 200.
- Azure OpenAI provider returns grounded responses with stable citation IDs.
- Azure OpenAI generates a structured meeting pre-brief with objective, context, talk track, discovery questions, allocation themes, suitability checks, unresolved items, follow-up actions, four visible evidence stages, and deterministic fallback.
- Unit Trust content is conversation preparation only: no named fund, suitability conclusion, guaranteed return, or transaction instruction.
- Today exposes four report-style metric dialogs and four RM workflow journeys.
- Operations exposes selectable captured runs and presenter-safe details for all four agents.
- Frontier Copilot persists as a collapsible right-side panel across every view.
- Sources provides six authored Outlook/SharePoint-style items across three fictional clients with stable citations.
- Opportunities provides briefing, fictional-product recommendation, and email/CRM draft actions with public evidence-and-rationale traces.
- Opportunities defaults to **With Fabric IQ** and offers a **Without Fabric IQ** comparison beside the shared `gpt-4.1-mini · managed identity` badge. Artifacts are isolated by client, mode and stage. General mode excludes enterprise citations, Houseview, activity and regulatory-control context while retaining mandatory human review and non-execution boundaries.
- Client presentation uses Client 360 only; Household 360 is not shown.
- The Today heading and shared `Live` page badge resolve the current calendar date and time in `Asia/Singapore` when the URL loads; Fabric snapshot labels retain their historical timestamp.
- The guided story has seven timed scenes with pause, resume, previous, next, direct-scene, keyboard and restart-safe controls.
- Model: `gpt-4.1-mini`, version `2025-04-14`, GlobalStandard capacity 10.
- API and Teams Container App revisions are healthy with one replica.
- API image: `frontier-rm-api:0.8.2`
- API image digest: `sha256:712242625b8ce426e60e2a5bcc0bde02bc0ababfe30ba88fe393e172088a6edb`
- API revision: `ca-frontier-rm-api-kqo7o4bgpiiay--0000012`, healthy with one replica and 100% traffic
- Foundry Customer Intelligence: `frontier-customer-intelligence:3`, with the `frontier-rm-fabric` project connection.
- Captured-live default: `run-daniel-lim-live-20260812173016-success`; controlled revision: `run-daniel-lim-live-20260812172824-revision`.
- Teams bot uses a user-assigned managed identity and rejects unauthenticated messages with HTTP 401.
- Azure Bot Teams channel is enabled and points to the deployed HTTPS endpoint.
- Fabric F4 is active and the dedicated workspace is assigned to it.
- The schema-enabled Lakehouse SQL endpoint is provisioned and the Bronze landing path matches local file counts and bytes.
- The medallion notebook completed without a failure reason; every expected Delta table root has a `_delta_log` in OneLake.
- SQL row-count validation remains pending registration of the `fabric-sqlendpoint-execute_query` MCP server in this VS Code host. The completed notebook assertions verified 20 customers, Daniel's meeting context, and Mei's compliance row.

## Teardown

All Azure workload resources are tagged `workload=frontier-rm-cockpit` and `expiry=2026-09-12`. Pause or delete only `fcfrontierrmebckqo7o4bg` after unassigning or relocating `Frontier-RM-EBC`. Review and remove only resources with those tags; do not delete the shared `Nikhil-FabricIQ` resource group without confirming ownership of any later workloads.