from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

import requests

from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    IntentAssessment,
    PropensityAssessment,
    RankingResult,
    RankingSystemStatus,
)
from ai_sdr_platform.src.agents.prospect_intelligence.metarank_events import (
    SDRMetaRankEventStore,
)


class RankingProvider(Protocol):
    def rank(
        self,
        *,
        account_id: str,
        contact_id: str,
        intent: IntentAssessment,
        propensity: PropensityAssessment,
    ) -> RankingResult:
        ...

    def rank_many(
        self,
        items: list[tuple[str, str, IntentAssessment, PropensityAssessment]],
    ) -> dict[str, RankingResult]:
        ...

    def status(self) -> RankingSystemStatus:
        ...


@dataclass
class LocalRankingProvider:
    event_store: SDRMetaRankEventStore | None = None
    def rank(
        self,
        *,
        account_id: str,
        contact_id: str,
        intent: IntentAssessment,
        propensity: PropensityAssessment,
    ) -> RankingResult:
        score = (
            propensity.reply_probability.value * 0.35
            + propensity.meeting_probability.value * 0.45
            + propensity.qualification_probability.value * 0.10
            + intent.probability.value * 0.10
        )
        band = "high" if score >= 0.60 else "medium" if score >= 0.30 else "low"
        return RankingResult(
            priority_score=score,
            priority_band=band,
            provider="local",
            reasons=[
                "Priority combines reply, meeting, qualification, and intent estimates.",
                "MetaRank will replace local ordering after outcome feedback is available.",
            ],
        )

    def feedback(self, event: dict[str, Any]) -> bool:
        if self.event_store:
            self.event_store.append(event)
            return True
        return False

    def rank_many(
        self,
        items: list[tuple[str, str, IntentAssessment, PropensityAssessment]],
    ) -> dict[str, RankingResult]:
        event_id = f"sdr-ranking-{uuid4()}"
        ranked = [
            (
                contact_id,
                self.rank(
                    account_id=account_id,
                    contact_id=contact_id,
                    intent=intent,
                    propensity=propensity,
                ),
            )
            for account_id, contact_id, intent, propensity in items
        ]
        ranked.sort(key=lambda item: item[1].priority_score, reverse=True)
        for index, (_, result) in enumerate(ranked, start=1):
            result.rank = index
            result.ranking_event_id = event_id
        if self.event_store:
            timestamp = datetime.now(timezone.utc).isoformat()
            for account_id, contact_id, intent, propensity in items:
                self.event_store.append(
                    {
                        "event": "item",
                        "id": f"lead-item-{contact_id}",
                        "item": contact_id,
                        "timestamp": timestamp,
                        "fields": [
                            {
                                "name": "intent_probability",
                                "value": intent.probability.value,
                            },
                            {
                                "name": "reply_probability",
                                "value": propensity.reply_probability.value,
                            },
                            {
                                "name": "meeting_probability",
                                "value": propensity.meeting_probability.value,
                            },
                            {
                                "name": "qualification_probability",
                                "value": propensity.qualification_probability.value,
                            },
                            {"name": "account_id", "value": account_id},
                        ],
                    }
                )
            self.event_store.append(
                {
                    "event": "ranking",
                    "id": event_id,
                    "user": "sdr-default-campaign",
                    "session": event_id,
                    "timestamp": timestamp,
                    "items": [
                        {"id": contact_id, "relevance": 0}
                        for contact_id, _ in ranked
                    ],
                    "fields": [{"name": "provider", "value": "local_cold_start"}],
                }
            )
        return dict(ranked)

    def status(self) -> RankingSystemStatus:
        return RankingSystemStatus(
            configured=False,
            reachable=False,
            model_name="local-weighted-ranking",
            active_provider="local",
            learned_reranking_active=False,
            detail="Using the local probability-weighted fallback.",
        )


