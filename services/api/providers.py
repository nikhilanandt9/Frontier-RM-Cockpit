from __future__ import annotations

import json
import os
import ssl
import time
from dataclasses import dataclass
from typing import Protocol
from urllib import error, parse, request


class KnowledgeProvider(Protocol):
    name: str

    def answer(self, question: str, knowledge: list[dict]) -> dict: ...


JOURNEY_ACTIONS = {"briefing", "recommendation", "opportunity-draft"}
GROUNDING_MODES = {"fabric-iq", "general"}


def source_references(sources: list[dict]) -> list[dict]:
    return [
        {
            "id": item["id"],
            "type": item["type"],
            "container": item["container"],
            "title": item.get("subject") or item.get("title"),
            "timestamp": item["timestamp"],
        }
        for item in sources[:6]
    ]


def public_reasoning(client: dict, opportunity: dict, sources: list[dict], action: str) -> dict:
    references = source_references(sources)
    return {
        "evidenceUsed": [
            *[{"id": f"fabric:{client['id']}:client-360", "label": "Fabric Client 360 and current profile"}],
            *[{"id": source["id"], "label": source["title"]} for source in references],
        ],
        "decisionRules": [
            "Confirm KYC, consent, objectives, liquidity, horizon, and risk capacity before personalised advice.",
            "Keep near-term liquidity separate from longer-term investment allocation.",
            "Use fictional products only as discussion candidates; the RM must confirm eligibility and suitability.",
        ],
        "whyThisFits": [
            f"The artifact responds to {len(client['signals'])} current client signals.",
            f"The selected action is bounded by the recorded {client['riskProfile']} risk profile.",
            f"The workflow retains {len(opportunity['checks'])} mandatory checks for John Doe's review.",
        ],
        "alternativesConsidered": [
            "Retain additional liquidity and defer any investment discussion.",
            "Use a deposit or service-only follow-up where the investment profile is incomplete.",
            "Escalate to compliance or a product specialist when evidence is missing.",
        ],
        "assumptions": [
            "Authored Outlook and SharePoint context is fictional demonstration evidence.",
            "Fabric snapshot facts remain unchanged since the displayed snapshot time.",
        ],
        "limitations": [
            "This is public decision support, not private model chain-of-thought.",
            "No recommendation, email, CRM record, or transaction is executed by this workflow.",
            f"The {action.replace('-', ' ')} artifact requires RM review before use.",
        ],
    }


def deterministic_recommendation(client: dict, opportunity: dict, sources: list[dict] | None = None) -> dict:
    sources = sources or []
    meeting_objective = (
        f"Understand {client['name']}'s current priorities and agree the next suitable step "
        f"for this {opportunity['type'].casefold()} conversation."
    )
    return {
        "clientId": client["id"],
        "title": opportunity["title"],
        "summary": opportunity["summary"],
        "confidence": opportunity["confidence"],
        "priority": opportunity["priority"],
        "value": opportunity["value"],
        "channel": opportunity["channel"],
        "time": opportunity["time"],
        "evidence": opportunity["evidence"],
        "checks": opportunity["checks"],
        "opening": opportunity["opening"],
        "meetingObjective": meeting_objective,
        "clientContext": [
            f"{client['segment']} relationship with {client['assets']} in assets under care.",
            f"Recorded risk profile: {client['riskProfile']}.",
            f"Latest interaction: {client['recentInteraction']}.",
        ],
        "whatChanged": list(client["signals"][:3]),
        "talkTrack": [
            {
                "topic": "Open with the client's priorities",
                "guidance": opportunity["opening"],
            },
            {
                "topic": "Explore liquidity and time horizon",
                "guidance": "Clarify near-term commitments, the amount that must remain accessible, and when longer-term capital may be needed.",
            },
            {
                "topic": "Discuss investment themes carefully",
                "guidance": "Only after confirming the client profile, explain how diversified Unit Trust allocation themes could support the stated objective. Do not name a fund or imply a recommendation at this stage.",
            },
            {
                "topic": "Agree the governed next step",
                "guidance": f"Confirm whether to prepare a documented follow-up through {opportunity['channel'].casefold()} after completing the required checks.",
            },
        ],
        "discoveryQuestions": [
            "What has changed in your priorities since our last review?",
            "How much liquidity do you expect to need over the next 12 to 24 months?",
            "What investment horizon and level of fluctuation would feel appropriate for the remaining amount?",
            "Are there upcoming commitments or portfolio holdings that should shape the next discussion?",
        ],
        "allocationThemes": [
            "Preserve an appropriate liquidity reserve before discussing investments.",
            "Explore diversified income, balanced, or growth allocation themes only after objectives and risk capacity are reconfirmed.",
            "Assess existing holdings and concentration before preparing any product-level comparison.",
        ],
        "suitabilityChecks": list(opportunity["checks"]),
        "unresolvedItems": [
            "Confirm current objectives, investment horizon, liquidity needs, and risk capacity with the client.",
            "Confirm KYC, consent, and local product eligibility before preparing a product-level recommendation.",
        ],
        "followUpActions": [
            "Record the client's answers and any material change in circumstances.",
            "Complete or escalate outstanding profile and suitability checks.",
            "Prepare an approved product comparison only if the client asks to continue.",
        ],
        "action": "briefing",
        "sources": source_references(sources),
        "reasoning": public_reasoning(client, opportunity, sources, "briefing"),
        "evidenceStages": [
            {"label": "Relationship context", "detail": f"Reviewed {client['assets']} relationship and current product mix."},
            {"label": "Need signals", "detail": f"Correlated {len(client['signals'])} recent behavioural and lifecycle signals."},
            {"label": "Governance", "detail": f"Applied {len(opportunity['checks'])} mandatory suitability and service checks."},
            {"label": "Action design", "detail": f"Selected {opportunity['channel']} for {opportunity['time']}."},
        ],
        "provider": "deterministic-mock",
    }


