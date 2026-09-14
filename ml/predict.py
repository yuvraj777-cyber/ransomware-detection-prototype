import argparse, json, joblib
from pathlib import Path
import pandas as pd
from features import read_jsonl, window_features

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--model", default="models/ransomware_classifier.joblib")
    ap.add_argument("--window", type=int, default=10)
    args = ap.parse_args()

    bundle = joblib.load(args.model)
    model = bundle["model"]
    feature_cols = bundle["features"]
    threshold = float(bundle.get("threshold", 0.5))

    feats = window_features(read_jsonl(Path(args.events)), args.window)
    if feats.empty:
        raise ValueError("No events found.")
    X = feats[feature_cols]
    probs = model.predict_proba(X)[:, 1]
    out = feats[["window_id"]].copy()
    out["ransomware_probability"] = probs
    out["prediction"] = (probs >= threshold).astype(int)

    print(out.to_json(orient="records", indent=2))

if __name__ == "__main__":
    main()
