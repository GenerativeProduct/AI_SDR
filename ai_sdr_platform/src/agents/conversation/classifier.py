from __future__ import annotations

import re

from ai_sdr_platform.src.agents.conversation.models import ReplyClassification


class ComplianceGuardrailClassifier:
    """Deterministic rules only for safety and compliance-critical intents."""

    def classify(self, text: str) -> ReplyClassification | None:
        normalized = " ".join(text.lower().split())
        rules = [
            (
                "unsubscribe",
                ("unsubscribe", "remove me", "stop emailing", "do not contact", "opt out", "opt-out"),
                "negative",
                False,
                "Suppress the contact and close the conversation.",
            ),
            (
                "wrong_person",
                ("wrong person", "not responsible", "not the right person", "doesn't handle", "not my area"),
                "neutral",
                True,
                "Ask for or review the correct contact.",
            ),
            (
                "out_of_office",
                ("out of office", "automatic reply", "away until", "on leave", "ooo", "back on", "vacation"),
                "neutral",
                False,
                "Resume only after the detected return date or manual review.",
            ),
        ]
        for intent, phrases, sentiment, requires_human, next_action in rules:
            matched = next((phrase for phrase in phrases if phrase in normalized), None)
            if not matched:
                continue
            entities = {}
            date_match = re.search(
                r"\b(next (?:week|month|quarter)|(?:mon|tues|wednes|thurs|fri)day)\b",
                normalized,
            )
            if date_match:
                entities["timing"] = date_match.group(1)
            return ReplyClassification(
                intent=intent,  # type: ignore[arg-type]
                confidence=0.98 if intent == "unsubscribe" else 0.94,
                sentiment=sentiment,  # type: ignore[arg-type]
                requires_human=requires_human,
                stop_follow_up=True,
                next_action=next_action,
                detected_entities=entities,
                reasons=[f"Compliance guardrail matched: {matched}"],
                source="rules",
            )
        return None


class SafeFallbackClassifier:
    """Degraded-mode classifier used only when the structured LLM is unavailable."""

    def classify(self, text: str) -> ReplyClassification:
        normalized = " ".join(text.lower().split())
        rules = [
            (
                "meeting_request",
                ("book a call", "schedule", "calendar", "meet next", "available on", "meeting", "call", "book a time", "available"),
                "positive",
            ),
            (
                "pricing_request",
                ("price", "pricing", "cost", "quote", "budget", "how much"),
                "positive",
            ),
            (
                "not_now",
                ("not now", "later", "next quarter", "next month", "circle back", "not right now"),
                "neutral",
            ),
            (
                "objection",
                ("already use", "not interested", "too expensive", "no need", "no budget", "already have", "not a priority"),
                "negative",
            ),
            (
                "interested",
                ("interested", "tell me more", "sounds useful", "send details", "yes", "sounds good", "sounds great", "let's talk"),
                "positive",
            ),
        ]
        for intent, phrases, sentiment in rules:
            matches = [phrase for phrase in phrases if phrase in normalized]
            if matches:
                matched = matches[0]
                match_count = len(matches)
                confidence = min(0.95, max(0.68, 0.50 + 0.15 * match_count))
                return ReplyClassification(
                    intent=intent,  # type: ignore[arg-type]
                    confidence=confidence,
                    sentiment=sentiment,  # type: ignore[arg-type]
                    requires_human=True,
                    stop_follow_up=True,
                    next_action="Review the degraded-mode classification and draft.",
                    reasons=[f"LLM unavailable; fallback phrase matched: {matched}"],
                    source="hybrid",
                )
        return ReplyClassification(
            intent="neutral",
            confidence=0.40,
            sentiment="neutral",
            requires_human=True,
            stop_follow_up=True,
            next_action="Review the ambiguous reply before continuing outreach.",
            reasons=["LLM unavailable and no fallback phrase matched."],
            source="hybrid",
        )


# Backward-compatible name for existing imports and tests.
ReplyClassifier = SafeFallbackClassifier