def deterministic_journey_artifact(
    client: dict,
    opportunity: dict,
    action: str,
    sources: list[dict] | None = None,
    advisory_context: dict | None = None,
) -> dict:
    if action not in JOURNEY_ACTIONS:
        raise ValueError(f"Unsupported journey action: {action}")
    sources = sources or []
    briefing = deterministic_recommendation(client, opportunity, sources)
    if action == "briefing":
        briefing["artifact"] = {
            key: briefing[key]
            for key in (
                "meetingObjective",
                "clientContext",
                "whatChanged",
                "talkTrack",
                "discoveryQuestions",
                "followUpActions",
                "opening",
            )
        }
        return briefing

    base = {
        "action": action,
        "clientId": client["id"],
        "title": opportunity["title"],
        "summary": opportunity["summary"],
        "confidence": opportunity["confidence"],
        "priority": opportunity["priority"],
        "value": opportunity["value"],
        "channel": opportunity["channel"],
        "time": opportunity["time"],
        "checks": list(opportunity["checks"]),
        "unresolvedItems": [
            "Confirm the client's current objectives, liquidity needs, horizon, and risk capacity.",
            "Confirm KYC, consent, product eligibility, and suitability before client use.",
        ],
        "sources": source_references(sources),
        "reasoning": public_reasoning(client, opportunity, sources, action),
        "provider": "deterministic-mock",
    }
    if advisory_context:
        base.update(
            {
                "houseviewContext": advisory_context["houseviewContext"],
                "riskContext": advisory_context["riskContext"],
                "activityEvidence": advisory_context["activityEvidence"],
                "regulatoryControls": advisory_context["regulatoryControls"],
                "suppressedCandidates": advisory_context["suppressedCandidates"],
            }
        )
        base["reasoning"]["evidenceUsed"].extend(
            [
                {
                    "id": item["investment_activity_id"],
                    "label": f"{item['activity_type']} {item['asset_class']} activity of {item['currency']} {item['amount']:,}",
                }
                for item in advisory_context["activityEvidence"][:3]
            ]
        )
        base["reasoning"]["evidenceUsed"].extend(
            [
                {"id": section["houseview_section_id"], "label": f"CIO Houseview: {section['title']}"}
                for section in advisory_context["houseviewContext"]["sections"]
            ]
        )
        base["reasoning"]["decisionRules"].extend(
            [f"{item['ruleId']} / FAA-N16 paragraph {item['paragraph']}: {item['explanation']}" for item in advisory_context["regulatoryControls"]]
        )
        risk = advisory_context["riskContext"]
        if risk["declaredScore"] != risk["observedIndicator"]:
            base["reasoning"]["whyThisFits"].append(
                f"Observed behaviour moved from {risk['previousObservedIndicator']} to {risk['observedIndicator']}; the declared profile remains {risk['declaredScore']} pending review."
            )
    if action == "recommendation":
        retained_candidates = advisory_context["retainedCandidates"] if advisory_context else []
        advisory_products = [
            {
                "name": candidate["name"],
                "fictional": True,
                "intendedRole": candidate["category"].replace("_", " ").title(),
                "fitRationale": "Retained by the deterministic client-profile, liquidity, Houseview and regulatory gates.",
                "objectiveAlignment": "Subject to confirmed objectives and needs analysis.",
                "riskAlignment": f"Within declared risk score range {candidate['minRiskScore']}–{candidate['maxRiskScore']}.",
                "risks": ["Capital and income are not guaranteed", "Market views may change", "RM must confirm suitability and eligibility"],
                "evidenceIds": candidate["evidenceIds"],
            }
            for candidate in retained_candidates
        ]
        base.update(
            {
                "title": f"Custom recommendations for {client['name']}",
                "summary": "Fictional product candidates for RM review, subject to objectives, eligibility, and suitability confirmation.",
                "artifact": {
                    "status": "review-required",
                    "products": advisory_products or [
                        {
                            "name": "Frontier Liquidity Reserve Fund",
                            "fictional": True,
                            "intendedRole": "Near-term liquidity allocation",
                            "fitRationale": "Supports capital access while the client clarifies upcoming commitments.",
                            "objectiveAlignment": "Liquidity and optionality",
                            "riskAlignment": "Lower-volatility discussion candidate; capital is not guaranteed.",
                            "risks": ["Market value may fluctuate", "Income is not guaranteed", "Eligibility must be confirmed"],
                            "evidenceIds": [source["id"] for source in source_references(sources)[:2]],
                        },
                        {
                            "name": "Frontier Balanced Opportunities Fund",
                            "fictional": True,
                            "intendedRole": "Diversified medium-to-long-term allocation",
                            "fitRationale": f"Provides a diversified discussion candidate within a {client['riskProfile']} conversation.",
                            "objectiveAlignment": "Longer-term growth with diversification",
                            "riskAlignment": "Market, currency, and allocation risk require explicit client acceptance.",
                            "risks": ["Capital loss", "Market volatility", "Currency and asset-allocation risk"],
                            "evidenceIds": [source["id"] for source in source_references(sources)],
                        },
                    ],
                    "gates": list(opportunity["checks"]),
                    "disclaimer": advisory_context["disclaimer"] if advisory_context else "Fictional products for internal demonstration. Not an executable recommendation.",
                },
            }
        )
        return base

    base.update(
        {
            "title": f"Opportunity draft for {client['name']}",
            "summary": "Editable client email and CRM opportunity record derived from the reviewed recommendation.",
            "artifact": {
                "status": "draft-review-required",
                "email": {
                    "subject": f"Follow-up on our discussion and agreed next steps",
                    "body": (
                        f"Hello {client['name'].split()[0]},\n\nThank you for discussing your current priorities. "
                        "Based on the objectives and liquidity needs we reviewed, I have prepared a follow-up "
                        "covering the options we discussed. Before sharing any product-level recommendation, "
                        "I will confirm the outstanding profile, eligibility, and suitability checks.\n\n"
                        "Please let me know if any priorities or upcoming commitments have changed.\n\nRegards,\nJohn"
                    ),
                    "disclosures": [
                        "Draft only; John Doe must verify facts and approve the communication.",
                        "No product selection or transaction instruction is included.",
                    ],
                    "placeholders": ["Confirm client-stated objective", "Confirm agreed follow-up date"],
                },
                "crm": {
                    "need": opportunity["type"],
                    "stage": "RM review",
                    "estimatedScope": opportunity["value"],
                    "owner": "John Doe",
                    "nextAction": f"Review draft and confirm checks via {opportunity['channel']}",
                    "nextActionAt": opportunity["time"],
                    "evidenceIds": [source["id"] for source in source_references(sources)],
                    "approvalState": "Not approved",
                },
            },
        }
    )
    return base


