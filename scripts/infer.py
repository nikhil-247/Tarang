from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tarang.detector import TarangDetector


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tarang inference on CSV network events")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, default=Path("reports/predictions.csv"))
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)

    detector = TarangDetector.load(args.model_dir)
    events = pd.read_csv(args.input)
    predictions = detector.predict(events)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output, index=False)

    summary = {
        "events": len(predictions),
        "high_risk": int((predictions["risk_level"] == "high").sum()),
        "medium_risk": int((predictions["risk_level"] == "medium").sum()),
        "low_risk": int((predictions["risk_level"] == "low").sum()),
    }
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
