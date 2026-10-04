# Tarang — NSL-KDD Benchmark Results

**Benchmark run:** GitHub Actions run 37231694998  
**Dataset:** NSL-KDD  
**Train rows:** 125,973  
**Untouched test rows:** 22,544 (9,711 benign / 12,833 attack)  
**Feature representation:** 121 features after numeric preprocessing and categorical one-hot encoding  
**Isolation Forest:** trained on benign training rows only  
**Hybrid baseline:** pre-specified 50% Isolation Forest anomaly score + 50% Random Forest attack probability  
**Threshold selection:** validation split from KDDTrain+ only  

> The old synthetic 100% accuracy result is intentionally not used as the headline metric. Synthetic data remains a pipeline smoke test.

## Final untouched-test results

| Model | Accuracy | Precision | Recall | F1 | Balanced Accuracy | ROC-AUC | Average Precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isolation Forest | 78.38% | 93.71% | 66.48% | 77.78% | 80.29% | 93.96% | 95.33% |
| Random Forest | 73.10% | 96.83% | 54.53% | 69.77% | 76.09% | 96.67% | 97.08% |
| **Hybrid 50/50** | **76.41%** | **96.88%** | **60.50%** | **74.49%** | **78.96%** | **95.30%** | **96.18%** |

## Hybrid confusion matrix

Rows = actual class, columns = predicted class. Class order: `[benign, attack]`.

```text
                 Predicted
                 Benign   Attack
Actual Benign      9461      250
       Attack      5069     7764
```

Equivalent values:

- True negatives: 9,461
- False positives: 250
- False negatives: 5,069
- True positives: 7,764

## What the result means

The hybrid model is materially better than the supervised Random Forest alone on the untouched test set for recall and F1: +5.97 percentage points recall and +4.72 percentage points F1. Precision remains 96.88%, with 250 false positives among 9,711 benign test rows.

The anomaly detector also shows useful independent behavior: Isolation Forest reaches 66.48% attack recall and 77.78% F1 without using attack labels for its model fitting.

## Fusion-weight sensitivity experiment

A separate validation-tuned fusion experiment selected a 10% Isolation Forest / 90% Random Forest weight based on validation F1. When evaluated on the same untouched test set, it produced 73.19% accuracy, 54.69% recall and 69.90% F1.

This experiment is retained as an engineering observation, not silently replaced with a better-looking configuration. It shows why fusion weight selection needs stronger cross-validation or temporal/domain validation rather than relying on one validation split.

## Interview-ready explanation

> I first used synthetic data to validate the pipeline and got 100%, but I did not treat that as evidence because the generated distribution was too close to the feature logic. I moved the evaluation to NSL-KDD and kept the test set completely untouched. Isolation Forest is trained only on benign training traffic, Random Forest uses the labels, and the hybrid combines their normalized signals. On 22,544 test flows, the pre-specified 50/50 hybrid reached 76.41% accuracy, 96.88% precision, 60.50% recall and 74.49% F1. Its confusion matrix had 250 false positives and 5,069 false negatives. The main engineering takeaway is that the hybrid improved recall and F1 over Random Forest alone, but the benchmark also shows that cross-domain validation is still needed before making any production claim.

## Limitations

NSL-KDD is an established benchmark rather than a modern enterprise telemetry set. The result is evidence of reproducible benchmark behavior, not a guarantee of deployment performance. The next validation target is CICIDS2017 or a representative private flow sample with a temporally separated test period.

## Reproducibility

Run:

```bash
python scripts/download_nsl_kdd.py
python scripts/benchmark_nsl_kdd.py
```

Use `python scripts/benchmark_nsl_kdd.py --tune-weight` only for the fusion-weight sensitivity experiment.

Source run: https://github.com/nikhil-247/Tarang/actions/runs/37231694998