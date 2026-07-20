from __future__ import annotations

from datetime import datetime, timezone
from math import exp, log

from ai_sdr_platform.src.agents.enrichment.models import EnrichmentResult
from ai_sdr_platform.src.agents.prospect_discovery.models import DiscoveredAccount, DiscoveredContact
from ai_sdr_platform.src.agents.prospect_intelligence.models import IntelligenceSignal, ProspectFeatures

HIGH_INTENT_TYPES = {"web_intent", "outreach_engagement"}
READINESS_TYPES = {
    "funding",
    "hiring",
    "leadership_change",
    "expansion",
    "technology_change",
    "growth",
    "product",
}


def build_features(
    account: DiscoveredAccount,
    contact: DiscoveredContact,
    enrichment: EnrichmentResult,
    signals: list[IntelligenceSignal],
) -> ProspectFeatures:
    positive = [_signal_strength(signal) for signal in signals if signal.polarity == "positive"]
    negative = [_signal_strength(signal) for signal in signals if signal.polarity == "negative"]
    high_intent = [_signal_strength(signal) for signal in signals if signal.signal_type in HIGH_INTENT_TYPES]
    readiness = [_signal_strength(signal) for signal in signals if signal.signal_type in READINESS_TYPES]

    completeness_fields = [
        enrichment.company_summary,
        enrichment.products_services,
        enrichment.target_customers,
        enrichment.pain_point_hypotheses,
        enrichment.personalization_angles,
        enrichment.contact_briefs,
        enrichment.citations,
    ]
    completeness = sum(bool(value) for value in completeness_fields) / len(completeness_fields)

    return ProspectFeatures(
        account_fit_score=_unit_score(account.fit_score),
        persona_match_score=_unit_score(contact.persona_match_score),
        contact_confidence=_unit_score(contact.confidence),
        enrichment_confidence=max(0.0, min(float(enrichment.confidence_score), 1.0)),
        enrichment_completeness=completeness,
        positive_signal_strength=_combine_strengths(positive),
        negative_signal_strength=_combine_strengths(negative),
        high_intent_signal_strength=_combine_strengths(high_intent),
        buying_readiness_strength=_combine_strengths(readiness),
        signal_count=len(signals),
        verified_signal_count=sum(signal.verified for signal in signals),
    )


def feature_vector(features: ProspectFeatures) -> dict[str, float]:
    return {
        "account_fit_score": features.account_fit_score,
        "persona_match_score": features.persona_match_score,
        "contact_confidence": features.contact_confidence,
        "enrichment_confidence": features.enrichment_confidence,
        "enrichment_completeness": features.enrichment_completeness,
        "positive_signal_strength": features.positive_signal_strength,
        "negative_signal_strength": features.negative_signal_strength,
        "high_intent_signal_strength": features.high_intent_signal_strength,
        "buying_readiness_strength": features.buying_readiness_strength,
        "signal_count_log": log(1 + features.signal_count),
        "verified_signal_count_log": log(1 + features.verified_signal_count),
    }


def _signal_strength(signal: IntelligenceSignal) -> float:
    now = datetime.now(timezone.utc)
    observed_at = signal.observed_at
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    age_days = max((now - observed_at).total_seconds() / 86400.0, 0.0)
    recency = exp(-age_days / 90.0)
    verification_bonus = 1.0 if signal.verified else 0.8
    return min(signal.confidence * signal.source_reliability * recency * verification_bonus, 1.0)


def _combine_strengths(values: list[float]) -> float:
    remaining = 1.0
    for value in values:
        remaining *= 1.0 - max(0.0, min(value, 1.0))
    return 1.0 - remaining


def _unit_score(value: int | float | None) -> float:
    numeric = float(value or 0.0)
    return max(0.0, min(numeric / 100.0, 1.0))
