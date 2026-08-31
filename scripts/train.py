from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tarang.detector import TarangDetector, MODEL_VERSION


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the Tarang threat detector")
    parser.add_argument("--input", type=Path, default=Path("data/network_events.csv"))
    parser.add_argument("--model-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--test-size", type=float, default=0.20)
    args = parser.parse_args()

    if not 0.10 <= args.test_size <= 0.40:
        raise ValueError("--test-size must be between 0.10 and 0.40")
    if not args.input.exists():
        raise FileNotFoundError(f"Dataset not found: {args.input}")

    df = pd.read_csv(args.input)
    if "label" not in df.columns:
        raise ValueError("Dataset must contain a 'label' column")

    train_df, test_df = train_test_split(
        df,
        test_size=args.test_size,
        random_state=42,
        stratify=df["label"],
    )

    detector = TarangDetector.train(train_df)
    predictions = detector.predict(test_df)
    args.model_dir.mkdir(parents=True, exist_ok=True)
    detector.save(args.model_dir)

    y_true = test_df["label"].astype(str)
    y_pred = predictions["predicted_label"].astype(str)
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    metrics = {
        "model_version": MODEL_VERSION,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "classification_report": report,
    }

    (args.model_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    predictions.to_csv(args.model_dir / "predictions.csv", index=False)

    print(f"Held-out accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")
    print(f"Weighted F1: {metrics['weighted_f1']:.4f}")
    print(f"Artifacts written to: {args.model_dir}")


if __name__ == "__main__":
    main()