def deterministic_general_artifact(client: dict, opportunity: dict, action: str) -> dict:
    if action not in JOURNEY_ACTIONS:
        raise ValueError(f"Unsupported journey action: {action}")
    basic = deterministic_journey_artifact(client, opportunity, action, [], None)
    basic["groundingMode"] = "general"
    basic["groundingLabel"] = "General AI draft"
    basic["comparisonSummary"] = "Uses basic client and opportunity facts only. Fabric IQ enterprise grounding is not applied."
    basic["sources"] = []
    basic["reasoning"] = {
        "evidenceUsed": [
            {"id": f"basic:{client['id']}:profile", "label": "Basic client profile"},
            {"id": f"basic:{opportunity['id']}:opportunity", "label": "Current opportunity summary"},
        ],
        "decisionRules": [
            "Use only the supplied broad client profile and opportunity summary.",
            "Retain mandatory checks and require human RM review before client use.",
        ],
        "whyThisFits": [
            f"The draft is lightly customized to {client['name']} and the current {opportunity['type'].casefold()} need.",
        ],
        "alternativesConsidered": ["Gather enterprise evidence before tailoring the artifact further."],
        "assumptions": ["No Fabric IQ, Houseview, activity, correspondence, semantic, Ontology, or regulatory-control context was supplied."],
        "limitations": [
            "This is a general AI draft with limited enterprise context and mandatory human review.",
            "It is not a suitability conclusion, compliance determination, or executable instruction.",
        ],
    }
    for field in ("houseviewContext", "riskContext", "activityEvidence", "regulatoryControls", "suppressedCandidates"):
        basic.pop(field, None)
    if action == "briefing":
        basic["clientContext"] = [
            f"{client['segment']} client with broad profile {client['riskProfile']}.",
            f"Current opportunity: {opportunity['title']}.",
        ]
        basic["whatChanged"] = list(client["signals"][:2])
        basic["talkTrack"] = [
            {"topic": "Confirm the purpose of the meeting", "guidance": opportunity["opening"]},
            {"topic": "Ask for updated priorities", "guidance": "Confirm objectives, liquidity, horizon, and material changes before discussing solutions."},
            {"topic": "Agree next steps", "guidance": "Document the conversation and gather missing evidence before tailoring further."},
        ]
    if action == "recommendation":
        basic["artifact"]["products"] = [
            {
                "name": "General diversified solution discussion",
                "fictional": True,
                "intendedRole": "Generic starting point",
                "fitRationale": "Broadly aligned to the recorded profile, without enterprise evidence to tailor further.",
                "objectiveAlignment": "Objectives must be reconfirmed.",
                "riskAlignment": "Broad profile only; no activity or Houseview validation.",
                "risks": ["Insufficient enterprise context", "Market and capital risk", "Suitability and eligibility must be confirmed"],
                "evidenceIds": [],
            }
        ]
        basic["artifact"]["disclaimer"] = "General fictional draft without Fabric IQ grounding. Not an executable recommendation."
    if action == "opportunity-draft":
        basic["artifact"]["crm"]["evidenceIds"] = []
        basic["artifact"]["email"]["placeholders"].append("Gather Fabric IQ evidence before tailoring")
    return basic


