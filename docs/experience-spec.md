# Frontier RM experience specification

## Audience and setting

The primary persona is John Doe, a fictional Singapore Premier relationship manager preparing for and moving through a working day. The experience is designed for an internal Executive Briefing Centre presentation and uses English, Singapore time, and SGD.

## Navigation

1. **Today** presents the morning portfolio pulse, four common RM workflows, an ordered action plan, and report-style metric drilldowns.
2. **Clients** provides a searchable individual Client 360. Household data may support backend relationships but is not presented as a separate 360 concept.
3. **Opportunities** guides the RM through three sequential artifacts: client briefing, custom fictional-product recommendations, and an editable client-email plus CRM opportunity draft. A segmented comparison control beside the model badge switches between Fabric IQ-grounded and general AI artifacts.
4. **Sources** provides a realistic read-only view of authored Outlook-style correspondence and SharePoint-style documents used as cited context.
5. **Operations** separates synthetic signal telemetry from connected-service health and selectable captured agent runs. It provides a transparent review of agent plans, delegation, tool calls, evidence, outputs, verification, and presenter-safe operating contracts.
6. **Houseview** is a secondary CIO research storyline combining full fictional market reports, Client 360, recent investment activity, declared and observed risk, and paragraph-cited regulatory controls.

Frontier Copilot is a persistent collapsible right-side panel available from every navigation view. It retains conversation state across routes and provides grounded process answers with approved citations and escalation boundaries.

## Visual system

- White is the dominant workspace and panel surface.
- Approved red is reserved for active navigation, primary commands, selection, and branded moments.
- Charcoal carries headings and body text; neutral greys establish hierarchy.
- Green, amber, and blue communicate semantic status and are never replaced with decorative red.
- Panels are compact and operational. Charts and controls remain stable at desktop, presentation, and mobile sizes.
- The interface uses original typography, spacing, motion, and composition.

## Demonstration sequence

1. Triage the morning portfolio and select a client journey.
2. Review Fabric Client 360 facts together with past authored emails and meeting notes.
3. Generate the pre-meeting briefing, including objective, what changed, talk track, questions, sources, and mandatory checks.
4. Generate custom recommendations using explicitly fictional product candidates, with fit rationale, risks, alternatives, evidence, and suitability gates.
5. Open “Why this?” to review public evidence and rationale. Private model chain-of-thought is never requested or displayed.
6. Generate an editable client email and CRM opportunity draft. Review placeholders and checks; nothing is sent or committed.
7. Inspect each agent's operating contract and compare verified, revision-requested, and rehearsal captures in Operations.
8. Use Frontier Copilot from any page and demonstrate escalation outside the approved knowledge base.

## RM journey

The comparison uses the same `gpt-4.1-mini` deployment in both modes and defaults to **With Fabric IQ**. Fabric IQ mode includes governed Client 360, authored enterprise sources, Houseview, activity evidence, semantic relationships, provenance and deterministic regulatory controls. Without Fabric IQ receives only a shallow client and opportunity profile, returns no enterprise citations, and keeps each stage explicitly labeled **General AI draft**. Generated stages are isolated by client, mode and action so switching modes never relabels or reuses an artifact from the other grounding envelope. Guided Story always uses Fabric IQ mode.

- **Prepare briefing** combines Fabric evidence, authored correspondence, meeting notes, consent, and process boundaries before the meeting.
- **Custom recommendations** compare explicitly fictional products against objectives, liquidity, horizon, holdings, and risk while retaining unresolved suitability gates.
- **Create opportunity draft** converts the reviewed solution into editable client-email and CRM artifacts for John Doe's approval. It does not send or commit either artifact.

Every stage provides an evidence-and-rationale view containing source citations, public decision rules, fit rationale, alternatives, assumptions, limitations, and unresolved checks. This is decision support rather than private chain-of-thought.

## Source truth

Fabric Client 360, semantic-model evidence, and captured agent runs retain their existing deployed or captured-live status. Outlook-style email threads and SharePoint-style documents are authored fictional demonstration context served from the checked-in source catalog. They have realistic interaction patterns but no Microsoft 365 tenant, mailbox, SharePoint site, authentication, retrieval, or write connection.

## Houseview and regulatory storyline

The Houseview experience reads two complete fictional CIO reports. The active report is dated 19 August 2026. It does not claim a live CIO feed or a prediction engine. Report sections have stable citation IDs and are stored as full PDFs plus retrievable metadata/sections in Fabric.

Client risk uses two separate concepts:

- **Investment Risk Profile Score (1–5):** client-declared and adviser-confirmed, with an effective date and review history.
- **Observed Behaviour Indicator (1–5):** calculated from recent fictional investment activity and used only as review evidence.

Activity never updates the declared score. A material buy or sell can change the observed indicator and set `review-suggested` or `review-required`. The rationale states the triggering activity and confirms whether the declared profile changed.

Retirement triggers an internal enhanced review of current income, liquidity, commitments, objectives, horizon, risk capacity and applicable knowledge/experience. This is not presented as an MAS rule that retirees must have score 1, nor as a universal MAS derivatives prohibition. Complex candidates are suppressed until applicable evidence and controls are complete.

The internal `Frontier Regulatory Control Pack — FAA-N16 Demo Extract` cites selected paragraphs of the attached Notice on Recommendations on Investment Products, issued 28 July 2011 and last updated 29 December 2025. It is not the official notice, legal advice, a suitability determination or proof of regulatory compliance.

Today's four metrics are interactive controls. Each opens an accessible modal report with a snapshot timestamp, a relevant breakdown, and client or action rows. These reports use the same checked-in Fabric snapshot and session preparation state as the rest of the cockpit.

## Agent transparency

The Operations view exposes structured agent events rather than hidden chain-of-thought. It shows four workers: RM Orchestrator, Customer Intelligence, Market Context, and Meeting Preparation. Each agent tile opens a presenter-safe operating contract covering its objective, runtime task summary, system-instruction summary, shared constraints, input context, structured output, and workflow handoff. Verbatim private prompts, credentials, unrestricted rows, and hidden reasoning are not presented.

The default Operations view is labeled **Captured live run** and shows a sanitized authenticated operator execution across Fabric and Foundry with capture and data-snapshot timestamps. A run selector exposes the verified capture, controlled revision run, and deterministic rehearsal. The cockpit replays the selected bundle and does not invoke Fabric continuously during the EBC session. The animated signal stream is separate synthetic demo telemetry. Ontology traversal is deferred until its generated graph model is repaired; current captured evidence uses the published semantic-model-only Data Agent plus direct validated DAX.
