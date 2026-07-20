from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV


FEATURE_NAMES = [
    "account_fit_score",
    "persona_match_score",
    "contact_confidence",
    "enrichment_confidence",
    "enrichment_completeness",
    "positive_signal_strength",
    "negative_signal_strength",
    "high_intent_signal_strength",
    "buying_readiness_strength",
    "signal_count_log",
    "verified_signal_count_log",
]

TARGET_WEIGHTS = {
    "intent": {
        "intercept": -2.2,
        "account_fit_score": 0.35,
        "persona_match_score": 0.25,
        "contact_confidence": 0.10,
        "enrichment_confidence": 0.55,
        "enrichment_completeness": 0.40,
        "positive_signal_strength": 0.70,
        "negative_signal_strength": -1.40,
        "high_intent_signal_strength": 2.40,
        "buying_readiness_strength": 1.45,
        "signal_count_log": 0.22,
        "verified_signal_count_log": 0.45,
    },
    "reply": {
        "intercept": -1.7,
        "account_fit_score": 0.80,
        "persona_match_score": 1.10,
        "contact_confidence": 0.80,
        "enrichment_confidence": 0.50,
        "enrichment_completeness": 0.25,
        "positive_signal_strength": 0.55,
        "negative_signal_strength": -1.25,
        "high_intent_signal_strength": 0.90,
        "buying_readiness_strength": 0.55,
        "signal_count_log": 0.12,
        "verified_signal_count_log": 0.20,
    },
    "meeting": {
        "intercept": -2.15,
        "account_fit_score": 0.75,
        "persona_match_score": 0.95,
        "contact_confidence": 0.45,
        "enrichment_confidence": 0.40,
        "enrichment_completeness": 0.30,
        "positive_signal_strength": 0.55,
        "negative_signal_strength": -1.30,
        "high_intent_signal_strength": 1.10,
        "buying_readiness_strength": 1.20,
        "signal_count_log": 0.12,
        "verified_signal_count_log": 0.25,
    },
    "qualification": {
        "intercept": -1.85,
        "account_fit_score": 1.35,
        "persona_match_score": 0.95,
        "contact_confidence": 0.35,
        "enrichment_confidence": 0.55,
        "enrichment_completeness": 0.65,
        "positive_signal_strength": 0.45,
        "negative_signal_strength": -1.45,
        "high_intent_signal_strength": 0.55,
        "buying_readiness_strength": 1.10,
        "signal_count_log": 0.18,
        "verified_signal_count_log": 0.30,
    },
}


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def synthetic_features(rows: int = 6000, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = rng.beta(2.0, 2.0, size=(rows, len(FEATURE_NAMES)))
    signal_count_idx = FEATURE_NAMES.index("signal_count_log")
    verified_count_idx = FEATURE_NAMES.index("verified_signal_count_log")
    high_intent_idx = FEATURE_NAMES.index("high_intent_signal_strength")
    readiness_idx = FEATURE_NAMES.index("buying_readiness_strength")
    positive_idx = FEATURE_NAMES.index("positive_signal_strength")
    negative_idx = FEATURE_NAMES.index("negative_signal_strength")

    raw_signal_count = rng.poisson(lam=2.2 + 4.0 * x[:, positive_idx], size=rows)
    raw_verified_count = np.minimum(
        raw_signal_count,
        rng.poisson(lam=0.4 + 2.5 * x[:, high_intent_idx], size=rows),
    )
    x[:, signal_count_idx] = np.log1p(raw_signal_count)
    x[:, verified_count_idx] = np.log1p(raw_verified_count)

    negative_mask = rng.random(rows) < 0.18
    x[~negative_mask, negative_idx] *= 0.25
    x[:, readiness_idx] = np.maximum(
        x[:, readiness_idx],
        0.55 * x[:, high_intent_idx] + 0.35 * x[:, positive_idx],
    ).clip(0.0, 1.0)
    return x


def labels_for(target: str, x: np.ndarray, seed: int) -> np.ndarray:
    weights = TARGET_WEIGHTS[target]
    linear = np.full(x.shape[0], float(weights["intercept"]))
    for idx, name in enumerate(FEATURE_NAMES):
        linear += float(weights[name]) * x[:, idx]
    probabilities = sigmoid(linear)
    rng = np.random.default_rng(seed)
    return (rng.random(x.shape[0]) < probabilities).astype(int)


def train_target(target: str, x: np.ndarray, out_dir: Path) -> Path:
    y = labels_for(target, x, seed=100 + len(target))
    base_model = LGBMClassifier(
        n_estimators=180,
        learning_rate=0.045,
        num_leaves=17,
        min_child_samples=30,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        class_weight="balanced",
        verbosity=-1,
    )
    model = CalibratedClassifierCV(base_model, method="sigmoid", cv=5)
    model.fit(x, y)
    artifact_path = out_dir / f"{target}-bootstrap-lightgbm.joblib"
    joblib.dump(model, artifact_path)
    return artifact_path


def main() -> None:
    out_dir = Path("ai_sdr_platform/models/prospect_intelligence/bootstrap")
    out_dir.mkdir(parents=True, exist_ok=True)
    x = synthetic_features()
    paths = {target: train_target(target, x, out_dir) for target in TARGET_WEIGHTS}
    print("Bootstrap Prospect Intelligence ML artifacts created:")
    for target, path in paths.items():
        print(f"{target}={path.resolve()}")


if __name__ == "__main__":
    main()
