from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NSLKDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins",
    "logged_in", "num_compromised", "root_shell", "su_attempted",
    "num_root", "num_file_creations", "num_shells", "num_access_files",
    "num_outbound_cmds", "is_host_login", "is_guest_login", "count",
    "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate",
    "srv_rerror_rate", "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate",
    "dst_host_count", "dst_host_srv_count", "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "label", "difficulty",
]

CATEGORICAL = ["protocol_type", "service", "flag"]
TARGET = "label"

@dataclass
class HybridBenchmarkModel:
    preprocessor: ColumnTransformer
    anomaly_model: IsolationForest
    classifier: RandomForestClassifier
    if_threshold: float
    rf_threshold: float
    hybrid_threshold: float
    hybrid_weight: float
    if_min: float
    if_max: float
    feature_names: list[str]

    def transform(self, frame: pd.DataFrame):
        clean = frame[NSLKDD_COLUMNS[:-2]].copy()
        return self.preprocessor.transform(clean)

def load_nsl_kdd(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    frame = pd.read_csv(path, sep="\t", header=None, names=NSLKDD_COLUMNS)
    if frame.shape[1] != len(NSLKDD_COLUMNS):
        raise ValueError(f"Expected {len(NSLKDD_COLUMNS)} NSL-KDD columns, got {frame.shape[1]}.")
    frame["label"] = frame["label"].astype(str).str.strip().str.lower().str.rstrip(".")
    frame["difficulty"] = pd.to_numeric(frame["difficulty"], errors="coerce")
    return frame

def build_preprocessor() -> ColumnTransformer:
    numeric = [c for c in NSLKDD_COLUMNS[:-2] if c not in CATEGORICAL]
    categorical = CATEGORICAL
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, numeric),
        ("cat", categorical_pipe, categorical),
    ])

def binary_labels(frame: pd.DataFrame) -> np.ndarray:
    return (frame["label"].to_numpy() != "normal").astype(int)

def _best_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    candidates = np.unique(np.quantile(scores, np.linspace(0.02, 0.98, 99)))
    best_threshold, best_f1 = 0.5, -1.0
    for threshold in candidates:
        pred = (scores >= threshold).astype(int)
        score = f1_score(y_true, pred, zero_division=0)
        if score > best_f1:
            best_threshold, best_f1 = float(threshold), float(score)
    return best_threshold, best_f1

def _minmax(values: np.ndarray, low: float, high: float) -> np.ndarray:
    scale = max(high - low, 1e-12)
    return np.clip((values - low) / scale, 0.0, 1.0)

def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray, score: np.ndarray | None = None) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 4),
        "confusion_matrix": cm.tolist(),
        "support": {"benign": int((y_true == 0).sum()), "attack": int((y_true == 1).sum())},
    }
    if score is not None and len(np.unique(y_true)) == 2:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, score)), 4)
        metrics["average_precision"] = round(float(average_precision_score(y_true, score)), 4)
    return metrics

def fit_hybrid(train_df: pd.DataFrame, validation_size: float = 0.20, random_state: int = 42) -> tuple[HybridBenchmarkModel, dict]:
    y = binary_labels(train_df)
    train_part, val_part = train_test_split(
        train_df,
        test_size=validation_size,
        random_state=random_state,
        stratify=y,
    )
    y_train = binary_labels(train_part)
    y_val = binary_labels(val_part)

    preprocessor = build_preprocessor()
    X_train = preprocessor.fit_transform(train_part[NSLKDD_COLUMNS[:-2]])
    X_val = preprocessor.transform(val_part[NSLKDD_COLUMNS[:-2]])

    anomaly_model = IsolationForest(
        n_estimators=300,
        contamination="auto",
        max_samples="auto",
        random_state=random_state,
        n_jobs=-1,
    )
    benign_mask = y_train == 0
    if benign_mask.sum() < 100:
        raise ValueError("Not enough benign training rows for Isolation Forest.")
    anomaly_model.fit(X_train[benign_mask])

    classifier = RandomForestClassifier(
        n_estimators=400,
        class_weight="balanced_subsample",
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1,
    )
    classifier.fit(X_train, y_train)

    if_scores = -anomaly_model.decision_function(X_val)
    rf_scores = classifier.predict_proba(X_val)[:, 1]

    if_threshold, _ = _best_threshold(y_val, if_scores)
    rf_threshold, _ = _best_threshold(y_val, rf_scores)

    if_min, if_max = float(if_scores.min()), float(if_scores.max())
    if_norm = _minmax(if_scores, if_min, if_max)
    best_weight, best_threshold, best_f1 = 0.5, 0.5, -1.0
    for weight in np.linspace(0.1, 0.9, 17):
        candidate_score = weight * if_norm + (1.0 - weight) * rf_scores
        candidate_threshold, candidate_f1 = _best_threshold(y_val, candidate_score)
        if candidate_f1 > best_f1:
            best_weight, best_threshold, best_f1 = float(weight), candidate_threshold, candidate_f1
    hybrid_threshold = best_threshold

    model = HybridBenchmarkModel(
        preprocessor=preprocessor,
        anomaly_model=anomaly_model,
        classifier=classifier,
        if_threshold=if_threshold,
        rf_threshold=rf_threshold,
        hybrid_threshold=hybrid_threshold,
        hybrid_weight=best_weight,
        if_min=if_min,
        if_max=if_max,
        feature_names=list(preprocessor.get_feature_names_out()),
    )

    validation_metrics = {
        "isolation_forest": binary_metrics(y_val, (if_scores >= if_threshold).astype(int), if_scores),
        "random_forest": binary_metrics(y_val, (rf_scores >= rf_threshold).astype(int), rf_scores),
        "hybrid": binary_metrics(y_val, (hybrid_score >= hybrid_threshold).astype(int), hybrid_score),
    }
    return model, validation_metrics

