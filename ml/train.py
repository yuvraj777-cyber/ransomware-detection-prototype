from pathlib import Path
import argparse
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, classification_report,
    confusion_matrix, f1_score, average_precision_score, roc_auc_score
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

RANDOM_STATE = 42
TARGET = "label"
DROP = {"label", "session_id", "source_file", "window_id"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/processed/dataset.csv")
    ap.add_argument("--model-dir", default="models")
    ap.add_argument("--report-dir", default="reports")
    args = ap.parse_args()

    df = pd.read_csv(args.dataset)
    if TARGET not in df:
        raise ValueError("dataset must contain a 'label' column")
    if df[TARGET].nunique() < 2:
        raise ValueError(
            "Supervised training requires BOTH classes. Add ransomware-labeled runs "
            "under data/raw/ransomware/ and rebuild the dataset."
        )

    feature_cols = [c for c in df.columns if c not in DROP]
    X = df[feature_cols].replace([np.inf, -np.inf], np.nan)
    y = df[TARGET].astype(int)
    groups = df["session_id"].astype(str)

    # Split by session, not by individual windows, to reduce temporal leakage.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    candidates = {
        "logistic_regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced",
                                      random_state=RANDOM_STATE))
        ]),
        "random_forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=400, min_samples_leaf=2, class_weight="balanced",
                random_state=RANDOM_STATE, n_jobs=-1
            ))
        ]),
        "hist_gradient_boosting": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", HistGradientBoostingClassifier(
                max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                random_state=RANDOM_STATE
            ))
        ]),
    }

    results = {}
    best_name, best_score, best_model = None, -1.0, None

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

        score = f1_score(y_test, pred, zero_division=0)
        row = {
            "accuracy": accuracy_score(y_test, pred),
            "balanced_accuracy": balanced_accuracy_score(y_test, pred),
            "f1": score,
            "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
            "classification_report": classification_report(
                y_test, pred, output_dict=True, zero_division=0
            ),
        }
        if prob is not None and len(np.unique(y_test)) == 2:
            row["roc_auc"] = roc_auc_score(y_test, prob)
            row["pr_auc"] = average_precision_score(y_test, prob)
        results[name] = row

        if score > best_score:
            best_name, best_score, best_model = name, score, model

    model_dir = Path(args.model_dir)
    report_dir = Path(args.report_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {"model": best_model, "features": feature_cols, "threshold": 0.50},
        model_dir / "ransomware_classifier.joblib"
    )

    report = {
        "best_model": best_name,
        "best_f1": best_score,
        "n_rows": len(df),
        "n_features": len(feature_cols),
        "train_rows": len(train_idx),
        "test_rows": len(test_idx),
        "train_sessions": groups.iloc[train_idx].nunique(),
        "test_sessions": groups.iloc[test_idx].nunique(),
        "results": results,
    }
    (report_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(
        {"best_model": best_name, "best_f1": round(best_score, 4), "results": results},
        indent=2
    ))

if __name__ == "__main__":
    main()
