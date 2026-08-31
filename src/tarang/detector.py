from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier

from .features import extract_features, model_columns

MODEL_VERSION = "0.2.0"


@dataclass
class PredictionResult:
    """Normalized output for one security event."""

    label: str
    confidence: float
    anomaly_score: float
    anomaly: bool
    risk: str


@dataclass
class TarangDetector:
    anomaly_model: IsolationForest
    classifier: RandomForestClassifier

    @classmethod
    def train(cls, df: pd.DataFrame) -> "TarangDetector":
        engineered = extract_features(df)
        if "label" not in engineered.columns:
            raise ValueError("A 'label' column is required for supervised training")
        if len(engineered) < 100:
            raise ValueError("At least 100 labeled events are recommended for training")

        X = engineered[model_columns()]
        y = engineered["label"].astype(str)
        if y.nunique() < 2:
            raise ValueError("Training data must contain at least two label classes")

        anomaly = IsolationForest(
            n_estimators=250,
            contamination="auto",
            random_state=42,
            n_jobs=-1,
        )
        anomaly.fit(X)

        classifier = RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            min_samples_leaf=2,
        )
        classifier.fit(X, y)
        return cls(anomaly, classifier)

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score one or more raw network events."""
        engineered = extract_features(df)
        X = engineered[model_columns()]
        labels = self.classifier.predict(X)
        probabilities = self.classifier.predict_proba(X).max(axis=1)
        anomaly_flags = self.anomaly_model.predict(X) == -1
        anomaly_scores = self.anomaly_model.decision_function(X)

        out = df.copy()
        out["predicted_label"] = labels
        out["classification_confidence"] = probabilities.round(4)
        out["anomaly_score"] = anomaly_scores.round(4)
        out["anomaly_flag"] = anomaly_flags
        out["risk_level"] = [
            _risk_level(bool(flag), float(confidence))
            for flag, confidence in zip(anomaly_flags, probabilities)
        ]
        return out

    def predict_one(self, event: dict) -> PredictionResult:
        result = self.predict(pd.DataFrame([event])).iloc[0]
        return PredictionResult(
            label=str(result["predicted_label"]),
            confidence=float(result["classification_confidence"]),
            anomaly_score=float(result["anomaly_score"]),
            anomaly=bool(result["anomaly_flag"]),
            risk=str(result["risk_level"]),
        )

    def save(self, directory: str | Path = "artifacts") -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"version": MODEL_VERSION, "model": self.anomaly_model},
            path / "isolation_forest.joblib",
        )
        joblib.dump(
            {"version": MODEL_VERSION, "model": self.classifier},
            path / "random_forest.joblib",
        )

    @classmethod
    def load(cls, directory: str | Path = "artifacts") -> "TarangDetector":
        path = Path(directory)
        anomaly_bundle = joblib.load(path / "isolation_forest.joblib")
        classifier_bundle = joblib.load(path / "random_forest.joblib")
        return cls(anomaly_bundle["model"], classifier_bundle["model"])


def _risk_level(anomaly: bool, confidence: float) -> str:
    if anomaly and confidence >= 0.75:
        return "high"
    if anomaly or confidence < 0.60:
        return "medium"
    return "low"
