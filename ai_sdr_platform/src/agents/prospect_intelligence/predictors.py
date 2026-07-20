from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai_sdr_platform.src.agents.prospect_intelligence.features import feature_vector
from ai_sdr_platform.src.agents.prospect_intelligence.models import ProbabilityEstimate, ProspectFeatures

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None


class ProbabilityPredictor(Protocol):
    def predict(self, features: ProspectFeatures) -> ProbabilityEstimate:
        ...


@dataclass
class ArtifactProbabilityPredictor:
    model_path: str
    model_name: str
    model_version: str
    calibrated: bool = True

    def predict(self, features: ProspectFeatures) -> ProbabilityEstimate:
        if joblib is None:
            raise RuntimeError("joblib is required to load propensity model artifacts")
        path = Path(self.model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        artifact = joblib.load(path)
        vector = feature_vector(features)
        ordered_names = list(vector)
        row = [[vector[name] for name in ordered_names]]
        probability = float(artifact.predict_proba(row)[0][1])
        contributions = _extract_contributions(artifact, ordered_names, row)
        return ProbabilityEstimate(
            value=probability,
            mode="model",
            calibrated=self.calibrated,
            model_name=self.model_name,
            model_version=self.model_version,
            reasons=_top_reasons(contributions),
            feature_contributions=contributions,
        )


@dataclass
class HeuristicProbabilityPredictor:
    target: str
    model_version: str = "heuristic-v1"

    def predict(self, features: ProspectFeatures) -> ProbabilityEstimate:
        weights = {
            "intent": {
                "high_intent_signal_strength": 0.45,
                "buying_readiness_strength": 0.20,
                "positive_signal_strength": 0.15,
                "enrichment_confidence": 0.10,
                "negative_signal_strength": -0.25,
            },
            "reply": {
                "persona_match_score": 0.25,
                "account_fit_score": 0.20,
                "high_intent_signal_strength": 0.20,
                "buying_readiness_strength": 0.10,
                "contact_confidence": 0.10,
                "enrichment_confidence": 0.10,
                "negative_signal_strength": -0.20,
            },
            "meeting": {
                "account_fit_score": 0.20,
                "persona_match_score": 0.20,
                "high_intent_signal_strength": 0.20,
                "buying_readiness_strength": 0.20,
                "enrichment_confidence": 0.10,
                "negative_signal_strength": -0.25,
            },
            "qualification": {
                "account_fit_score": 0.30,
                "persona_match_score": 0.20,
                "buying_readiness_strength": 0.20,
                "enrichment_completeness": 0.10,
                "enrichment_confidence": 0.10,
                "negative_signal_strength": -0.25,
            },
        }[self.target]
        base = {"intent": 0.08, "reply": 0.05, "meeting": 0.02, "qualification": 0.04}[self.target]
        contributions = {
            name: float(getattr(features, name)) * weight
            for name, weight in weights.items()
        }
        value = max(0.01, min(base + sum(contributions.values()), 0.95))
        return ProbabilityEstimate(
            value=value,
            mode="heuristic",
            calibrated=False,
            model_name=f"{self.target}_heuristic",
            model_version=self.model_version,
            reasons=_top_reasons(contributions),
            feature_contributions=contributions,
        )


def _extract_contributions(artifact: object, names: list[str], row: list[list[float]]) -> dict[str, float]:
    try:
        import shap

        explainable_model = artifact
        calibrated = getattr(artifact, "calibrated_classifiers_", None)
        if calibrated:
            explainable_model = getattr(calibrated[0], "estimator", artifact)
        explainer = shap.TreeExplainer(explainable_model)
        values = explainer.shap_values(row)
        if isinstance(values, list):
            values = values[-1]
        first = values[0]
        return {name: float(first[idx]) for idx, name in enumerate(names)}
    except Exception:
        return {}


def _top_reasons(contributions: dict[str, float]) -> list[str]:
    ordered = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)
    reasons: list[str] = []
    for name, contribution in ordered[:4]:
        direction = "increased" if contribution >= 0 else "reduced"
        reasons.append(f"{name.replace('_', ' ')} {direction} the estimate")
    return reasons
