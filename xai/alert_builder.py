from datetime import datetime
import sys
from pathlib import Path

from risk_score import score_risk

# Add ml folder to Python path
ml_path = Path(__file__).resolve().parent.parent / "ml"
sys.path.append(str(ml_path))

from predict import predict_risk


def build_alert(feature_row):

    # Get probability from ML model
    probability = predict_risk(feature_row)

    # Convert probability into risk level
    risk = score_risk(probability)

    return {
        "risk_level": risk["risk_level"],
        "probability": risk["probability"],
        "main_contributing_indicators": [],
        "timestamp": datetime.utcnow().isoformat()
    }