def evaluate(model: HybridBenchmarkModel, test_df: pd.DataFrame) -> dict:
    y_true = binary_labels(test_df)
    X_test = model.transform(test_df)

    if_scores = -model.anomaly_model.decision_function(X_test)
    rf_scores = model.classifier.predict_proba(X_test)[:, 1]
    if_norm = _minmax(if_scores, model.if_min, model.if_max)
    hybrid_score = model.hybrid_weight * if_norm + (1.0 - model.hybrid_weight) * rf_scores

    predictions = {
        "isolation_forest": (if_scores >= model.if_threshold).astype(int),
        "random_forest": (rf_scores >= model.rf_threshold).astype(int),
        "hybrid": (hybrid_score >= model.hybrid_threshold).astype(int),
    }

    metrics = {
        name: binary_metrics(y_true, pred, score)
        for (name, pred), score in zip(
            predictions.items(),
            [if_scores, rf_scores, hybrid_score],
        )
    }

    return {
        "dataset": "NSL-KDD",
        "protocol": {
            "train_file": "KDDTrain+.txt",
            "test_file": "KDDTest+.txt",
            "positive_class": "attack = any label other than normal",
            "isolation_forest_training": "benign training rows only",
            "threshold_selection": "validation split from KDDTrain+",
            "test_usage": "untouched until final evaluation",
        },
        "rows": {
            "train": int(len(test_df) + 0),  # overwritten by caller when saved
            "test": int(len(test_df)),
            "test_benign": int((y_true == 0).sum()),
            "test_attack": int((y_true == 1).sum()),
        },
        "thresholds": {
            "isolation_forest": model.if_threshold,
            "random_forest": model.rf_threshold,
            "hybrid": model.hybrid_threshold,
            "hybrid_weight": model.hybrid_weight,
        },
        "metrics": metrics,
    }

def save_bundle(model: HybridBenchmarkModel, metrics: dict, train_rows: int, directory: str | Path) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, directory / "hybrid_nsl_kdd.joblib")
    payload = dict(metrics)
    payload["rows"]["train"] = int(train_rows)
    payload["feature_count_after_encoding"] = len(model.feature_names)
    (directory / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.Series(model.feature_names, name="feature").to_csv(directory / "features.csv", index=False)

def benchmark_predictions(model: HybridBenchmarkModel, test_df: pd.DataFrame) -> pd.DataFrame:
    """Return per-record benchmark predictions without exposing test labels to training."""
    X_test = model.transform(test_df)
    if_scores = -model.anomaly_model.decision_function(X_test)
    rf_scores = model.classifier.predict_proba(X_test)[:, 1]
    if_norm = _minmax(if_scores, model.if_min, model.if_max)
    hybrid_score = 0.5 * if_norm + 0.5 * rf_scores
    frame = test_df[["label", "difficulty"]].copy()
    frame["true_binary"] = binary_labels(test_df)
    frame["if_score"] = if_scores
    frame["if_predicted"] = (if_scores >= model.if_threshold).astype(int)
    frame["rf_attack_probability"] = rf_scores
    frame["rf_predicted"] = (rf_scores >= model.rf_threshold).astype(int)
    frame["hybrid_weight"] = model.hybrid_weight
    frame["hybrid_score"] = hybrid_score
    frame["hybrid_predicted"] = (hybrid_score >= model.hybrid_threshold).astype(int)
    return frame
