# Tarang — Intelligent Network Threat Detection Platform

Tarang is a Python-based defensive security prototype for analyzing network communication records, extracting protocol-aware features, and flagging anomalous or potentially malicious traffic.

> **Note:** This repository is a research/learning prototype. The included dataset is synthetic, and the reported evaluation metrics are generated from that dataset. It is not a production intrusion-detection system.

## What it does

- Generates reproducible synthetic network-flow records.
- Extracts protocol-aware numerical features from HTTP, DNS, TCP, UDP and TLS-like traffic.
- Uses **Isolation Forest** for unsupervised anomaly detection.
- Uses a supervised **Random Forest** classifier when labeled examples are available.
- Produces per-event risk scores and reasons for flagged traffic.
- Exposes a small command-line workflow for training and inference.

## Architecture

```text
Raw network events
       |
       v
Feature extraction
       |
       +------> Isolation Forest ----> anomaly score
       |
       +------> Random Forest --------> threat class
       |
       v
Risk aggregation + explainable flags
       |
       v
CSV / JSON security report
```

## Project structure

```text
Tarang/
├── data/
│   └── network_events.csv
├── src/
│   └── tarang/
│       ├── __init__.py
│       ├── features.py
│       └── detector.py
├── scripts/
│   ├── generate_dataset.py
│   └── train.py
├── tests/
│   └── test_features.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Generate data

```bash
python scripts/generate_dataset.py --rows 1200 --output data/network_events.csv
```

## Train the detector

```bash
python scripts/train.py --input data/network_events.csv --model-dir artifacts
```

The training script reports precision, recall and F1 for the supervised classifier and saves the trained models locally under `artifacts/`.

## Example event fields

`timestamp, src_bytes, dst_bytes, duration_ms, packet_count, protocol, dst_port, dns_entropy, tls, failed_connections, label`

## Design choices

**Isolation Forest** is used to surface unusual traffic patterns without requiring labels for every event. **Random Forest** provides a supervised baseline for known threat classes. Combining both gives a practical prototype for environments where labeled security data is limited but a small labeled sample is available.

## Scope and limitations

The project deliberately uses synthetic data to keep the repository reproducible and safe. Real network telemetry requires additional packet parsing, feature engineering, class-imbalance handling, drift monitoring, model calibration, and rigorous validation against representative traffic. The current implementation should therefore be treated as a demonstrator rather than a security product.

## License

MIT
