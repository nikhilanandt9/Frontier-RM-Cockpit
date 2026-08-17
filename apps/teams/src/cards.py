from __future__ import annotations


def build_knowledge_card(question: str, result: dict) -> dict:
    citations = result.get("citations", [])
    citation_blocks = [
        {
            "type": "TextBlock",
            "text": f"[{citation['id']}] {citation['source']}",
            "size": "Small",
            "color": "Accent",
            "wrap": True,
        }
        for citation in citations
    ]
    if not citation_blocks:
        citation_blocks.append(
            {
                "type": "TextBlock",
                "text": "No approved source found. Escalation required.",
                "size": "Small",
                "color": "Attention",
                "wrap": True,
            }
        )

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {"type": "TextBlock", "text": "FRONTIER RM", "weight": "Bolder", "color": "Attention", "size": "Small"},
                    {"type": "TextBlock", "text": "Grounded knowledge", "weight": "Bolder", "size": "Large"},
                ],
            },
            {"type": "TextBlock", "text": question, "weight": "Bolder", "wrap": True, "spacing": "Medium"},
            {"type": "TextBlock", "text": result["answer"], "wrap": True},
            {"type": "TextBlock", "text": "Verified demonstration sources", "weight": "Bolder", "size": "Small", "spacing": "Large"},
            *citation_blocks,
            {
                "type": "TextBlock",
                "text": "Internal fictional demonstration. Verify approved sources before client communication.",
                "size": "Small",
                "isSubtle": True,
                "wrap": True,
                "spacing": "Large",
            },
        ],
    }