@dataclass
class MetaRankRankingProvider:
    base_url: str
    model_name: str = "sdr-prospect-ranker"
    timeout_seconds: float = 3.0
    fallback: RankingProvider = field(default_factory=LocalRankingProvider)
    event_store: SDRMetaRankEventStore | None = None

    def rank(
        self,
        *,
        account_id: str,
        contact_id: str,
        intent: IntentAssessment,
        propensity: PropensityAssessment,
    ) -> RankingResult:
        payload: dict[str, Any] = {
            "event": "ranking",
            "id": f"prospect-{account_id}-{contact_id}",
            "items": [
                {
                    "id": contact_id,
                    "fields": [
                        {"name": "account_id", "value": account_id},
                        {"name": "intent_probability", "value": intent.probability.value},
                        {"name": "reply_probability", "value": propensity.reply_probability.value},
                        {"name": "meeting_probability", "value": propensity.meeting_probability.value},
                    ],
                }
            ],
            "user": account_id,
            "session": account_id,
        }
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/rank/{self.model_name}",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            raw_items = data.get("items", [])
            if raw_items:
                raw_score = float(raw_items[0].get("score", 0.0))
                normalized = 1.0 / (1.0 + pow(2.718281828, -raw_score))
                band = "high" if normalized >= 0.60 else "medium" if normalized >= 0.30 else "low"
                return RankingResult(
                    priority_score=normalized,
                    rank=1,
                    priority_band=band,
                    provider="metarank",
                    reasons=["Ranked by the configured MetaRank prospect model."],
                )
        except Exception:
            pass
        return self.fallback.rank(
            account_id=account_id,
            contact_id=contact_id,
            intent=intent,
            propensity=propensity,
        )

    def rank_many(
        self,
        items: list[tuple[str, str, IntentAssessment, PropensityAssessment]],
    ) -> dict[str, RankingResult]:
        if not items:
            return {}
        event_id = f"sdr-ranking-{uuid4()}"
        payload: dict[str, Any] = {
            "event": "ranking",
            "id": event_id,
            "items": [
                {
                    "id": contact_id,
                    "fields": [
                        {"name": "account_id", "value": account_id},
                        {"name": "intent_probability", "value": intent.probability.value},
                        {"name": "reply_probability", "value": propensity.reply_probability.value},
                        {"name": "meeting_probability", "value": propensity.meeting_probability.value},
                        {
                            "name": "qualification_probability",
                            "value": propensity.qualification_probability.value,
                        },
                    ],
                }
                for account_id, contact_id, intent, propensity in items
            ],
            "user": "sdr-queue",
            "session": f"sdr-queue-{items[0][0]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if self.event_store:
            for account_id, contact_id, intent, propensity in items:
                self.event_store.append(
                    {
                        "event": "item",
                        "id": f"lead-item-{contact_id}",
                        "item": contact_id,
                        "timestamp": payload["timestamp"],
                        "fields": [
                            {
                                "name": "intent_probability",
                                "value": intent.probability.value,
                            },
                            {
                                "name": "reply_probability",
                                "value": propensity.reply_probability.value,
                            },
                            {
                                "name": "meeting_probability",
                                "value": propensity.meeting_probability.value,
                            },
                            {
                                "name": "qualification_probability",
                                "value": propensity.qualification_probability.value,
                            },
                            {"name": "account_id", "value": account_id},
                        ],
                    }
                )
            self.event_store.append(payload)
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/rank/{self.model_name}",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            raw_items = response.json().get("items", [])
            results: dict[str, RankingResult] = {}
            for index, item in enumerate(raw_items, start=1):
                contact_id = str(item.get("id", ""))
                if not contact_id:
                    continue
                raw_score = float(item.get("score", 0.0))
                normalized = 1.0 / (1.0 + pow(2.718281828, -raw_score))
                results[contact_id] = RankingResult(
                    priority_score=normalized,
                    rank=index,
                    priority_band=(
                        "high" if normalized >= 0.60
                        else "medium" if normalized >= 0.30
                        else "low"
                    ),
                    provider="metarank",
                    ranking_event_id=event_id,
                    reasons=["Queue reranked by the configured MetaRank SDR model."],
                )
            if len(results) == len(items):
                return results
        except Exception:
            pass
        fallback = getattr(self.fallback, "rank_many", None)
        if fallback:
            return fallback(items)
        return {
            contact_id: self.fallback.rank(
                account_id=account_id,
                contact_id=contact_id,
                intent=intent,
                propensity=propensity,
            )
            for account_id, contact_id, intent, propensity in items
        }

    def status(self) -> RankingSystemStatus:
        try:
            response = requests.get(
                f"{self.base_url.rstrip('/')}/health",
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return RankingSystemStatus(
                configured=True,
                reachable=True,
                model_name=self.model_name,
                active_provider="metarank",
                learned_reranking_active=True,
                detail="MetaRank is reachable; queue requests will use the configured SDR model.",
            )
        except Exception as exc:
            return RankingSystemStatus(
                configured=True,
                reachable=False,
                model_name=self.model_name,
                active_provider="local",
                learned_reranking_active=False,
                detail=f"MetaRank is unavailable; local fallback is active: {exc}",
            )

    def feedback(self, event: dict[str, Any]) -> bool:
        if self.event_store:
            self.event_store.append(event)
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/feedback",
                json=event,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return True
        except Exception:
            return False
