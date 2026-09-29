from datetime import datetime
from pathlib import Path
import sys

from risk_score import score_risk

# Add ml folder to Python path
ml_path = Path(__file__).resolve().parent.parent / "ml"
sys.path.append(str(ml_path))

from predict import predict_risk


def build_alert(feature_row):
    # Get probability from the current 48-feature ML model
    probability = predict_risk(feature_row)

    # Convert probability into the existing risk level
    risk = score_risk(probability)

    indicators = []

    fs_renamed = int(feature_row.get("fs_renamed", 0))
    suspicious_ext = int(
        feature_row.get("suspicious_extension_events", 0)
    )
    max_rename_1s = int(
        feature_row.get("max_rename_events_1s", 0)
    )
    max_fs_1s = int(
        feature_row.get("max_fs_events_1s", 0)
    )
    filesystem_burst = int(
        feature_row.get("filesystem_burst", 0)
    )
    fs_modified = int(
        feature_row.get("fs_modified", 0)
    )

    if fs_renamed > 0:
        indicators.append(
            f"{fs_renamed} file rename events detected"
        )

    if suspicious_ext > 0:
        indicators.append(
            f"{suspicious_ext} suspicious file-extension events detected"
        )

    if max_rename_1s > 0:
        indicators.append(
            f"{max_rename_1s} file renames detected within 1 second"
        )

    if max_fs_1s > 0:
        indicators.append(
            f"{max_fs_1s} filesystem events detected within 1 second"
        )

    if filesystem_burst:
        indicators.append(
            "Rapid filesystem activity burst detected"
        )

    if fs_modified > 0:
        indicators.append(
            f"{fs_modified} file modification events detected"
        )

    return {
        "risk_level": risk["risk_level"],
        "probability": risk["probability"],
        "main_contributing_indicators": indicators,
        "timestamp": datetime.utcnow().isoformat()
    }
