from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tarang.detector import TarangDetector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/network_events.csv"))
    parser.add_argument("--model-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    train_df, test_df = train_test_split(
        df,
        test_size=0.20,
        random_state=42,
        stratify=df["label"],
    )

    detector, _ = TarangDetector.train(train_df)
    predictions = detector.predict(test_df)
    detector.save(args.model_dir)

    accuracy = accuracy_score(test_df["label"], predictions["predicted_label"])
    print(f"Held-out accuracy: {accuracy:.3f}")
    print(classification_report(test_df["label"], predictions["predicted_label"], zero_division=0))
    print(f"Models saved to: {args.model_dir}")


if __name__ == "__main__":
    main()
