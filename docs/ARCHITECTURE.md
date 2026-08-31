# Architecture

Tarang separates ingestion, feature engineering, model inference, and delivery so each part can be tested independently.

```text
Network/flow records
        |
        v
+-------------------+
| Input validation  |
+-------------------+
        |
        v
+-------------------+
| Feature engineering|
| ratios + entropy   |
| protocol indicators|
+-------------------+
        |
        +-----------------------+
        |                       |
        v                       v
+-------------------+   +-------------------+
| Isolation Forest  |   | Random Forest     |
| anomaly detection |   | threat class      |
+-------------------+   +-------------------+
        |                       |
        +-----------+-----------+
                    v
          Risk aggregation
                    |
          +---------+---------+
          |                   |
          v                   v
       CLI/CSV            FastAPI /v1/predict
```

## Components

- `src/tarang/features.py`: validates the event schema and creates deterministic numerical features.
- `src/tarang/detector.py`: trains, persists, loads, and executes the hybrid detector.
- `scripts/generate_dataset.py`: creates safe synthetic data for reproducible demonstrations.
- `scripts/train.py`: performs a stratified train/test split and writes held-out metrics and predictions.
- `scripts/infer.py`: batch scores a CSV using persisted artifacts.
- `src/tarang/api.py`: exposes health and single-event prediction endpoints.

## Production hardening roadmap

For real deployment, connect the feature layer to packet/flow parsers such as NetFlow/IPFIX or a controlled packet sensor, introduce a feature schema registry, model versioning, drift monitoring, authentication, rate limiting, structured observability, and a review queue for high-risk alerts.
