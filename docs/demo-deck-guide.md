# Frontier RM unified deck guide

## Canonical presentation

Use these files for the EBC presentation:

- `Frontier_RM_Microsoft_Data_M365_A365_IQ_EBC.pptx` — canonical editable 40-slide deck.
- `Frontier_RM_Microsoft_Data_M365_A365_IQ_EBC.pdf` — shareable PDF export.
- `deck-preview-unified/` — PNG rendering of all 40 slides.
- `../scripts/generate_unified_demo_deck.ps1` — reproducible PowerPoint generator.
- `../scripts/validate_unified_demo_deck.ps1` — structural, notes, screenshot-zone, count, and claim validator.
- `source-deck-inventory.json` — read-only inventory of the two source decks.
- `../scripts/inspect_source_decks.ps1` — source-deck inventory generator.

The previous `Frontier_RM_Intelligent_System_Demo*.pptx` decks remain reference and rollback artifacts. They are superseded for presentation use and are not deleted.

The presenter narration remains available in `end-to-end-demo-narration.md` and `Frontier_RM_End_to_End_Demo_Narration.pdf`.

## Story structure

1. **Slides 1–2:** Introduction and agenda
2. **Slides 3–14:** Day in the life of an RM
3. **Slides 15–22:** Microsoft Data and Azure
4. **Slides 23–31:** Microsoft 365 and Agent 365
5. **Slides 32–38:** Fabric IQ and governed agents
6. **Slides 39–40:** Closing and next steps

| Section | Time |
| --- | ---: |
| Opening and agenda | 2 minutes |
| RM day and live demonstration | 10–12 minutes |
| Microsoft Data and Azure | 4–5 minutes |
| Microsoft 365 and Agent 365 | 4–5 minutes |
| Fabric IQ, architecture, and governance | 5–6 minutes |
| Close | 1–2 minutes |

For a live-demo-led session, switch to the cockpit after slide 6 and return at slide 14 or 15. For a deck-led session, use slides 7–13 as screenshot-supported walkthroughs.

## Source-deck treatment

The unified deck restyles concepts from two read-only source decks:

- `C:\Users\anandnikhil\Downloads\Fabric IQ L100 Pitch Deck.PPTX`
- `C:\Users\anandnikhil\Downloads\NewPresentation_v1.pptx`

| Unified topic | Source concepts |
| --- | --- |
| Fragmented meaning and AI context gap | Fabric IQ L100 slides 7–13 |
| Microsoft Fabric unified platform | Fabric IQ L100 slides 14–15; NewPresentation slide 5 |
| OneLake and open data | NewPresentation slides 6–8 |
| Semantic models and trusted meaning | NewPresentation slide 10; Fabric IQ L100 slide 32 |
| Fabric IQ definition and benefits | Fabric IQ L100 slides 17–24 |
| Ontology and graph concepts | Fabric IQ L100 slides 32–34 |
| Fabric Data Agents | Fabric IQ L100 slide 36 |
| Microsoft IQ and work context | NewPresentation slides 3–4 and 23–24 |
| Microsoft 365 Frontier Suite and Copilot | NewPresentation slides 20–22 |
| Agent 365 framing | NewPresentation slides 19–22, expanded into a capability/control-plane section |

Selected concepts were rebuilt in the Frontier visual language rather than pasted unchanged. Duplicate agendas, customer-specific content, unsupported roadmap material, and source branding were excluded.

## Screenshot checklist

The deck contains 18 labeled native screenshot zones named `SCREENSHOT_ZONE_Sxx`.

| Slide | Screenshot to add |
| ---: | --- |
| 6 | Guided Story opening or seven-scene montage |
| 7 | Today page: pulse, metrics, workflow cards, and plan |
| 8 | Daniel Lim Client 360 with declared/observed risk evidence |
| 10 | Without Fabric IQ artifact |
| 10 | With Fabric IQ artifact |
| 11 | Authored Sources reading pane |
| 11 | Persistent Frontier Copilot panel |
| 12 | CIO Houseview and selected-client advisory context |
| 13 | Operations agent fleet, captured run, event stream, and outcome |
| 20 | Fabric workspace, Lakehouse, medallion notebook, or tables |
| 21 | Direct Lake semantic model, Power BI view, or DAX validation |
| 26 | Microsoft 365 Outlook/SharePoint work-context view |
| 26 | Teams bot or Copilot delivery view |
| 28 | Agent 365 registry or agent identity inventory |
| 30 | Agent 365 observability, evaluation, or lifecycle view |
| 34 | Fabric IQ Ontology definition, entity map, or graph view |
| 37 | Fabric Data Agent, Foundry project, or verified Agent 365 evidence |
| 38 | Detailed end-to-end reference architecture |

To replace a zone:

1. Insert and crop the screenshot to the dashed zone.
2. Send it behind the colored placeholder label if retaining the label helps.
3. Delete the dashed rectangle and instruction text.
4. Keep the slide title and adjacent callouts.
5. Recheck the slide in Presenter View at 16:9.

## Agent 365 evidence gate

The Frontier inventory verifies four Microsoft Foundry agents, a semantic-model-only Fabric Data Agent, managed-identity Azure OpenAI, an authenticated Teams bot, and captured-run replay.

It does not yet contain Agent 365 tenant, registry, control-plane, identity, or observability evidence. Agent 365 slides therefore use **capability**, **target control plane**, or **evidence pending** wording.

Before changing those slides to `deployed`, `registered`, or `managed`, add:

- Agent 365 tenant or control-plane name.
- Registered agent IDs.
- Registry or identity screenshot.
- Observability or lifecycle screenshot.
- Deployment-inventory update identifying the Agent 365 resources.

Do not relabel Foundry agents or the Fabric Data Agent as Agent 365-managed without this evidence.

## Verified Frontier facts

- 20 fictional customers and 399 deterministic rows.
- 21 Bronze, 21 Silver, and 12 Gold Delta tables.
- 12 Direct Lake semantic-model tables and 11 measures.
- 15 Ontology entities, 13 relationships, and 15 bindings.
- Active Houseview dated 19 August 2026.
- Ontology definition deployed and readback-validated.
- Ontology graph routing disabled pending readiness.
- Four Foundry agents and a semantic-model-only Fabric Data Agent.
- Production application image `0.8.0`.

## Truth boundaries

- Broader Azure, Microsoft 365, Agent 365, and Purview slides describe Microsoft capabilities unless explicitly labeled as deployed.
- Outlook and SharePoint-style sources are authored fictional content, not live Microsoft 365 retrieval.
- Operations separates live health, synthetic telemetry, and captured replay.
- Public evidence and rationale are shown; private chain-of-thought is not.
- Fabric IQ adds context, relationships, provenance, and controls; it does not guarantee suitability or compliance.
- Email and CRM artifacts are drafts; nothing is sent or committed.
- Activity can change observed behaviour and trigger review, but cannot silently change declared risk.
- Retirement enhanced review is an internal safeguard, not an automatic MAS score rule.
- The Ontology definition is deployed, but live graph traversal is not claimed.

## Regenerate and validate

```powershell
.\scripts\inspect_source_decks.ps1
.\scripts\generate_unified_demo_deck.ps1
.\scripts\validate_unified_demo_deck.ps1
```

Regeneration replaces the canonical PPTX, PDF, and PNG previews. Add screenshots after final generation, or save a separate customized copy first.

The validator expects 40 slides, notes on all 40, 18 screenshot zones, 40 previews, current deployment counts, and no stale or unsupported claims.