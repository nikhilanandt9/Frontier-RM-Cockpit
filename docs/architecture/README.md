# Frontier RM logical architecture

## Files

- `frontier-rm-logical-architecture.svg` — editable 16:9 vector source.
- `frontier-rm-logical-architecture.png` — presentation-ready 1920×1080 render.
- `frontier-rm-ai-factory-building-blocks.svg` — editable layered framework covering the demo and wider Microsoft ecosystem.
- `frontier-rm-ai-factory-building-blocks.png` — presentation-ready 4K render of the layered framework.
- `frontier-rm-moments-services.svg` — editable five-stage RM workflow with demo activities and Microsoft services.
- `frontier-rm-moments-services.png` — presentation-ready 4K render of the activity and services workflow.
- `frontier-rm-moments-security.svg` — editable five-stage workflow with an additional security and governance layer.
- `frontier-rm-moments-security.png` — presentation-ready 4K render of the secured and governed workflow.
- `../../scripts/render_logical_architecture.ps1` — reproducible SVG-to-PNG renderer.

The PNG is designed for the reference-architecture placeholder on slide 38 of `../Frontier_RM_Microsoft_Data_M365_A365_IQ_EBC.pptx`.

## Logical zones

1. **Channels and people:** Browser-based Frontier RM cockpit, authenticated Microsoft Teams bot, and human-approved RM artifacts.
2. **Azure application tier:** Azure Container Apps for the Web/API and Teams bot, user-assigned managed identity, Azure Container Registry, Application Insights, and Log Analytics.
3. **AI and orchestration:** Azure OpenAI `gpt-4.1-mini`, four Microsoft Foundry agents, and deterministic advisory/verification controls.
4. **Microsoft Fabric and Fabric IQ:** OneLake Lakehouse medallion tables, Direct Lake Semantic Model, Power BI, Fabric Data Agent, and the deployed Ontology definition.

## Flow boundaries

- **Solid blue:** Interactive runtime requests. The Web/API uses deterministic baselines and Azure OpenAI wording.
- **Dashed purple:** Captured operator workflow through the Fabric Data Agent and Microsoft Foundry agents. Operations replays these captures; it does not continuously execute agents.
- **Dotted teal:** The validated Fabric snapshot packaged with the API so the EBC remains available without a live SQL query per page load.
- **Dotted magenta:** Deferred Ontology graph route. The Ontology definition is deployed and validated, but graph routing is not currently enabled.

Authored Outlook-style correspondence, SharePoint-style documents, CIO Houseviews, and the FAA-N16 demo control pack are fictional read-only demonstration sources. The application does not send email, write documents, transact, or commit CRM records.

## RM workflow variants

Both workflow diagrams preserve the same five stages:

1. **Triage:** Today prioritizes client needs, reviews, and material signals.
2. **Understand:** Client 360 and Sources connect profile, activity, and client voice.
3. **Prepare:** Foundry agents and Azure OpenAI prepare the briefing, talk track, and questions.
4. **Decide:** Fabric IQ, the Semantic Model, Houseview, and deterministic gates support explainable candidate comparison.
5. **Follow up:** The cockpit creates editable email and CRM drafts for RM approval.

The security variant adds stage-specific controls. Entra ID, managed identity, scoped tools, structured-output validation, deterministic gates, and Azure Monitor telemetry reflect the implemented design. Purview, Defender/DLP, Dynamics 365, and Power Automate are labeled as wider Microsoft options rather than active demo integrations.

## Regenerate

```powershell
pwsh -NoProfile -File .\scripts\render_logical_architecture.ps1
pwsh -NoProfile -File .\scripts\render_logical_architecture.ps1 `
	-Source .\docs\architecture\frontier-rm-ai-factory-building-blocks.svg `
	-Output .\docs\architecture\frontier-rm-ai-factory-building-blocks.png `
	-Width 3840 -Height 2160
pwsh -NoProfile -File .\scripts\render_logical_architecture.ps1 `
	-Source .\docs\architecture\frontier-rm-moments-services.svg `
	-Output .\docs\architecture\frontier-rm-moments-services.png `
	-Width 3840 -Height 2160
pwsh -NoProfile -File .\scripts\render_logical_architecture.ps1 `
	-Source .\docs\architecture\frontier-rm-moments-security.svg `
	-Output .\docs\architecture\frontier-rm-moments-security.png `
	-Width 3840 -Height 2160
```