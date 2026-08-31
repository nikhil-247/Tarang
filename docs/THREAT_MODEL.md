# Threat Model

Tarang is a defensive analytics prototype. It is intended to help analysts prioritize suspicious network events, not to automatically block traffic.

## In scope

- Network-flow metadata
- Protocol indicators
- Abnormal traffic ratios and rates
- DNS-string entropy
- Labeled threat classes for supervised learning

## Example threat classes

- `suspicious`: unusual traffic that needs review
- `exfiltration`: unusually high outbound volume or transfer-like behavior
- `scan`: repeated failed/irregular connection behavior
- `benign`: normal demonstration traffic

## Safety boundaries

The repository uses synthetic records. It does not capture credentials, exploit live systems, inject packets, or perform active intrusion. Any production deployment should isolate collection infrastructure and apply organization-approved security controls.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| False positives | Use held-out evaluation and analyst review thresholds |
| False negatives | Monitor recall by class and retrain with representative data |
| Dataset shift | Track feature distributions and model drift |
| Model overconfidence | Calibrate probabilities and expose confidence to downstream systems |
| Malicious input | Validate numeric ranges and sanitize text fields |
| Unauthorized scoring | Put the API behind authentication, TLS, and network controls |

## Important limitation

High accuracy on synthetic data should not be interpreted as proof of real-world detection performance. Real-world validation requires representative traffic, temporal splits, adversarial testing, and careful precision/recall analysis.
