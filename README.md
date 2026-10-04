# Tarang — Network Threat Detection Platform

Tarang is a defensive network-security analytics project that turns network-flow metadata into explainable threat signals. It combines a supervised Random Forest classifier with an unsupervised Isolation Forest detector and exposes the pipeline through CLI and FastAPI interfaces.

> **Evaluation policy:** the original synthetic dataset is retained as a development smoke test only. The headline model evaluation is now defined against the public NSL-KDD benchmark with an untouched test set.

## What changed

- Hybrid Isolation Forest + Random Forest architecture retained.
- Isolation Forest is trained on benign training rows for the benchmark workflow.
- NSL-KDD KDDTrain+ / KDDTest+ download and checksum verification.
- Native benchmark preprocessing: numeric imputation + standardization and categorical one-hot encoding.
- Thresholds are tuned only on a validation split from KDDTrain+.
- KDDTest+ is not used for training or threshold selection.
- Metrics include accuracy, precision, recall, F1, balanced accuracy, ROC-AUC, average precision and a 2x2 confusion matrix.
- Per-record benchmark predictions and protocol metadata are exported.
- GitHub Actions runs the benchmark on pushes to main and stores the evidence bundle as an artifact.

## Architecture

```text
Raw network records
       |
       v
Schema validation
       |
       +-----------------------------+
       |                             |
       v                             v
Native benchmark              Existing flow pipeline
preprocessing                 (development path)
       |
       v
  +----+-------------------+
  |                        |
  v                        v
Isolation Forest       Random Forest
benign-only training   labeled training
  |                        |
  +-----------+------------+
              v
       hybrid threat score
              |
              v
 metrics + predictions + API
```

## Reproducible NSL-KDD benchmark

The current benchmark result is from an untouched **22,544-row NSL-KDD test set**. The pre-specified 50/50 hybrid achieved **76.41% accuracy, 96.88% precision, 60.50% recall and 74.49% F1**, with **250 false positives** and **5,069 false negatives**. Full metrics, confusion matrix and the sensitivity experiment are in [docs/NSL_KDD_RESULTS.md](docs/NSL_KDD_RESULTS.md).

| Model | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Isolation Forest | 78.38% | 93.71% | 66.48% | 77.78% |
| Random Forest | 73.10% | 96.83% | 54.53% | 69.77% |
| **Hybrid 50/50** | **76.41%** | **96.88%** | **60.50%** | **74.49%** |

This benchmark is the project’s current evidence baseline; it is not a claim of production detection performance.

### Run locally

`python scripts/download_nsl_kdd.py`
`python scripts/benchmark_nsl_kdd.py`

NSL-KDD is used because it has a fixed train/test benchmark structure and can be downloaded and verified automatically. The repository does not hard-code benchmark numbers; the workflow generates them.

### Local run

```bash
python scripts/download_nsl_kdd.py
python scripts/benchmark_nsl_kdd.py
```

Outputs:

```text
artifacts/nsl-kdd/
├── benchmark_protocol.json
├── features.csv
├── hybrid_nsl_kdd.joblib
├── metrics.json
└── test_predictions.csv
```

### Benchmark protocol

1. Download and checksum the fixed training and test files.
2. Split KDDTrain+ into train/validation.
3. Fit preprocessing only on the training partition.
4. Train Random Forest on labeled training rows.
5. Train Isolation Forest on benign training rows only.
6. Tune each model threshold and the hybrid threshold on validation.
7. Evaluate once on untouched KDDTest+.
8. Export metrics and row-level predictions.

### Honest interview framing

Do not lead with the old 100% synthetic accuracy. The defensible statement is:

> My first version used synthetic traffic to validate the feature pipeline and reached 100%, but I treated that as a development smoke test rather than model evidence. I moved the benchmark to NSL-KDD, kept Isolation Forest truly unsupervised by training it only on benign training data, selected thresholds on validation, and reported precision, recall, F1 and the confusion matrix on the untouched test set.

## Existing development path

The original compact flow pipeline in `src/tarang/features.py` is still useful for live/demo events. The new benchmark adapter intentionally uses NSL-KDD's native features rather than forcing a lossy nine-field mapping. This preserves a comparable hybrid architecture without inventing fields the benchmark does not contain.

## API

```bash
uvicorn tarang.api:app --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /health`
- `POST /v1/predict`

## Testing

```bash
pytest -q
```

CI validates the Python test suite and the separate NSL-KDD benchmark workflow.

## Production-readiness roadmap

- calibrated probabilities
- temporal and cross-domain validation
- CICIDS2017 second-benchmark replication
- model/data version registry
- feature drift monitoring
- alert deduplication and analyst feedback
- authenticated ingestion and service-to-service TLS
- structured observability

## Limitations

NSL-KDD is an established benchmark, not a complete representation of modern enterprise traffic. Benchmark results should be treated as evidence of reproducibility and generalization on that benchmark, not as a guarantee of production detection performance.

## References

- UNB Canadian Institute for Cybersecurity: https://www.unb.ca/cic/datasets/nsl.html
- Zenodo pinned NSL-KDD copy used by the downloader: https://zenodo.org/records/17424143
- Scikit-learn IsolationForest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- Scikit-learn RandomForestClassifier: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
