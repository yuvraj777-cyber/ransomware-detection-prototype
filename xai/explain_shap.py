import shap
import joblib
import pandas as pd

model = joblib.load("../ml/model.pkl")

FEATURES = [
    "file_modified_rate",
    "file_created_rate",
    "file_renamed_rate",
    "file_deleted_rate",
    "new_process_rate",
    "avg_cpu",
    "avg_mem"
]

explainer = shap.TreeExplainer(model)


def explain_prediction(feature_row: dict, top_n=4):

    X = pd.DataFrame([feature_row])[FEATURES]

    shap_values = explainer.shap_values(X)

    # for binary RandomForest,
    # shap_values[1] = contributions toward ransomware-like class

    contributions = list(
        zip(FEATURES, shap_values[1][0])
    )

    contributions.sort(
        key=lambda x: abs(x[1]),
        reverse=True
    )

    return [
        f"{name.replace('_', ' ')} (impact: {round(val, 3)})"
        for name, val in contributions[:top_n]
    ]