def deterministic_answer(question: str, knowledge: list[dict]) -> dict:
    normalised = question.casefold()
    words = {word for word in normalised.replace("?", " ").split() if len(word) > 2}
    best_entry = None
    best_score = 0

    for entry in knowledge:
        score = sum(2 for keyword in entry["keywords"] if keyword in normalised)
        score += sum(1 for word in words if word in entry["title"].casefold())
        if score > best_score:
            best_entry = entry
            best_score = score

    if best_entry is None or best_score == 0:
        return {
            "answer": (
                "I cannot answer that from the approved demonstration knowledge. "
                "Please consult the relevant product, compliance, or operations owner "
                "before communicating with a client."
            ),
            "citations": [],
            "escalationRequired": True,
            "provider": "deterministic-mock",
        }

    return {
        "answer": best_entry["answer"],
        "citations": [
            {
                "id": best_entry["id"],
                "title": best_entry["title"],
                "source": best_entry["source"],
            }
        ],
        "escalationRequired": False,
        "provider": "deterministic-mock",
    }


@dataclass(frozen=True)
class DeterministicKnowledgeProvider:
    name: str = "deterministic-mock"

    def answer(self, question: str, knowledge: list[dict]) -> dict:
        return deterministic_answer(question, knowledge)


@dataclass(frozen=True)
class AzureOpenAIKnowledgeProvider:
    endpoint: str
    deployment: str
    api_version: str = "2024-10-21"
    name: str = "azure-openai"

    def answer(self, question: str, knowledge: list[dict]) -> dict:
        try:
            token = _managed_identity_token()
        except (error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError("Managed identity token acquisition failed safely") from exc
        allowed_ids = {entry["id"] for entry in knowledge}
        context = "\n\n".join(
            f"[{entry['id']}] {entry['title']}\n{entry['answer']}\nSource: {entry['source']}"
            for entry in knowledge
        )
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Frontier Knowledge for an internal fictional banking demo. "
                        "Answer only from APPROVED KNOWLEDGE. If the answer is absent, set "
                        "escalationRequired to true and say that an approved owner must be consulted. "
                        "Never provide personalised financial advice, forecasts, or guaranteed outcomes. "
                        "Return strict JSON with answer, citationIds, and escalationRequired.\n\n"
                        f"APPROVED KNOWLEDGE\n{context}"
                    ),
                },
                {"role": "user", "content": question},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
            "response_format": {"type": "json_object"},
        }
        encoded_deployment = parse.quote(self.deployment, safe="")
        url = (
            f"{self.endpoint.rstrip('/')}/openai/deployments/{encoded_deployment}"
            f"/chat/completions?api-version={parse.quote(self.api_version)}"
        )
        http_request = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "frontier-rm-cockpit/0.1",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=30, context=ssl.create_default_context()) as response:
                raw = json.loads(response.read().decode("utf-8"))
            content = raw["choices"][0]["message"]["content"]
            generated = json.loads(content)
        except (error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError("Azure OpenAI request failed safely") from exc

        citation_ids = [item for item in generated.get("citationIds", []) if item in allowed_ids]
        citations = [
            {"id": entry["id"], "title": entry["title"], "source": entry["source"]}
            for entry in knowledge
            if entry["id"] in citation_ids
        ]
        escalation = bool(generated.get("escalationRequired")) or not citations
        return {
            "answer": str(generated.get("answer", "Approved knowledge did not return an answer.")),
            "citations": citations,
            "escalationRequired": escalation,
            "provider": self.name,
        }

    def recommend(
        self,
        client: dict,
        opportunity: dict,
        action: str = "briefing",
        sources: list[dict] | None = None,
        advisory_context: dict | None = None,
        grounding_mode: str = "fabric-iq",
    ) -> dict:
        if action not in JOURNEY_ACTIONS:
            raise ValueError(f"Unsupported journey action: {action}")
        if grounding_mode not in GROUNDING_MODES:
            raise ValueError(f"Unsupported grounding mode: {grounding_mode}")
        sources = sources or []
        prompt_client = client if grounding_mode == "fabric-iq" else {
            "id": client["id"],
            "name": client["name"],
            "segment": client["segment"],
            "riskProfile": client["riskProfile"],
            "signals": list(client["signals"][:3]),
        }
        try:
            token = _managed_identity_token()
        except (error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError("Managed identity token acquisition failed safely") from exc
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Frontier RM Recommendation Engine for a fictional internal Premier banking demo. "
                        f"Create the {action} artifact using only the supplied client facts and authored sources. Do not invent rates, "
                        "returns, products, balances, or personal details. Preserve mandatory checks. Return strict "
                        "JSON with title, summary, confidence (integer 0-100), priority, value, channel, time, "
                        "evidence (array), checks (array), opening, meetingObjective, clientContext (array), "
                        "whatChanged (array), talkTrack (array of objects with topic and guidance), "
                        "discoveryQuestions (array), allocationThemes (array), suitabilityChecks (array), "
                        "unresolvedItems (array), and followUpActions (array). The opening must be a professional, "
                        "editable conversation starter and not financial advice. Allocation themes may discuss "
                        "diversification, liquidity, income, balanced, or growth approaches, but must not name funds, "
                        "select a real product, conclude suitability, promise returns, or instruct a transaction. "
                        "Never provide private chain-of-thought. Keep any rationale concise, evidence-based, and suitable for display."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "action": action,
                            "groundingMode": grounding_mode,
                            "client": prompt_client,
                            "currentOpportunity": opportunity,
                            "authoredSources": [
                                {
                                    "id": item["id"],
                                    "type": item["type"],
                                    "title": item.get("subject") or item.get("title"),
                                    "timestamp": item["timestamp"],
                                    "body": item["body"][:1200],
                                }
                                for item in (sources[:6] if grounding_mode == "fabric-iq" else [])
                            ],
                            "advisoryContext": advisory_context if grounding_mode == "fabric-iq" else None,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 1600,
            "response_format": {"type": "json_object"},
        }
        encoded_deployment = parse.quote(self.deployment, safe="")
        url = (
            f"{self.endpoint.rstrip('/')}/openai/deployments/{encoded_deployment}"
            f"/chat/completions?api-version={parse.quote(self.api_version)}"
        )
        http_request = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "frontier-rm-cockpit/0.2",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=35, context=ssl.create_default_context()) as response:
                raw = json.loads(response.read().decode("utf-8"))
            generated = json.loads(raw["choices"][0]["message"]["content"])
        except (error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError("Azure OpenAI recommendation failed safely") from exc

        safe = (
            deterministic_journey_artifact(client, opportunity, action, sources, advisory_context)
            if grounding_mode == "fabric-iq"
            else deterministic_general_artifact(client, opportunity, action)
        )
        for key in (
            "title",
            "summary",
            "priority",
            "value",
            "channel",
            "time",
            "opening",
            "meetingObjective",
        ):
            if generated.get(key):
                safe[key] = str(generated[key])[:1000]
        if isinstance(generated.get("confidence"), int):
            safe["confidence"] = max(0, min(100, generated["confidence"]))
        for key in (
            "evidence",
            "checks",
            "clientContext",
            "whatChanged",
            "discoveryQuestions",
            "allocationThemes",
            "suitabilityChecks",
            "unresolvedItems",
            "followUpActions",
        ):
            if isinstance(generated.get(key), list) and generated[key]:
                safe[key] = [str(item)[:300] for item in generated[key][:6]]
        if action == "briefing" and isinstance(generated.get("talkTrack"), list) and generated["talkTrack"]:
            talk_track = []
            for item in generated["talkTrack"][:6]:
                if not isinstance(item, dict) or not item.get("topic") or not item.get("guidance"):
                    continue
                talk_track.append(
                    {
                        "topic": str(item["topic"])[:120],
                        "guidance": str(item["guidance"])[:600],
                    }
                )
            if talk_track:
                safe["talkTrack"] = talk_track
        safe["provider"] = self.name
        safe["groundingMode"] = grounding_mode
        safe.setdefault("groundingLabel", "Fabric IQ grounded" if grounding_mode == "fabric-iq" else "General AI draft")
        if action == "briefing":
            safe["evidenceStages"] = [
                {"label": "Relationship context", "detail": f"Reviewed {client['assets']} relationship and current product mix."},
                {"label": "Need signals", "detail": f"Correlated {len(client['signals'])} verified lifecycle and engagement signals."},
                {"label": "Governance", "detail": f"Applied {len(safe['checks'])} mandatory suitability and service checks."},
                {"label": "Action design", "detail": f"Selected {safe['channel']} for {safe['time']}."},
            ]
        return safe


def provider_from_environment() -> KnowledgeProvider:
    mode = os.environ.get("FRONTIER_AI_MODE", "mock").casefold()
    if mode != "azure":
        return DeterministicKnowledgeProvider()

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()
    if not endpoint or not deployment:
        return DeterministicKnowledgeProvider()
    return AzureOpenAIKnowledgeProvider(endpoint=endpoint, deployment=deployment)


_TOKEN_CACHE: tuple[str, float] | None = None


def _managed_identity_token() -> str:
    global _TOKEN_CACHE
    if _TOKEN_CACHE and _TOKEN_CACHE[1] > time.time() + 120:
        return _TOKEN_CACHE[0]

    identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
    identity_header = os.environ.get("IDENTITY_HEADER")
    if identity_endpoint and identity_header:
        separator = "&" if "?" in identity_endpoint else "?"
        token_url = (
            f"{identity_endpoint}{separator}resource="
            f"{parse.quote('https://cognitiveservices.azure.com/')}&api-version=2019-08-01"
        )
        client_id = os.environ.get("AZURE_CLIENT_ID")
        if client_id:
            token_url += f"&client_id={parse.quote(client_id)}"
        token_request = request.Request(
            token_url,
            headers={"X-IDENTITY-HEADER": identity_header, "Metadata": "true"},
        )
        with request.urlopen(token_request, timeout=10, context=ssl.create_default_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        token = payload["access_token"]
        expiry = float(payload.get("expires_on", time.time() + 300))
        _TOKEN_CACHE = (token, expiry)
        return token

    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError("Managed identity is unavailable") from exc
    try:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        access_token = credential.get_token("https://cognitiveservices.azure.com/.default")
    except Exception as exc:  # Azure Identity exposes multiple credential-specific errors.
        raise RuntimeError("Managed identity is unavailable") from exc
    _TOKEN_CACHE = (access_token.token, float(access_token.expires_on))
    return access_token.token
