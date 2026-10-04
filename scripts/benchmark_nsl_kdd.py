from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tarang.benchmark import benchmark_predictions, evaluate, fit_hybrid, load_nsl_kdd, save_bundle

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Tarang on NSL-KDD without test leakage.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/nsl-kdd"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/nsl-kdd"))
    parser.add_argument("--tune-weight", action="store_true", help="Select the hybrid fusion weight using validation F1; default benchmark keeps a pre-specified 50/50 blend.")
    args = parser.parse_args()

    train_path = args.data_dir / "KDDTrain+.txt"
    test_path = args.data_dir / "KDDTest+.txt"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("Run scripts/download_nsl_kdd.py first.")

    train_df = load_nsl_kdd(train_path)
    test_df = load_nsl_kdd(test_path)

    model, validation = fit_hybrid(train_df, tune_weight=args.tune_weight)
    final_metrics = evaluate(model, test_df)
    final_metrics["validation_metrics"] = validation
    final_metrics["rows"]["train"] = len(train_df)

    save_bundle(model, final_metrics, len(train_df), args.output_dir)
    predictions = benchmark_predictions(model, test_df)
    predictions.to_csv(args.output_dir / "test_predictions.csv", index=False)
    (args.output_dir / "benchmark_protocol.json").write_text(
        json.dumps(final_metrics["protocol"], indent=2),
        encoding="utf-8",
    )

    print("\nNSL-KDD benchmark — untouched test set")
    for name, metric in final_metrics["metrics"].items():
        print(
            f"{name:17s} "
            f"accuracy={metric['accuracy']:.4f} "
            f"precision={metric['precision']:.4f} "
            f"recall={metric['recall']:.4f} "
            f"f1={metric['f1']:.4f} "
            f"balanced_acc={metric['balanced_accuracy']:.4f}"
        )
        print(f"  confusion_matrix={metric['confusion_matrix']}")
    print(f"\nArtifacts: {args.output_dir}")

if __name__ == "__main__":
    main()
