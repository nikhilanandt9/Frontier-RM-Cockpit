from __future__ import annotations


RISK_LABELS = {
    1: "Capital Preservation",
    2: "Cautious",
    3: "Balanced",
    4: "Growth",
    5: "Aggressive",
}


CANDIDATES = (
    {
        "id": "candidate-liquidity-reserve",
        "name": "Frontier Liquidity Reserve Fund",
        "category": "LIQUIDITY",
        "minRiskScore": 1,
        "maxRiskScore": 5,
        "complex": False,
        "houseviewSectionIds": ["hv-q4-liquidity"],
    },
    {
        "id": "candidate-quality-income",
        "name": "Frontier Quality Income Fund",
        "category": "INCOME",
        "minRiskScore": 1,
        "maxRiskScore": 4,
        "complex": False,
        "houseviewSectionIds": ["hv-q4-income"],
    },
    {
        "id": "candidate-balanced-opportunities",
        "name": "Frontier Balanced Opportunities Fund",
        "category": "BALANCED",
        "minRiskScore": 3,
        "maxRiskScore": 5,
        "complex": False,
        "houseviewSectionIds": ["hv-q4-regime", "hv-q4-growth"],
    },
    {
        "id": "candidate-quality-growth",
        "name": "Frontier Quality Growth Fund",
        "category": "GROWTH",
        "minRiskScore": 4,
        "maxRiskScore": 5,
        "complex": False,
        "houseviewSectionIds": ["hv-q4-growth"],
    },
    {
        "id": "candidate-structured-derivative",
        "name": "Frontier Tactical Derivative Note",
        "category": "COMPLEX_DERIVATIVE",
        "minRiskScore": 5,
        "maxRiskScore": 5,
        "complex": True,
        "houseviewSectionIds": ["hv-q4-regime"],
    },
)


def _control(rule_by_gate: dict, gate: str, status: str, explanation: str) -> dict:
    rule = rule_by_gate[gate]
    return {
        "ruleId": rule["regulatory_rule_id"],
        "paragraph": rule["paragraph"],
        "title": rule["title"],
        "status": status,
        "explanation": explanation,
    }


def build_advisory_context(data: dict, client_id: str, houseview_id: str | None = None) -> dict:
    client = next((item for item in data["clients"] if item["id"] == client_id), None)
    if client is None:
        raise ValueError("Client advisory context not found")
    houseview = next(
        (
            item
            for item in data["houseviews"]
            if item["houseview_id"] == houseview_id
        ),
        None,
    ) if houseview_id else next((item for item in data["houseviews"] if item["status"] == "ACTIVE"), None)
    if houseview is None:
        raise ValueError("Houseview report not found")

    profile = client["advisoryProfile"]
    activity = client["investmentActivity"]
    behaviour = client["behaviourHistory"][0]
    rules = {item["gate"]: item for item in data["regulatoryRules"]}
    complete_profile = bool(profile["income_complete"] and profile["commitments_complete"])
    review_current = profile["risk_review_status"] == "CURRENT"
    knowledge_current = profile["knowledge_experience_status"] == "CURRENT"
    kyc_current = "Current" in client["kycStatus"]
    enhanced_review = profile["retirement_status"] == "RETIRED"

    controls = [
        _control(
            rules,
            "objectives-financial-situation-needs",
            "PASS" if complete_profile else "REVIEW_REQUIRED",
            "Objectives, financial situation and particular needs are complete." if complete_profile else "Income or commitment evidence is incomplete and must be refreshed.",
        ),
        _control(
            rules,
            "profile-completeness",
            "PASS" if complete_profile and review_current else "REVIEW_REQUIRED",
            "Client information and declared profile are current." if complete_profile and review_current else "Profile information or review status is incomplete.",
        ),
        _control(
            rules,
            "product-risk-liquidity",
            "PASS" if profile["liquidity_horizon_months"] else "REVIEW_REQUIRED",
            f"Liquidity horizon is recorded as {profile['liquidity_horizon_months']} months.",
        ),
        _control(
            rules,
            "documented-basis",
            "PASS",
            "The artifact retains Houseview, activity and client-profile evidence IDs.",
        ),
    ]
    if enhanced_review:
        controls.append(
            {
                "ruleId": "INTERNAL-RETIREMENT-ENHANCED-REVIEW",
                "paragraph": "Internal policy",
                "title": "Retirement enhanced review",
                "status": "REVIEW_REQUIRED" if not (complete_profile and knowledge_current and kyc_current) else "PASS",
                "explanation": "Retirement requires current income, liquidity, commitments and applicable knowledge/experience evidence. This is an internal safeguard, not an MAS automatic risk-score rule.",
            }
        )

    score = profile["declared_risk_score"]
    retained = []
    suppressed = []
    for candidate in CANDIDATES:
        failures = []
        if not candidate["minRiskScore"] <= score <= candidate["maxRiskScore"]:
            failures.append(f"Declared Investment Risk Profile {score} ({RISK_LABELS[score]}) is outside the candidate range.")
        if candidate["complex"] and not knowledge_current:
            failures.append("Knowledge or experience evidence is incomplete.")
        if candidate["complex"] and profile["cka_status"] not in {"CURRENT", "NOT_APPLICABLE"}:
            failures.append("Applicable Customer Knowledge Assessment is not current.")
        if candidate["complex"] and profile["car_status"] not in {"CURRENT", "NOT_APPLICABLE"}:
            failures.append("Applicable Customer Account Review is not current.")
        if candidate["complex"] and enhanced_review and not complete_profile:
            failures.append("Retirement enhanced review has incomplete income or commitment evidence.")
        if not kyc_current:
            failures.append("KYC profile is not current.")
        result = {
            **candidate,
            "fictional": True,
            "evidenceIds": [
                f"fabric:{client_id}:advisory-profile",
                *[item["investment_activity_id"] for item in activity[:3]],
                *candidate["houseviewSectionIds"],
            ],
        }
        if failures:
            suppressed.append({**result, "reasons": failures, "ruleIds": [item["ruleId"] for item in controls if item["status"] != "PASS"]})
        else:
            retained.append(result)

    return {
        "clientId": client_id,
        "clientName": client["name"],
        "houseviewContext": {
            "reportId": houseview["houseview_id"],
            "title": houseview["title"],
            "asOf": houseview["as_of_date"],
            "status": houseview["status"],
            "cioStance": houseview["cio_stance"],
            "sections": houseview["sections"],
        },
        "riskContext": {
            "declaredScore": score,
            "declaredLabel": profile["declared_risk_label"],
            "profileEffectiveAt": profile["profile_effective_at"],
            "observedIndicator": profile["observed_behaviour_indicator"],
            "observedLabel": profile["observed_behaviour_label"],
            "previousObservedIndicator": behaviour["previous_indicator"],
            "divergence": profile["observed_behaviour_indicator"] - score,
            "reviewStatus": profile["risk_review_status"],
            "employmentStatus": profile["employment_status"],
            "retirementStatus": profile["retirement_status"],
            "declaredProfileChangedByActivity": behaviour["declared_profile_changed"],
            "indicatorCalculatedAt": profile["indicator_calculated_at"],
        },
        "activityEvidence": activity,
        "regulatoryControls": controls,
        "retainedCandidates": retained,
        "suppressedCandidates": suppressed,
        "disclaimer": "Compliance-aware fictional positioning candidates for RM review. Not financial advice, a suitability conclusion, legal advice, or proof of regulatory compliance.",
    }
