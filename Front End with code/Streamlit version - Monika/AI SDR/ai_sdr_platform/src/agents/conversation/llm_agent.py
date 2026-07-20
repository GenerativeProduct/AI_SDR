from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from ai_sdr_platform.src.agents.conversation.models import (
    ConversationAgentDecision,
    ReplyClassification,
)


@dataclass
class StructuredConversationLLMAgent:
    base_url: str
    model_name: str
    timeout_seconds: float = 90.0

    def decide(self, *, reply_text: str, context: dict[str, Any]) -> ConversationAgentDecision:
        schema = ConversationAgentDecision.model_json_schema()
        response = requests.post(
            f"{self.base_url.rstrip('/')}/api/chat",
            json={
                "model": self.model_name,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0.1},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a production B2B SDR conversation agent. Classify the inbound "
                            "reply and draft a concise grounded response. Use only the supplied context. "
                            "Never invent pricing, commitments, customer facts, meeting times, or metrics. "
                            "All outbound replies require human approval. stop_follow_up must be true for "
                            "any genuine human reply, objection, not-now response, pricing request, meeting "
                            "request, or interest. Return JSON matching the supplied schema."
                            " If multiple intents appear, choose the most actionable intent in this "
                            "priority order: meeting_request, pricing_request, interested, objection, "
                            "not_now, neutral. suggested_reply is required for every intent except "
                            "unsubscribe and out_of_office."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"inbound_reply": reply_text, "context": context},
                            indent=2,
                            default=str,
                        ),
                    },
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        raw_content = payload.get("message", {}).get("content", "")
        parsed = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
        decision = ConversationAgentDecision.model_validate(parsed)
        decision.classification.source = "llm"
        decision.classification.requires_human = True
        decision.classification.stop_follow_up = True
        decision.model_name = self.model_name
        return decision

    def reachable(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url.rstrip('/')}/api/tags",
                timeout=2.0,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False


def fallback_decision(
    classification: ReplyClassification,
    suggested_reply: str | None,
    *,
    model_name: str,
    reason: str,
) -> ConversationAgentDecision:
    return ConversationAgentDecision(
        classification=classification,
        suggested_reply=suggested_reply,
        guardrail_notes=[
            "Structured LLM was unavailable; human review is mandatory.",
            reason,
        ],
        model_name=model_name,
    )
