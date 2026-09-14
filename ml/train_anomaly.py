from pathlib import Path
import argparse, json, joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/processed/dataset.csv")
    ap.add_argument("--model", default="models/anomaly_detector.joblib")
    args = ap.parse_args()

    df = pd.read_csv(args.dataset)
    benign = df[df["label"] == 0].copy()
    if benign.empty:
        raise ValueError("Need at least one benign run.")

    drop = {"label", "session_id", "source_file", "window_id"}
    features = [c for c in df.columns if c not in drop]
    X = benign[features].replace([np.inf, -np.inf], np.nan)

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("iso", IsolationForest(
            n_estimators=400, contamination="auto", random_state=42, n_jobs=-1
        )),
    ])
    model.fit(X)
    Path(args.model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features}, args.model)

    scores = model.decision_function(X)
    print(json.dumps({
        "trained_on_benign_rows": len(benign),
        "feature_count": len(features),
        "score_mean": float(np.mean(scores)),
        "score_std": float(np.std(scores)),
        "model": args.model
    }, indent=2))

if __name__ == "__main__":
    main()
