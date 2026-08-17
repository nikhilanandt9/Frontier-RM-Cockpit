# Frontier RM End-to-End Demo Narration

## Presenter profile

- **Target duration:** 20-25 minutes
- **Primary audience:** Executive Briefing Centre visitors, business leaders, technology leaders, and control partners
- **Primary persona:** John Doe, fictional Singapore Premier relationship manager
- **Primary client:** Daniel Lim
- **Format:** Each section contains what to **Do**, what to **Say**, and the **Key point** to land
- **Production experience:** [Frontier RM Cockpit](https://<RM_CONTAINER_APP_HOST>)
- **Guided Story launch:** Add `?present=1` to the production URL

> Internal demonstration only. All clients, balances, products, market views, recommendations, and outcomes are fictional. Nothing in the experience constitutes financial advice, a suitability decision, legal advice, or proof of regulatory compliance.

## Timing budget

| Section | Target |
| --- | ---: |
| Opening and Guided Story | 2-3 minutes |
| Today | 2-3 minutes |
| Clients | 2-3 minutes |
| Opportunities | 5-6 minutes |
| Sources | 2 minutes |
| Operations | 3 minutes |
| Houseview | 3 minutes |
| Architecture and close | 1-2 minutes |
| **Total with interactions** | **20-25 minutes** |

## Pre-demo checklist

Complete these checks before the audience enters:

- Open the production cockpit and confirm the header says **Live - Azure AI**.
- Confirm the model badge in Opportunities says `gpt-4.1-mini · managed identity`.
- Select Daniel Lim and leave Opportunities in **With Fabric IQ** mode.
- Confirm the active Houseview is dated **19 August 2026**.
- Close Frontier Copilot so its opening is visible during the walkthrough.
- Use **Reset story** on Today if the day plan or prepared-state counters were changed during rehearsal.
- Keep a second browser tab open at the Guided Story URL.
- Keep deterministic **Rehearsal mode** available as the approved fallback.
- Allow the latest captured agent run to load before opening Operations.

## Opening frame

**Time:** 30-45 seconds

**Do**

Open the cockpit on Today. Do not click yet.

**Say**

> The question we are exploring today is simple: what would a day in the life of a relationship manager look like if the bank's data, knowledge, applications, and AI capabilities worked together as one intelligent system?
>
> This is John Doe, a fictional Premier relationship manager in Singapore. The objective is not to replace John's judgement. It is to give him a governed workspace that understands client context, identifies material needs, prepares evidence-backed actions, and keeps the human accountable at every decision point.
>
> I will start with the 60-second Guided Story. Then I will come back into the working application and show how every part of that story is produced.

**Key point**

This is a human-controlled operating model for relationship management, not an autonomous sales agent.

---

# Part 1: Guided Story

**Target time:** Approximately 2 minutes including the introduction and transition

## Guided Story controls

**Do**

Select **Start the guided story** or use the URL with `?present=1`.

The story advances automatically. Use:

- **Space** to pause or resume
- **Left/Right Arrow** to move between scenes
- The scene names across the top to jump directly
- **Escape** or the close button to return to the cockpit
- `?present=1&scene=3` to recover directly to the briefing scene

Pause only when the audience needs more time. The following narration is deliberately short enough to fit the automatic sequence.

## Scene 1: The day begins

**Visible duration:** About 6.5 seconds

**Say**

> At 8:30 in Singapore, John starts with 128 relationships, S$184.6 million in assets under care, and four material signals. The system has prioritised the day, but human judgement remains in control.

**Key point**

AI begins with workload prioritisation, not an unbounded client recommendation.

## Scene 2: Sources converge

**Visible duration:** About 8 seconds

**Say**

> Before John opens a client record, Fabric Client 360, lifecycle events, past correspondence, and meeting notes converge as cited context. Structured data and client voice arrive together instead of living in separate systems.

**Key point**

The system combines governed data with authored enterprise-style knowledge while preserving source provenance.

## Scene 3: Client 360

**Visible duration:** About 8 seconds

**Say**

> The first priority is Daniel Lim's 11:30 meeting. John sees the S$4.8 million relationship, portfolio composition, current profile, contact preference, and recent engagement in one individual Client 360.

**Key point**

The application gives the RM a decision surface, not another list of disconnected records.

## Scene 4: Briefing prepared

**Visible duration:** About 11 seconds

**Say**

> The first workflow artifact is a pre-meeting briefing. Fabric facts, past emails, meeting notes, and suitability boundaries are resolved into an objective, talk track, discovery questions, mandatory checks, and a client-appropriate opening. The wording is generated live by `gpt-4.1-mini`.

**Key point**

AI prepares the conversation using visible evidence and explicit boundaries.

## Scene 5: Recommendations

**Visible duration:** About 9 seconds

**Say**

> In the meeting, the system can compare fictional positioning candidates. Liquidity comes first; risks stay visible; alternatives are retained; and eligibility and suitability checks remain unresolved until John confirms them.

**Key point**

The output is decision support. It is not a suitability conclusion and cannot execute a transaction.

## Scene 6: Draft approved

**Visible duration:** About 7.5 seconds

**Say**

> After the meeting, the reviewed context becomes an editable client email and CRM opportunity draft. It is drafted, not sent. Nothing is committed until John reviews and approves later use.

**Key point**

The system accelerates follow-through without bypassing accountability or write controls.

## Scene 7: Day in motion

**Visible duration:** About 7.5 seconds

**Say**

> By the end of the day, progress is measured in prepared client needs, completed actions, time returned to John, and cited AI answers. This is bank data, knowledge, applications, and AI working as one governed system.

**Key point**

The desired outcome is better client coverage and preparation, not more AI activity.

## Transition to the cockpit

**Do**

Close the Guided Story. Return to Today.

**Say**

> That was the 60-second promise. Now let me show the working system behind each moment, starting with how John organises his day.

---

# Part 2: Working Cockpit

## Tab 1: Today

**Target time:** 2-3 minutes

### Morning portfolio pulse

**Do**

Point to the hero, morning portfolio pulse, and moving signal ticker.

**Say**

> Today is John's operational home. It opens with the portfolio pulse: Daniel's maturity is time-sensitive, Mei's profile refresh must happen before a portfolio discussion, and service windows have opened overnight.
>
> The signal stream keeps material client events visible as John moves through the application. The signals are fictional demonstration data, but they show how a working queue can continuously surface what deserves attention.

**Key point**

The system sequences work around client commitments, consent, and mandatory checks.

### Interactive metrics

**Do**

Open **Reviews due** or **Needs advanced**. Briefly scroll the report rows, point to the snapshot time, then close it.

**Say**

> These are not decorative KPI cards. Each metric opens a report-style view built from the same Fabric snapshot used elsewhere in the cockpit. John can move from the aggregate to the clients and actions behind it without changing applications.

**Key point**

Summary metrics and client workflow use one consistent data contract.

### One journey, three artifacts

**Do**

Point to the three workflow cards: **Prepare the client briefing**, **Shape custom recommendations**, and **Create the opportunity draft**.

**Say**

> The day is organised around a three-stage client journey: prepare before the meeting, decide with evidence in the meeting, and follow up through RM-approved drafts afterward. Each stage creates a usable artifact rather than another chat response.

### State and outcomes

**Do**

Select the next item in **Today's plan**. Let the completion state and metrics update. Point to **Client outcomes** and **Priority needs**.

**Say**

> When John completes real work, the day rebalances and the outcome measures move. Preparation state persists throughout the session. The cockpit therefore connects insight to action and action to visible progress.

**Optional capability callout**

Point to the **Live / Rehearsal** control.

> Live mode uses the managed-identity Azure AI service. Rehearsal mode uses deterministic output with the same safety contract, giving the presenter an operational fallback without changing the story.

**Transition**

> We have seen how the system prioritises John's portfolio. Now let us open the client context behind the first priority.

---

## Tab 2: Clients

**Target time:** 2-3 minutes

### Searchable Client 360

**Do**

Open **Clients**. Select Daniel Lim. Optionally type part of a client name or need in the search box, then clear it.

**Say**

> Clients gives John a searchable individual Client 360. Daniel's assets, portfolio allocation, relationship timeline, next meeting, profile status, consent, contact preference, and material signals are presented together.
>
> Household relationships may support the data model, but the user experience remains explicitly Client 360. The RM is preparing for an individual conversation.

### Risk and activity boundary

**Do**

Point to **Investment Risk Profile**, **Declared profile**, **Observed behaviour**, and **Latest activity evidence**.

**Say**

> There is an important control distinction here. Daniel's Investment Risk Profile is client-declared and adviser-confirmed. The Observed Behaviour Indicator is derived from recent fictional activity.
>
> Daniel's material equity sale can change the observed indicator and suggest a review. It does not silently rewrite his declared risk profile. That boundary is enforced in the data and displayed directly to John.

**Key point**

Observed behaviour is review evidence, not a replacement for client-confirmed risk tolerance.

### Meeting brief and journey handoff

**Do**

Select **Meeting brief**. Point to What changed and Recommended posture. Close it. Point to **Open journey**.

**Say**

> John can open a concise meeting brief or move directly into the governed opportunity journey. The handoff carries the selected client context with it, so he does not have to reconstruct the case.

### Copilot demonstration 1

**Do**

Open **Frontier Copilot**. Select the starter question **What should I review for Daniel Lim?**

**Say**

> Copilot is persistent across the cockpit rather than isolated in its own tab. Its starter questions adapt to the route and selected client. Answers are grounded in approved sources, include citations where available, and escalate when the approved knowledge base cannot support an answer.

Leave Copilot open briefly, then close it.

**Transition**

> Client 360 tells John what is known. Opportunity Studio turns that governed context into the three artifacts he needs before, during, and after the meeting.

---

## Tab 3: Opportunities

**Target time:** 5-6 minutes

This is the primary capability demonstration. Use Daniel Lim throughout.

### Explain the comparison

**Do**

Open **Opportunities**. Point to the comparison control beside `gpt-4.1-mini · managed identity`.

**Say**

> Here we can make the value of Fabric IQ visible. Both modes use the same `gpt-4.1-mini` deployment through managed identity. The variable is not the language model. The variable is the grounding envelope supplied to it.

### Without Fabric IQ

**Do**

Select **Without Fabric IQ**. Generate **Prepare briefing**. If time permits, continue to **Custom recommendations**.

While it runs, point to the preparation trace: basic client facts, generic need framing, mandatory safety checks, and general draft composition.

**Say**

> Without Fabric IQ, the model receives a deliberately shallow profile: basic client and opportunity facts plus mandatory safety boundaries. It can still produce a somewhat customised draft, and it is still constrained by human review and non-execution rules.

When the artifact appears, point to **General AI draft** and **No enterprise citations in general mode**.

> The result is useful as a starting point, but it cannot show enterprise provenance, the active CIO view, recent activity evidence, relationship context, or paragraph-mapped controls. Notice that the interface labels that limitation rather than allowing a generic answer to look fully grounded.

**Key point**

Without Fabric IQ is not presented as wrong or unsafe. It is visibly less informed and less explainable.

### With Fabric IQ

**Do**

Select **With Fabric IQ**. Generate the same stage. Continue through the three stages as time permits.

Point to the evidence trace: Fabric Client 360, enterprise sources and Houseview, activity and regulatory controls, and governed artifact design.

**Say**

> Now I will run the same client and stage with Fabric IQ. The same model receives governed Client 360, authored enterprise sources, the active Houseview, recent activity, semantic relationships, provenance, and deterministic control results.

When the briefing appears, point to:

- **Fabric IQ grounded**
- Meeting objective
- Client context and What changed
- Conversation talk track
- Discovery questions
- Suitability and compliance
- Editable opening
- Source citations

> The briefing is now a working pre-meeting artifact. It gives John an objective, what changed, a structured talk track, discovery questions, required checks, an editable opening, and direct source citations.

### Custom recommendations

**Do**

Open **Custom recommendations** and generate it. Point to the grounded positioning panel, fictional product candidates, risks, gates, unresolved items, suppressed-candidate strip, and control chips.

**Say**

> Stage two creates fictional positioning candidates. The deterministic advisory layer applies liquidity, risk, profile, activity, and control gates before Azure AI shapes the language.
>
> John can see why a candidate may fit, its intended role, objective and risk alignment, material risks, alternatives, and what remains unresolved. Candidates that fail a current gate are suppressed with a visible reason rather than quietly disappearing.
>
> This richer grounding enables a more tailored and explainable artifact. It does not make the recommendation automatically suitable or compliant. John still has to confirm the client facts and complete the applicable process.

### Why this?

**Do**

Select **Why this? View evidence and rationale**.

Point to Evidence used, Decision rules, Why this fits, Alternatives considered, Assumptions, Limitations, and Unresolved checks.

**Say**

> Why this exposes a concise public decision-support trace: the evidence used, the rules applied, alternatives, assumptions, limitations, and unresolved checks. It does not expose or request private model chain-of-thought.

Optionally open one source citation, Houseview section, or FAA-N16 control, then return to Opportunities.

### Opportunity draft

**Do**

Continue to **Create opportunity draft**. Point to the editable client email, CRM opportunity record, placeholders, disclosures, evidence IDs, mandatory checks, and approval button.

**Say**

> Stage three transforms the reviewed context into an editable client email and CRM opportunity record. Placeholders and disclosures remain visible. The draft carries its evidence forward, but it is not sent and it is not committed to CRM.
>
> Approval here means approved for later RM use. It does not trigger an external write or transaction.

### Mode isolation

**Do**

Switch briefly between **With Fabric IQ** and **Without Fabric IQ**.

**Say**

> Each client, comparison mode, and stage has its own artifact chain. Switching modes does not relabel or reuse an artifact from the other grounding envelope. That makes this a fair, inspectable comparison.

**Transition**

> We have followed citations from the generated artifact. Let us now look at the source library those citations resolve to.

---

## Tab 4: Sources

**Target time:** About 2 minutes

### Source explorer

**Do**

Open **Sources**. Demonstrate the **All**, **Mail**, and **Documents** segments and the client filter.

Open one Daniel email and one advisory document.

**Say**

> Sources provides the client correspondence and internal documents used in grounded preparation. John can filter by source type and client, then inspect the full authored item rather than relying on a detached excerpt.
>
> The reading pane preserves participants or author, timestamp or version, sensitivity, attachments, client association, and provenance. Stable source IDs allow an artifact citation to resolve back to this evidence.

### Truth boundary

**Say**

> These are authored fictional Outlook-style and SharePoint-style sources with realistic interaction patterns. There is no live Microsoft 365 tenant, mailbox, SharePoint retrieval, reply, send, upload, or document-write connection in this experience.

**Key point**

The demo proves the interaction and provenance contract without pretending that authored sources are live tenant data.

### Copilot demonstration 2

**Do**

Open Frontier Copilot and select **How should email evidence be used?**

**Say**

> The same Copilot conversation remains available here, while its suggested questions adapt to source governance. This is how knowledge assistance follows the RM's workflow instead of forcing the RM into a separate assistant experience.

Close Copilot.

**Transition**

> We have seen the RM-facing workflow. Operations lets us inspect how the deployed services and specialist agents support it without hiding the system boundaries.

---

## Tab 5: Operations

**Target time:** About 3 minutes

### Establish the three truth states

**Do**

Open **Operations** and point to the truth banner before interacting with the page.

**Say**

> Operations deliberately separates three different truth states. Connected-service health reflects deployed components. The moving signal feed is synthetic demonstration telemetry. The agent event stream is a replay of the selected captured operator run; it is not continuous live execution during this presentation.

**Key point**

The interface distinguishes live health, synthetic motion, and captured evidence instead of blending them into one ambiguous status.

### Connected services and architecture

**Do**

Point to the service list and architecture flow.

**Say**

> The deployed estate includes the web cockpit, managed-identity Azure OpenAI using `gpt-4.1-mini`, an active Fabric F4 capacity, the schema-enabled Frontier RM Lakehouse, an authenticated Teams bot, and a deterministic fallback.
>
> The application path is straightforward: RM cockpit, managed identity, grounded Azure AI preparation, and human review. Credentials and unrestricted source rows are not exposed to the presenter view.

### Captured runs

**Do**

Use the run selector to show:

1. The verified captured live run
2. The controlled revision-required run
3. The deterministic rehearsal capture

Return to the verified run.

**Say**

> The verified capture shows a successful authenticated operator execution. The controlled revision run proves that verification can reject an output when required evidence, such as consent, is missing. The rehearsal capture provides a deterministic fallback.

### Agent fleet and event stream

**Do**

Point to the four agents:

- RM Orchestrator
- Customer Intelligence
- Market Context
- Meeting Preparation

Open one agent tile, preferably Customer Intelligence or RM Orchestrator. Show Objective, Runtime Task Prompt, System Instructions, Shared Constraints, Input Context, Structured Output, and Workflow Handoff. Close it.

Expand an event or filter by an event type.

**Say**

> The specialist agents have visible operating contracts. We show their objectives, task summaries, shared constraints, accepted context, structured outputs, and handoffs. We do not expose verbatim private prompts, credentials, unrestricted rows, or hidden reasoning.
>
> The captured event stream shows observable plans, delegation, tool-call summaries, evidence IDs, outputs, and verification. The verified outcome remains marked ready for RM review, not ready for autonomous client communication.

### Fabric IQ and agent routing boundary

**Say**

> The published Fabric Data Agent currently uses the Direct Lake semantic model. Direct validated DAX remains authoritative for hidden identifiers and monetary values. The Ontology definition is deployed, but live graph traversal remains disabled pending graph-model readiness. We keep that limitation explicit rather than claiming a route that is not production-ready.

**Transition**

> The final tab shows how enterprise research, client risk evidence, and regulatory controls can be combined without collapsing them into a black-box recommendation.

---

## Tab 6: Houseview

**Target time:** About 3 minutes

### Research library

**Do**

Open **Houseview**. Point to the active and superseded reports. Select the active report if necessary.

**Say**

> The Houseview workspace contains two complete fictional CIO reports. The active tactical update is dated 19 August 2026; the earlier report remains available as superseded research.
>
> The report reader provides the executive summary, CIO stance, section-level market views, positioning language, risks, and stable citation IDs. It is a research source, not a live prediction engine or a recommendation by itself.

### Tailor to Daniel

**Do**

Select Daniel Lim in **Tailor to client**. Point to:

- Declared profile
- Observed behaviour
- Latest activity
- Retained candidates
- Suppressed candidates
- Regulatory controls

**Say**

> The client panel layers four contexts: Client 360, recent investment activity, the selected CIO Houseview, and applicable regulatory controls.
>
> Daniel's declared profile remains separate from the observed indicator derived from recent activity. The material sale affects the review evidence and liquidity picture; it does not rewrite the declared score.
>
> The deterministic layer shows which fictional candidates remain available for discussion and which are suppressed. John can inspect the exact reasons and open the relevant control rather than treating absence as unexplained model behaviour.

### Regulatory control detail

**Do**

Open an FAA-N16 control chip.

**Say**

> These controls use stable paragraph references from the internal `Frontier Regulatory Control Pack - FAA-N16 Demo Extract`. The pack is a curated demonstration aid. It is not the official notice, legal advice, a suitability determination, or proof of compliance. The authoritative notice and Compliance or Legal owners remain the source for interpretation.

### Optional Mei contrast

**Do**

If time permits, select Mei Tan and open the internal retirement enhanced-review control.

**Say**

> Mei demonstrates an additional internal safeguard. Retirement triggers enhanced review of current income, liquidity, commitments, objectives, horizon, risk capacity, and applicable knowledge or experience. This is not an MAS rule that automatically sets a retired client's risk score to one, and it is not a universal MAS prohibition on derivatives.

### Return to action

**Do**

Select **Tailor positioning in Opportunity studio**.

**Say**

> Research does not end in a static reader. The selected Houseview and client context can flow back into Opportunity Studio, where John reviews the evidence-backed positioning candidates and unresolved controls.

**Key point**

Houseview turns governed research into client-specific decision support while keeping market views, client risk, activity, and controls separately inspectable.

---

# Part 3: Architecture and Close

## Architecture summary

**Target time:** 60-90 seconds

**Say**

> Underneath the experience is a deployed Microsoft stack.
>
> Fabric holds a deterministic 20-client dataset in a schema-enabled Lakehouse. A notebook builds Bronze, Silver, and Gold layers. The Direct Lake semantic model exposes governed business entities and measures, with validated DAX used for authoritative values. A Fabric IQ Ontology definition models client, opportunity, activity, Houseview, and control relationships, while graph routing remains deliberately disabled until ready.
>
> A published Fabric Data Agent and four Microsoft Foundry agents support the captured preparation workflow. Azure OpenAI uses managed identity rather than embedded keys. The cockpit and APIs run in Azure Container Apps, an authenticated Teams bot provides an additional channel, and deterministic rehearsal remains available for resilience.
>
> Most importantly, the architecture preserves source provenance, deterministic controls, explicit limitations, and human review from beginning to end.

## Final close

**Time:** About 30 seconds

**Say**

> The value here is not another chatbot. It is a governed operating system for relationship-management work.
>
> Data establishes what is true. Knowledge adds client voice and enterprise context. Fabric IQ connects relationships, provenance, and controls. AI turns that context into usable preparation. Applications place it inside the RM's working day. And John remains responsible for the client conversation and every consequential action.
>
> That is what it looks like when the bank's data, knowledge, applications, and AI capabilities work together as one intelligent system.

---

# Presenter Fallbacks

## Azure generation is slow

**Do**

Narrate the visible evidence trace while generation continues. If it does not return promptly, switch to **Rehearsal mode** and regenerate.

**Say**

> The live wording service is taking longer than expected, so I will use the deterministic rehearsal engine. It preserves the same artifact structure, evidence contract, controls, and human-review boundaries.

Do not imply the deterministic result is a captured Azure response.

## A source citation does not open

Navigate directly to Sources, filter to Daniel, and open an email or document manually.

**Say**

> I will open the same authored source directly from the library. The important contract is that generated artifacts retain stable evidence IDs and resolve only to allowlisted source content.

## Captured agent replay is unavailable

Stay on Connected services and explain the three truth states. Do not describe the animated telemetry as an agent run.

**Say**

> The captured replay is unavailable in this browser session. Service health remains live, while the moving feed is synthetic demonstration telemetry. I will not conflate either with a live agent execution.

## Houseview advisory context is slow

Narrate the report reader first. Return to Daniel after the client panel loads. If necessary, demonstrate the already-generated Fabric IQ recommendation in Opportunities.

## Guided Story is interrupted

Use the scene buttons or Arrow keys. For the briefing scene, reopen with `?present=1&scene=3`.

## Reset between rehearsals

Use **Reset story** on Today. This clears prepared artifacts, agenda progress, drafts, Copilot messages, and generated journey artifacts for the browser session.

---

# Shortened 12-15 Minute Route

Use this route when the agenda is compressed. It still touches every tab.

1. **Guided Story:** Run the complete 60-second sequence.
2. **Today:** Open one metric and point to the three-stage journey. Do not update the agenda.
3. **Clients:** Show Daniel's Client 360 and the declared-versus-observed risk boundary.
4. **Opportunities:** Make this the focus. Compare one recommendation Without Fabric IQ and With Fabric IQ, open Why this, then show the opportunity draft without editing it.
5. **Sources:** Open one cited source and state the authored-content boundary.
6. **Operations:** State the three truth modes, show one captured run, and open one agent contract.
7. **Houseview:** Show the 19 August active report, Daniel's retained/suppressed candidates, and one control.
8. **Copilot:** Ask one contextual question from any route.
9. **Close:** Use the 30-second final message.

Skip the optional Mei contrast, detailed metric rows, event filtering, and the extended architecture inventory.

---

# Claims and Phrases to Avoid

Do not say:

- "This is reading live Outlook or SharePoint." The sources are authored fictional demonstration content.
- "These agents are executing live right now." Operations replays a selected captured run.
- "The signal animation is live bank telemetry." It is synthetic demonstration telemetry.
- "This shows the model's chain-of-thought." It shows public evidence, rules, rationale, assumptions, limitations, and unresolved checks.
- "Fabric IQ makes the recommendation correct, suitable, or compliant." It supplies richer governed context, provenance, relationships, and deterministic controls.
- "The system recommends or executes a transaction." It creates fictional positioning candidates for discussion.
- "The email was sent" or "the CRM record was committed." Both remain editable drafts.
- "Recent trades changed the client's risk profile." Activity changes only the observed indicator and review status.
- "MAS requires retirees to have risk score one" or "MAS bans derivatives for retirees." Retirement enhanced review is an internal safeguard.
- "The internal control pack is the official MAS notice." It is a curated demo extract and not legal advice.
- "The Ontology is actively traversed by the Data Agent." The definition is deployed, but graph routing remains disabled pending readiness.

Prefer:

- "Evidence-backed and human-reviewed"
- "Fictional positioning candidate"
- "Compliance-aware control"
- "Public evidence-and-rationale trace"
- "Captured live run replay"
- "Authored Outlook-style or SharePoint-style source"
- "Observed behaviour triggered review; declared profile remained unchanged"
- "Richer governed context, provenance, relationships, and controls"

---

# Final Rehearsal Checklist

- The Guided Story completes without clipping the narration.
- Daniel remains selected across Clients, Opportunities, and Houseview.
- Without Fabric IQ shows **General AI draft** and no enterprise citations.
- With Fabric IQ shows source citations, Houseview context, activity, controls, and suppressed candidates.
- Why this opens the public rationale dialog.
- The opportunity email and CRM artifacts remain visibly uncommitted.
- Sources show authored provenance and no write controls.
- Operations loads the verified, revision-required, and rehearsal captures.
- At least one agent operating contract opens successfully.
- Houseview displays **19 August 2026** for the active report.
- At least one FAA-N16 control opens successfully.
- Copilot answers one contextual question and shows its citation or escalation state.
- The final narration stays within 20-25 minutes.
