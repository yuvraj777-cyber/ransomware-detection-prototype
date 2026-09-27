from datetime import datetime

from risk_scoring import score_risk


def build_alert(feature_row):
    """
    Build an alert from a feature row.

    feature_row:
        Dictionary containing extracted ransomware-related features.
    """

    # Temporary probability for testing.
    # Later this will come from Utkarsh's predict_risk().
    probability = 0.8

    # Convert probability into risk level
    risk = score_risk(probability)

    return {
        "risk_level": risk["risk_level"],
        "probability": risk["probability"],
        "main_contributing_indicators": [],
        "timestamp": datetime.utcnow().isoformat()
    }