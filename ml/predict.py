import argparse
import json
import joblib
from pathlib import Path

import pandas as pd

try:
    from .features import read_jsonl, window_features
except ImportError:
    from features import read_jsonl, window_features


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "ransomware_classifier.joblib"
)


def predict_risk(feature_row: dict) -> float:
    """
    Predict ransomware probability for one already-extracted
    feature row using the current 48-feature classifier.
    """
    bundle = joblib.load(MODEL_PATH)

    model = bundle["model"]
    feature_cols = bundle["features"]

    X = pd.DataFrame([feature_row])

    missing = [c for c in feature_cols if c not in X.columns]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    X = X[feature_cols]

    return float(model.predict_proba(X)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument(
        "--model",
        default=str(MODEL_PATH),
    )
    ap.add_argument("--window", type=int, default=10)
    args = ap.parse_args()

    bundle = joblib.load(args.model)
    model = bundle["model"]
    feature_cols = bundle["features"]
    threshold = float(bundle.get("threshold", 0.5))

    feats = window_features(
        read_jsonl(Path(args.events)),
        args.window,
    )

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
