from __future__ import annotations

from dataclasses import dataclass

from ai_sdr_platform.src.agents.qualification.models import (
    BANTAssessment,
    FrameworkCriterion,
    MEDDICAssessment,
    QualificationRequest,
)


def _criterion(
    name: str,
    score: float,
    confidence: float,
    evidence: list[str],
    missing: list[str] | None = None,
) -> FrameworkCriterion:
    return FrameworkCriterion(
        name=name,
        score=round(max(0.0, min(score, 100.0))),
        confidence=max(0.0, min(confidence, 1.0)),
        evidence=evidence,
        missing_information=missing or [],
    )


def _title_authority(title: str, seniority: str) -> tuple[int, list[str]]:
    value = f"{title} {seniority}".lower()
    executive = ("chief", "c-level", "vp", "vice president", "president", "founder")
    decision_maker = ("head", "director", "owner")
    influencer = ("manager", "lead")
    if any(token in value for token in executive):
        return 95, [f"Executive decision-maker role identified: {title}"]
    if any(token in value for token in decision_maker):
        return 82, [f"Senior decision-maker role identified: {title}"]
    if any(token in value for token in influencer):
        return 65, [f"Likely evaluator or influencer role identified: {title}"]
    return 35, []


@dataclass
class BANTEvaluator:
    def evaluate(self, request: QualificationRequest) -> BANTAssessment:
        intel = request.intelligence
        enrichment = request.enrichment
        contact = request.contact

        revenue = str(
            enrichment.raw_search.get("account", {}).get("revenue_range")
            or enrichment.raw_search.get("revenue_range")
            or ""
        )
        employee_count = enrichment.raw_search.get("account", {}).get("employee_count")
        budget_evidence: list[str] = []
        budget_missing: list[str] = []
        budget_score = 40
        if revenue:
            budget_score = 75
            budget_evidence.append(f"Reported company revenue range: {revenue}")
        elif isinstance(employee_count, int) and employee_count >= 200:
            budget_score = 65
            budget_evidence.append(
                f"Company size of {employee_count} employees suggests established budget."
            )
        else:
            budget_missing.append("Validated budget or revenue evidence")

        authority_score, authority_evidence = _title_authority(
            contact.title, contact.seniority
        )
        authority_missing = [] if authority_evidence else ["Confirmed decision authority"]

        intent = intel.intent.probability.value
        qualification = intel.propensity.qualification_probability.value
        pain_count = len(enrichment.pain_point_hypotheses)
        need_score = min(100.0, (intent * 45) + (qualification * 35) + pain_count * 7)
        need_evidence = [
            f"ML intent probability is {intent:.0%}.",
            f"ML qualification probability is {qualification:.0%}.",
        ]
        if pain_count:
            need_evidence.append(f"{pain_count} evidence-backed pain hypotheses identified.")

        readiness = intel.features.buying_readiness_strength
        timeline_score = min(100.0, readiness * 80 + intent * 20)
        timeline_evidence = [
            f"Buying-readiness signal strength is {readiness:.0%}.",
            f"Recommended timing: {intel.intent.recommended_timing}.",
        ]

        budget = _criterion(
            "Budget", budget_score, 0.45 if budget_missing else 0.75, budget_evidence, budget_missing
        )
        authority = _criterion(
            "Authority",
            authority_score,
            0.55 if authority_missing else 0.85,
            authority_evidence,
            authority_missing,
        )
        need = _criterion("Need", need_score, 0.85, need_evidence)
        timeline = _criterion("Timeline", timeline_score, 0.75, timeline_evidence)
        overall = round(
            budget.score * 0.20
            + authority.score * 0.30
            + need.score * 0.30
            + timeline.score * 0.20
        )
        return BANTAssessment(
            score=overall,
            budget=budget,
            authority=authority,
            need=need,
            timeline=timeline,
        )


@dataclass
class MEDDICEvaluator:
    def evaluate(self, request: QualificationRequest) -> MEDDICAssessment:
        intel = request.intelligence
        enrichment = request.enrichment
        contact = request.contact
        qualification = intel.propensity.qualification_probability.value
        meeting = intel.propensity.meeting_probability.value
        intent = intel.intent.probability.value
        authority_score, authority_evidence = _title_authority(
            contact.title, contact.seniority
        )

        metrics = _criterion(
            "Metrics",
            qualification * 70 + intel.features.enrichment_completeness * 30,
            0.65,
            [
                f"ML qualification probability is {qualification:.0%}.",
                f"Enrichment completeness is {intel.features.enrichment_completeness:.0%}.",
            ],
            ["Quantified business impact or ROI target"],
        )
        economic_buyer = _criterion(
            "Economic Buyer",
            authority_score,
            0.55 if not authority_evidence else 0.80,
            authority_evidence,
            [] if authority_evidence else ["Named economic buyer and purchasing authority"],
        )
        signal_count = len(intel.signals)
        decision_criteria = _criterion(
            "Decision Criteria",
            min(100, 35 + signal_count * 8 + len(enrichment.personalization_angles) * 6),
            0.65,
            [f"{signal_count} normalized buying signals available."],
            ["Confirmed technical and commercial evaluation criteria"],
        )
        decision_process = _criterion(
            "Decision Process",
            meeting * 45 + intent * 35 + intel.features.buying_readiness_strength * 20,
            0.55,
            [
                f"ML meeting probability is {meeting:.0%}.",
                f"Intent probability is {intent:.0%}.",
            ],
            ["Confirmed procurement steps, stakeholders, and approval process"],
        )
        pain_count = len(enrichment.pain_point_hypotheses)
        identified_pain = _criterion(
            "Identify Pain",
            min(100, 30 + pain_count * 16 + intent * 25),
            0.80 if pain_count else 0.40,
            enrichment.pain_point_hypotheses[:5],
            [] if pain_count else ["Validated business pain"],
        )
        champion_score = min(
            100,
            intent * 45 + intel.propensity.reply_probability.value * 30 + authority_score * 0.25,
        )
        champion = _criterion(
            "Champion",
            champion_score,
            0.45,
            [f"Reply propensity is {intel.propensity.reply_probability.value:.0%}."],
            ["Confirmed internal champion"],
        )
        criteria = [
            metrics,
            economic_buyer,
            decision_criteria,
            decision_process,
            identified_pain,
            champion,
        ]
        return MEDDICAssessment(
            score=round(sum(item.score for item in criteria) / len(criteria)),
            metrics=metrics,
            economic_buyer=economic_buyer,
            decision_criteria=decision_criteria,
            decision_process=decision_process,
            identified_pain=identified_pain,
            champion=champion,
        )
