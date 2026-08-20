from __future__ import annotations

from dataclasses import dataclass, field

from ai_sdr_platform.src.agents.qualification.evaluators import (
    BANTEvaluator,
    MEDDICEvaluator,
)
from ai_sdr_platform.src.agents.qualification.models import (
    QualificationRequest,
    QualificationResult,
)
from ai_sdr_platform.src.shared.config import settings
from ai_sdr_platform.src.agents.qualification.repository import (
    QualificationRepository,
)


@dataclass
class QualificationService:
    repository: QualificationRepository
    bant_evaluator: BANTEvaluator = field(default_factory=BANTEvaluator)
    meddic_evaluator: MEDDICEvaluator = field(default_factory=MEDDICEvaluator)

    def qualify(self, request: QualificationRequest) -> QualificationResult:
        bant = self.bant_evaluator.evaluate(request) if "BANT" in request.frameworks else None
        meddic = (
            self.meddic_evaluator.evaluate(request)
            if "MEDDIC" in request.frameworks
            else None
        )
        framework_scores = [
            assessment.score for assessment in (bant, meddic) if assessment is not None
        ]
        framework_score = (
            sum(framework_scores) / len(framework_scores) if framework_scores else 0.0
        )
        ml_estimate = request.intelligence.propensity.qualification_probability
        score = round(ml_estimate.value * 100 * 0.55 + framework_score * 0.45)
        missing = sorted(
            {
                item
                for assessment in (bant, meddic)
                if assessment is not None
                for criterion in self._criteria(assessment)
                for item in criterion.missing_information
            }
        )
        status, tier, sales_ready, next_action = self._recommend(score, missing)
        reasoning = [
            f"Calibrated ML qualification probability: {ml_estimate.value:.0%}.",
            f"Qualification framework evidence score: {framework_score:.0f}/100.",
            f"Combined hybrid qualification score: {score}/100.",
        ]
        if missing:
            reasoning.append(
                f"{len(missing)} qualification evidence gaps require SDR confirmation."
            )
        result = QualificationResult(
            intelligence_id=request.intelligence.intelligence_id,
            account_id=request.intelligence.account_id,
            contact_id=request.intelligence.contact_id,
            company_name=request.intelligence.company_name,
            contact_name=request.intelligence.contact_name,
            bant=bant,
            meddic=meddic,
            ml_qualification_probability=ml_estimate.value,
            qualification_score=score,
            qualification_tier=tier,
            qualification_status=status,
            sales_ready=sales_ready,
            next_action=next_action,
            reasoning=reasoning,
            missing_information=missing,
            model_version=ml_estimate.model_version,
            metadata={
                "ml_model_name": ml_estimate.model_name,
                "ml_calibrated": ml_estimate.calibrated,
                "ml_prediction_mode": ml_estimate.mode,
                "ranking_event_id": request.intelligence.ranking.ranking_event_id,
            },
            created_by=request.created_by,
        )
        return self.repository.save(result)

    def get_latest(self, contact_id: str) -> QualificationResult | None:
        return self.repository.get_latest(contact_id)

    def list_results(self, account_id: str | None = None) -> list[QualificationResult]:
        return self.repository.list_latest(account_id)

    @staticmethod
    def _criteria(assessment: object) -> list[object]:
        if hasattr(assessment, "budget"):
            return [
                assessment.budget,
                assessment.authority,
                assessment.need,
                assessment.timeline,
            ]
        return [
            assessment.metrics,
            assessment.economic_buyer,
            assessment.decision_criteria,
            assessment.decision_process,
            assessment.identified_pain,
            assessment.champion,
        ]

    @staticmethod
    def _recommend(
        score: int, missing: list[str]
    ) -> tuple[str, str, bool, str]:
        if score >= settings.qualification_sql_threshold and len(missing) <= 3:
            return "SQL", "Tier 1", True, "Push to Outreach"
        if score >= settings.qualification_mql_threshold:
            return "MQL", "Tier 2", False, "Assign SDR to validate missing qualification evidence"
        if score >= settings.qualification_nurture_threshold:
            return "Nurture", "Tier 3", False, "Nurture and collect qualification evidence"
        return "Disqualified", "Tier 3", False, "Do not prioritize for active outreach"
