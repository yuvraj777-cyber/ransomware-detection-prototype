import joblib
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
def top_contributing_factors(feature_row: dict, top_n=4):
    importances = model.feature_importances_
    ranked = sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True)
    factors = []
    for name, imp in ranked[:top_n]:
        factors.append(
            f"{name.replace('_', ' ')}: {feature_row.get(name)}"
        )
    return factors
