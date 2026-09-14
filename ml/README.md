# Behavioral Ransomware Detection — ML Pipeline

This repository turns the event stream produced by the monitoring agent into time-window features and trains machine-learning detectors.

## What is already present

The supplied `monitor.py` records:
- filesystem create/modify/delete/rename events
- newly created processes
- CPU, memory, disk read/write deltas, process count, and platform
- JSONL output in `events/events.jsonl`

## Important data limitation

The supplied telemetry contains behavioral events but no ground-truth `benign` vs `ransomware` labels. Therefore:
1. the supervised classifier is ready but cannot honestly be trained/evaluated until ransomware-labeled runs exist;
2. an Isolation Forest anomaly detector can be trained using benign telemetry immediately.

## Repository layout

```text
ransomware_ml/
├── data/
│   ├── raw/
│   │   ├── benign/
│   │   └── ransomware/
│   └── processed/
├── models/
├── reports/
├── src/
│   ├── features.py
│   ├── build_dataset.py
│   ├── train.py
│   ├── train_anomaly.py
│   ├── evaluate.py
│   └── predict.py
├── requirements.txt
└── README.md
```

## 1. Setup in VS Code

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 2. Collect labeled runs

Put complete JSONL runs into:

```text
data/raw/benign/
data/raw/ransomware/
```

Example:

```text
data/raw/benign/normal_browsing_01.jsonl
data/raw/benign/file_copy_01.jsonl
data/raw/ransomware/lab_run_01.jsonl
data/raw/ransomware/lab_run_02.jsonl
```

Use only an isolated, authorized malware-analysis lab for ransomware samples.

A label belongs to the RUN, not an individual event. This is important because adjacent windows from the same execution should not be split randomly across train and test.

## 3. Build the feature dataset

```bash
python src/build_dataset.py --input data/raw --output data/processed/dataset.csv --window 10
```

The feature generator creates 10-second behavioral windows and includes event rates, filesystem activity, process bursts, suspicious-process-name counts, CPU/memory summaries, disk I/O rates, and process-count statistics.

## 4. Train the supervised model

```bash
python src/train.py
```

The training script compares:
- Logistic Regression
- Random Forest
- Histogram Gradient Boosting

The split is grouped by session/run, not by individual windows, reducing temporal leakage.

The best model by validation F1 is saved as:

```text
models/ransomware_classifier.joblib
```

Metrics are saved to:

```text
reports/metrics.json
```

For ransomware detection, inspect precision, recall, F1, ROC-AUC, PR-AUC, and the confusion matrix. Accuracy alone can be misleading on imbalanced data.

## 5. Train an anomaly baseline

You can run this immediately on benign telemetry:

```bash
python src/train_anomaly.py
```

It creates:

```text
models/anomaly_detector.joblib
```

This detector learns normal behavioral patterns without ransomware labels. Treat it as a baseline, not proof of ransomware detection.

## 6. Predict on a new labeled/unlabeled run

```bash
python src/predict.py --events path/to/events.jsonl
```

Output is a per-window ransomware probability and binary decision.

## Recommended development sequence

First collect several genuinely different benign runs (idle system, browsing, file copy, application launch, archive extraction, compilation, etc.). Then collect ransomware-lab runs with the same monitor configuration. Keep whole runs together during evaluation.

Do not report the accuracy of a model trained only on the supplied PDF as "ransomware detection accuracy"; the supplied data is not ransomware-labeled.

## GitHub

Suggested `.gitignore` entries should keep `.venv`, Python caches, local logs/databases, IDE files, and event JSONL out of the repository. Large raw datasets and trained model binaries should also normally be kept out of Git unless you intentionally use Git LFS.
