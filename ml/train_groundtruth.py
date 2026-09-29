from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedGroupKFold

DATASET = Path("data/processed/dataset_groundtruth.csv")
CLEAN_DATASET = Path("data/processed/dataset_groundtruth_clean.csv")
MODEL_PATH = Path("models/ransomware_classifier_groundtruth.joblib")
METRICS_PATH = Path("models/ransomware_groundtruth_cv_metrics.json")

META = {
    "session_id",
    "window_id",
    "label",
    "attack_overlap_s",
    "groundtruth",
    "source_file",
}

df = pd.read_csv(DATASET)

feature_cols = [c for c in df.columns if c not in META]

if len(feature_cols) != 48:
    raise SystemExit(
        f"Expected 48 ML features, found {len(feature_cols)}"
    )

if not all(pd.api.types.is_numeric_dtype(df[c]) for c in feature_cols):
    bad = [c for c in feature_cols if not pd.api.types.is_numeric_dtype(df[c])]
    raise SystemExit(f"Non-numeric ML features found: {bad}")

# Remove every feature-vector group that appears in more than one session.
duplicate_keys = []
for _, group in df.groupby(feature_cols, dropna=False):
    if group["session_id"].nunique() > 1:
        duplicate_keys.append(group.index)

duplicate_indices = (
    pd.Index([])
    if not duplicate_keys
    else pd.Index([i for idx in duplicate_keys for i in idx])
)

clean = df.drop(index=duplicate_indices).copy()

clean.to_csv(CLEAN_DATASET, index=False)

X = clean[feature_cols]
y = clean["label"].astype(int)
groups = clean["session_id"]

print("\n" + "=" * 70)
print("CLEAN GROUND-TRUTH MODEL")
print("=" * 70)

print(f"\nOriginal rows: {len(df)}")
print(f"Removed rows: {len(df) - len(clean)}")
print(f"Clean rows: {len(clean)}")
print(f"Features: {len(feature_cols)}")
print(f"Sessions: {groups.nunique()}")

print("\nClass distribution:")
print(y.value_counts().sort_index())

cv = StratifiedGroupKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)

oof_true = []
oof_pred = []
oof_prob = []

fold_results = []

for fold, (train_idx, test_idx) in enumerate(
    cv.split(X, y, groups=groups),
    start=1,
):
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    train_groups = groups.iloc[train_idx].unique().tolist()
    test_groups = groups.iloc[test_idx].unique().tolist()

    model = RandomForestClassifier(
        n_estimators=500,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
        min_samples_leaf=1,
    )

    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    oof_true.extend(y_test.tolist())
    oof_pred.extend(pred.tolist())
    oof_prob.extend(prob.tolist())

    fold_acc = accuracy_score(y_test, pred)
    fold_bal = balanced_accuracy_score(y_test, pred)
    fold_f1 = f1_score(y_test, pred, zero_division=0)

    fold_results.append({
        "fold": fold,
        "train_rows": len(train_idx),
        "test_rows": len(test_idx),
        "train_sessions": train_groups,
        "test_sessions": test_groups,
        "accuracy": fold_acc,
        "balanced_accuracy": fold_bal,
        "f1": fold_f1,
    })

    print(f"\n--- Fold {fold} ---")
    print(f"Train rows: {len(train_idx)}")
    print(f"Test rows:  {len(test_idx)}")
    print(f"Test sessions: {test_groups}")
    print(f"Accuracy: {fold_acc:.4f}")
    print(f"Balanced Accuracy: {fold_bal:.4f}")
    print(f"F1: {fold_f1:.4f}")

oof_true = pd.Series(oof_true)
oof_pred = pd.Series(oof_pred)

accuracy = accuracy_score(oof_true, oof_pred)
balanced = balanced_accuracy_score(oof_true, oof_pred)
precision = precision_score(oof_true, oof_pred, zero_division=0)
recall = recall_score(oof_true, oof_pred, zero_division=0)
f1 = f1_score(oof_true, oof_pred, zero_division=0)
cm = confusion_matrix(oof_true, oof_pred)

print("\n" + "=" * 70)
print("5-FOLD SESSION-AWARE OOF RESULTS")
print("=" * 70)

print(f"\nAccuracy:            {accuracy:.4f}")
print(f"Balanced Accuracy:  {balanced:.4f}")
print(f"Precision:           {precision:.4f}")
print(f"Recall:              {recall:.4f}")
print(f"F1 Score:            {f1:.4f}")

print("\nConfusion Matrix:")
print(cm)

print("\nInterpretation:")
print("Rows = actual class")
print("Columns = predicted class")
print("[[TN, FP], [FN, TP]]")

# Final model trained on all clean data.
final_model = RandomForestClassifier(
    n_estimators=500,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
    min_samples_leaf=1,
)

final_model.fit(X, y)

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

bundle = {
    "model": final_model,
    "features": feature_cols,
    "training_rows": len(clean),
    "training_sessions": sorted(groups.unique().tolist()),
    "dataset": str(CLEAN_DATASET),
    "evaluation": {
        "accuracy": accuracy,
        "balanced_accuracy": balanced,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": cm.tolist(),
    },
}

joblib.dump(bundle, MODEL_PATH)

METRICS_PATH.write_text(
    json.dumps(
        {
            "dataset": str(CLEAN_DATASET),
            "rows": len(clean),
            "features": len(feature_cols),
            "sessions": groups.nunique(),
            "cross_session_duplicate_rows_removed": int(len(df) - len(clean)),
            "accuracy": accuracy,
            "balanced_accuracy": balanced,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "confusion_matrix": cm.tolist(),
            "folds": fold_results,
        },
        indent=2,
    )
)

print("\n" + "=" * 70)
print("SAVED")
print("=" * 70)
print(f"Clean dataset: {CLEAN_DATASET}")
print(f"Final model:   {MODEL_PATH}")
print(f"Metrics:       {METRICS_PATH}")
print("=" * 70)
