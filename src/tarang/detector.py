from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report

from .features import extract_features, model_columns


@dataclass
class TarangDetector:
    anomaly_model: IsolationForest
    classifier: RandomForestClassifier

    @classmethod
    def train(cls, df: pd.DataFrame) -> tuple["TarangDetector", str]:
        engineered = extract_features(df)
        X = engineered[model_columns()]
        y = engineered["label"].astype(str) if "label" in engineered.columns else None

        anomaly = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42,
        )
        anomaly.fit(X)

        classifier = RandomForestClassifier(
            n_estimators=250,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        if y is None:
            raise ValueError("A 'label' column is required to train the supervised classifier")
        classifier.fit(X, y)

        detector = cls(anomaly, classifier)
        metrics = ""
        predictions = classifier.predict(X)
        metrics = classification_report(y, predictions, zero_division=0)
        return detector, metrics

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        engineered = extract_features(df)
        X = engineered[model_columns()]
        out = df.copy()
        out["predicted_label"] = self.classifier.predict(X)
        probabilities = self.classifier.predict_proba(X).max(axis=1)
        out["classification_confidence"] = probabilities.round(4)
        anomaly = self.anomaly_model.decision_function(X)
        out["anomaly_score"] = anomaly.round(4)
        out["anomaly_flag"] = self.anomaly_model.predict(X).eq(-1)
        out["risk_level"] = out.apply(_risk_level, axis=1)
        return out

    def save(self, directory: str | Path = "artifacts") -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.anomaly_model, path / "isolation_forest.joblib")
        joblib.dump(self.classifier, path / "random_forest.joblib")


def _risk_level(row: pd.Series) -> str:
    if row["anomaly_flag"] and row["classification_confidence"] >= 0.75:
        return "high"
    if row["anomaly_flag"] or row["classification_confidence"] < 0.60:
        return "medium"
    return "low"
