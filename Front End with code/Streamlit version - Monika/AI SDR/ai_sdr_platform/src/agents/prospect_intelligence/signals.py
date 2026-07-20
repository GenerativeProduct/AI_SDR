from __future__ import annotations

import re
from datetime import datetime, timezone

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResult
from ai_sdr_platform.src.agents.prospect_intelligence.models import IntelligenceSignal, SignalType

TYPE_ALIASES: dict[str, SignalType] = {
    "funding": "funding",
    "financial": "funding",
    "investment": "funding",
    "hiring": "hiring",
    "job": "hiring",
    "leadership": "leadership_change",
    "executive": "leadership_change",
    "expansion": "expansion",
    "growth": "growth",
    "product": "product",
    "launch": "product",
    "technology": "technology_change",
    "tech": "technology_change",
    "technographic": "technology_change",
    "intent": "web_intent",
    "website": "web_intent",
    "engagement": "outreach_engagement",
    "email": "outreach_engagement",
    "news": "news",
    "risk": "risk",
}

POSITIVE_TYPES = {
    "funding",
    "hiring",
    "leadership_change",
    "expansion",
    "technology_change",
    "product",
    "web_intent",
    "outreach_engagement",
    "growth",
}
NEGATIVE_TERMS = {
    "layoff",
    "decline",
    "bankruptcy",
    "shutdown",
    "loss",
    "risk",
    "breach",
    "lawsuit",
}


def normalize_enrichment_signals(enrichment: EnrichmentResult) -> list[IntelligenceSignal]:
    output: list[IntelligenceSignal] = []
    seen: set[tuple[str, str]] = set()
    now = datetime.now(timezone.utc)
    citation_urls = {citation.url for citation in enrichment.citations if citation.url}

    for raw in enrichment.signals:
        normalized_type = _normalize_type(raw.type, raw.detail)
        detail = re.sub(r"\s+", " ", raw.detail).strip()
        if not detail:
            continue
        key = (normalized_type, detail.lower())
        if key in seen:
            continue
        seen.add(key)
        source_url = raw.source_url or None
        verified = bool(source_url and source_url in citation_urls)
        source_reliability = 0.85 if verified else 0.55 if source_url else 0.35
        polarity = "negative" if _is_negative(normalized_type, detail) else (
            "positive" if normalized_type in POSITIVE_TYPES else "neutral"
        )
        output.append(
            IntelligenceSignal(
                account_id=enrichment.account_id,
                signal_type=normalized_type,
                detail=detail,
                confidence=max(0.0, min(float(raw.confidence), 1.0)),
                source_reliability=source_reliability,
                source_url=source_url,
                observed_at=now,
                polarity=polarity,
                verified=verified,
                raw_type=raw.type,
            )
        )
    return output


def _normalize_type(raw_type: str, detail: str) -> SignalType:
    searchable = f"{raw_type} {detail}".lower()
    for alias, normalized in TYPE_ALIASES.items():
        if alias in searchable:
            return normalized
    return "other"


def _is_negative(signal_type: SignalType, detail: str) -> bool:
    if signal_type == "risk":
        return True
    lowered = detail.lower()
    return any(term in lowered for term in NEGATIVE_TERMS)
