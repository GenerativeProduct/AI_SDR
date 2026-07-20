from __future__ import annotations

from dataclasses import dataclass, field

from ai_sdr_platform.src.agents.prospect_intelligence.features import build_features
from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    IntentAssessment,
    PropensityAssessment,
    ProspectIntelligenceRequest,
    ProspectIntelligenceResult,
    ProspectOutcome,
    RankingSystemStatus,
)
from ai_sdr_platform.src.agents.prospect_intelligence.monitoring import IntelligenceMonitor
from ai_sdr_platform.src.agents.prospect_intelligence.personalization import PersonalizationAgent
from ai_sdr_platform.src.agents.prospect_intelligence.predictors import (
    HeuristicProbabilityPredictor,
    ProbabilityPredictor,
)
from ai_sdr_platform.src.agents.prospect_intelligence.ranking import LocalRankingProvider, RankingProvider
from ai_sdr_platform.src.agents.prospect_intelligence.repository import ProspectIntelligenceRepository
from ai_sdr_platform.src.agents.prospect_intelligence.signals import normalize_enrichment_signals


@dataclass
class ProspectIntelligenceService:
    repository: ProspectIntelligenceRepository
    intent_predictor: ProbabilityPredictor = field(
        default_factory=lambda: HeuristicProbabilityPredictor("intent")
    )
    reply_predictor: ProbabilityPredictor = field(
        default_factory=lambda: HeuristicProbabilityPredictor("reply")
    )
    meeting_predictor: ProbabilityPredictor = field(
        default_factory=lambda: HeuristicProbabilityPredictor("meeting")
    )
    qualification_predictor: ProbabilityPredictor = field(
        default_factory=lambda: HeuristicProbabilityPredictor("qualification")
    )
    ranking_provider: RankingProvider = field(default_factory=LocalRankingProvider)
    personalization_agent: PersonalizationAgent = field(default_factory=PersonalizationAgent)
    monitor: IntelligenceMonitor = field(default_factory=IntelligenceMonitor)

    def analyze(self, request: ProspectIntelligenceRequest) -> ProspectIntelligenceResult:
        signals = normalize_enrichment_signals(request.enrichment)
        features = build_features(request.account, request.contact, request.enrichment, signals)

        intent_probability = self.intent_predictor.predict(features)
        intent_level = (
            "high" if intent_probability.value >= 0.70
            else "medium" if intent_probability.value >= 0.35
            else "low"
        )
        intent = IntentAssessment(
            probability=intent_probability,
            level=intent_level,
            detected_signals=[
                signal
                for signal in signals
                if signal.signal_type in {"web_intent", "outreach_engagement", "funding", "hiring", "expansion"}
            ],
            recommended_timing=(
                "within_24_hours" if intent_level == "high"
                else "within_3_business_days" if intent_level == "medium"
                else "monitor"
            ),
        )

        propensity = PropensityAssessment(
            reply_probability=self.reply_predictor.predict(features),
            meeting_probability=self.meeting_predictor.predict(features),
            qualification_probability=self.qualification_predictor.predict(features),
        )
        ranking = self.ranking_provider.rank(
            account_id=request.account.account_id,
            contact_id=request.contact.contact_id,
            intent=intent,
            propensity=propensity,
        )
        personalization = self.personalization_agent.generate(request, signals, propensity)
        estimates = [
            intent.probability,
            propensity.reply_probability,
            propensity.meeting_probability,
            propensity.qualification_probability,
        ]
        warnings = []
        if any(estimate.mode == "heuristic" for estimate in estimates):
            warnings.append(
                "One or more probabilities use heuristic fallback estimates because trained model artifacts are not configured."
            )
        if not signals:
            warnings.append("No normalized enrichment signals were available; intelligence confidence is limited.")

        result = ProspectIntelligenceResult(
            account_id=request.account.account_id,
            contact_id=request.contact.contact_id,
            company_name=request.account.company_name,
            contact_name=request.contact.full_name,
            signals=signals,
            features=features,
            intent=intent,
            propensity=propensity,
            ranking=ranking,
            personalization=personalization,
            model_versions={
                "intent": intent.probability.model_version,
                "reply": propensity.reply_probability.model_version,
                "meeting": propensity.meeting_probability.model_version,
                "qualification": propensity.qualification_probability.model_version,
                "ranking": ranking.provider,
            },
            warnings=warnings,
            created_by=request.created_by,
        )
        saved = self.repository.save(result)
        self.monitor.record(saved)
        return saved

    def get_latest(self, contact_id: str) -> ProspectIntelligenceResult | None:
        return self.repository.get_latest(contact_id)

    def list_results(self, account_id: str | None = None) -> list[ProspectIntelligenceResult]:
        return self.repository.list_latest(account_id=account_id)

    def record_outcome(self, outcome: ProspectOutcome) -> ProspectOutcome:
        return self.repository.save_outcome(outcome)

    def rerank_results(
        self, results: list[ProspectIntelligenceResult]
    ) -> list[ProspectIntelligenceResult]:
        ranking_by_contact = self.ranking_provider.rank_many(
            [
                (result.account_id, result.contact_id, result.intent, result.propensity)
                for result in results
            ]
        )
        for result in results:
            if result.contact_id in ranking_by_contact:
                result.ranking = ranking_by_contact[result.contact_id]
                result.model_versions["ranking"] = result.ranking.provider
                self.repository.save(result)
        return sorted(results, key=lambda item: item.ranking.rank or 10**9)

    def ranking_status(self) -> RankingSystemStatus:
        return self.ranking_provider.status()

    def send_ranking_feedback(self, event: dict[str, object]) -> bool:
        sender = getattr(self.ranking_provider, "feedback", None)
        return bool(sender and sender(event))
