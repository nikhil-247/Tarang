# Tarang — Intelligent Network Threat Detection Platform

Tarang is a defensive network-security analytics prototype that converts network-flow metadata into explainable risk signals. It combines protocol-aware feature engineering, unsupervised anomaly detection, and supervised threat classification, with both CLI and REST API entry points.

> **Research/demo scope:** the bundled records are synthetic. The project is designed to demonstrate an end-to-end ML engineering workflow and must not be treated as a production intrusion-prevention system without additional validation and security controls.

## Highlights

- Protocol-aware features for TCP, UDP, DNS, HTTP, HTTPS, and TLS-like events
- Shannon entropy and traffic-rate features for suspicious DNS/network behavior
- Hybrid **Isolation Forest + Random Forest** detection pipeline
- Held-out evaluation with accuracy, macro F1, weighted F1, and per-class report
- Batch CSV inference with risk levels and confidence scores
- FastAPI service with `/health` and `/v1/predict`
- Pydantic request validation and deterministic model feature ordering
- Automated tests and GitHub Actions CI
- Docker-ready runtime for the scoring API

## Architecture

```text
                    +----------------------+
                    | Network-flow events  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Input validation      |
                    | schema + ranges       |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Feature engineering   |
                    | rates + ratios + DNS  |
                    | entropy + protocols   |
                    +----------+-----------+
                               |
                     +---------+---------+
                     |                   |
                     v                   v
              +-------------+     +-------------+
              | Isolation   |     | Random      |
              | Forest      |     | Forest      |
              | anomaly     |     | classification|
              +------+------+     +------+------+
                     |                   |
                     +---------+---------+
                               v
                    +----------------------+
                    | Risk + confidence    |
                    | analyst-facing score |
                    +----------+-----------+
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
             CSV reports              FastAPI service
```

## Repository layout

```text
Tarang/
├── .github/workflows/ci.yml
├── data/network_events.csv
├── docs/
│   ├── ARCHITECTURE.md
│   └── THREAT_MODEL.md
├── scripts/
│   ├── generate_dataset.py
│   ├── infer.py
│   └── train.py
├── src/tarang/
│   ├── __init__.py
│   ├── api.py
│   ├── detector.py
│   └── features.py
├── tests/
│   ├── test_api.py
│   └── test_features.py
├── Dockerfile
├── .gitignore
└── requirements.txt
```

## Quick start

### 1. Install

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate a reproducible dataset

The committed CSV is a small example. For training, generate a larger synthetic dataset:

```bash
python scripts/generate_dataset.py --rows 2500 --output data/network_events.csv
```

### 3. Train and evaluate

```bash
python scripts/train.py --input data/network_events.csv --model-dir artifacts
```

The command creates local model artifacts plus:

- `artifacts/metrics.json`
- `artifacts/predictions.csv`
- `artifacts/isolation_forest.joblib`
- `artifacts/random_forest.joblib`

The reported metrics are **held-out results on the generated synthetic dataset**.

### 4. Batch inference

```bash
python scripts/infer.py \
  --input data/network_events.csv \
  --model-dir artifacts \
  --output reports/predictions.csv
```

### 5. Run the REST API

```bash
uvicorn tarang.api:app --host 0.0.0.0 --port 8000
```

Check health:

```bash
curl http://localhost:8000/health
```

Score one event:

```bash
curl -X POST http://localhost:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "src_bytes": 7600,
    "dst_bytes": 1200,
    "duration_ms": 210,
    "packet_count": 8,
    "protocol": "TCP",
    "dst_port": 54321,
    "dns_query": "x9q7a.test",
    "tls": 0,
    "failed_connections": 7
  }'
```

## Testing

```bash
pytest -q
```

The CI workflow runs the test suite automatically on pushes and pull requests.

## Model and feature design

Tarang currently combines two complementary approaches:

1. **Isolation Forest** surfaces observations that differ from learned traffic patterns without requiring labels for every event.
2. **Random Forest** classifies known demonstration classes when labeled training records are available.

Engineered features include byte ratios, bytes per packet, packets per second, DNS entropy, DNS length, port indicators, failed-connection rate, and protocol one-hot indicators.

## Operational considerations

For a real deployment, the next engineering steps would include authenticated ingestion, TLS, network controls, structured logging, model/version registry, probability calibration, drift monitoring, representative temporal validation, packet/flow parsers, alert deduplication, analyst feedback loops, and a controlled review workflow for high-risk events.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for safety boundaries and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the component design.

## Ethical and defensive use

Use Tarang only on network telemetry you are authorized to analyze. The repository is intentionally limited to synthetic data and passive analytics; it does not contain exploit code or an active traffic-blocking mechanism.

## License

MIT
