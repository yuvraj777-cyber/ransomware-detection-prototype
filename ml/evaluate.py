import argparse, json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, average_precision_score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/processed/dataset.csv")
    ap.add_argument("--model", default="models/ransomware_classifier.joblib")
    args = ap.parse_args()

    df = pd.read_csv(args.dataset)
    bundle = joblib.load(args.model)
    model = bundle["model"]
    cols = bundle["features"]

    X = df[cols]
    y = df["label"].astype(int)
    p = model.predict_proba(X)[:, 1]
    pred = (p >= bundle.get("threshold", 0.5)).astype(int)

    result = {
        "warning": "These metrics are on the full dataset and are NOT a valid holdout estimate.",
        "classification_report": classification_report(y, pred, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }
    if y.nunique() == 2:
        result["roc_auc"] = roc_auc_score(y, p)
        result["pr_auc"] = average_precision_score(y, p)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
