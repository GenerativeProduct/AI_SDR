from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from ai_sdr_platform.src.agents.prospect_intelligence.features import feature_vector
from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    ModelTrainingRequest,
    ModelTrainingResponse,
    ProspectOutcome,
    TrainedModelSummary,
)
from ai_sdr_platform.src.agents.prospect_intelligence.repository import ProspectIntelligenceRepository

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover
    LGBMClassifier = None

try:
    import mlflow
except Exception:  # pragma: no cover
    mlflow = None


@dataclass
class ProspectModelTrainer:
    repository: ProspectIntelligenceRepository
    mlflow_tracking_uri: str | None = None

    def train(self, request: ModelTrainingRequest) -> ModelTrainingResponse:
        rows = self.repository.list_training_rows()
        summaries = [self._train_target(target, rows, request) for target in request.targets]
        return ModelTrainingResponse(models=summaries)

    def _train_target(self, target: str, rows: list[tuple], request: ModelTrainingRequest) -> TrainedModelSummary:
        labels = [self._label(target, outcome) for _, outcome in rows]
        sample_count = len(labels)
        positive_count = sum(labels)
        if sample_count < request.minimum_samples:
            return TrainedModelSummary(
                target=target,
                trained=False,
                sample_count=sample_count,
                positive_count=positive_count,
                reason=f"At least {request.minimum_samples} labeled outcomes are required.",
            )
        if len(set(labels)) < 2:
            return TrainedModelSummary(
                target=target,
                trained=False,
                sample_count=sample_count,
                positive_count=positive_count,
                reason="Both positive and negative outcomes are required.",
            )
        negative_count = sample_count - positive_count
        if min(positive_count, negative_count) < 5:
            return TrainedModelSummary(
                target=target,
                trained=False,
                sample_count=sample_count,
                positive_count=positive_count,
                reason="At least five positive and five negative outcomes are required for calibration.",
            )

        feature_rows = [feature_vector(result.features) for result, _ in rows]
        feature_names = list(feature_rows[0])
        x = np.asarray([[row[name] for name in feature_names] for row in feature_rows], dtype=float)
        y = np.asarray(labels, dtype=int)
        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )

        base_model = (
            LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                num_leaves=15,
                random_state=42,
                class_weight="balanced",
            )
            if LGBMClassifier is not None
            else HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=42)
        )
        class_counts = np.bincount(y_train, minlength=2)
        if int(class_counts.min()) < 2:
            return TrainedModelSummary(
                target=target,
                trained=False,
                sample_count=sample_count,
                positive_count=positive_count,
                reason="Training split does not contain enough examples per class for calibration.",
            )
        calibration_cv = min(5, int(class_counts.min()))
        model = CalibratedClassifierCV(base_model, method="sigmoid", cv=calibration_cv)
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        metrics = {"brier_score": float(brier_score_loss(y_test, probabilities))}
        if len(set(y_test.tolist())) == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities))

        version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_dir = Path(request.artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"{target}-{version}.joblib"
        joblib.dump(model, artifact_path)
        self._log_mlflow(target, version, metrics, sample_count, positive_count, artifact_path)
        return TrainedModelSummary(
            target=target,
            trained=True,
            sample_count=sample_count,
            positive_count=positive_count,
            artifact_path=str(artifact_path.resolve()),
            model_name="lightgbm" if LGBMClassifier is not None else "hist_gradient_boosting",
            model_version=version,
            calibrated=True,
            metrics=metrics,
        )

    def _log_mlflow(
        self,
        target: str,
        version: str,
        metrics: dict[str, float],
        sample_count: int,
        positive_count: int,
        artifact_path: Path,
    ) -> None:
        if mlflow is None or not self.mlflow_tracking_uri:
            return
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment("ai-sdr-prospect-intelligence")
        with mlflow.start_run(run_name=f"{target}-{version}"):
            mlflow.log_params(
                {
                    "target": target,
                    "sample_count": sample_count,
                    "positive_count": positive_count,
                    "calibration": "sigmoid",
                }
            )
            mlflow.log_metrics(metrics)
            mlflow.log_artifact(str(artifact_path))

    @staticmethod
    def _label(target: str, outcome: ProspectOutcome) -> int:
        if target == "reply":
            return int(outcome.positive_reply or outcome.replied)
        if target == "meeting":
            return int(outcome.meeting_booked)
        return int(outcome.qualified or outcome.opportunity_created)
