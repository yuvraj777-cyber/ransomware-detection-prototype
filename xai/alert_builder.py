from risk_scoring import score_risk
from explain_simple import top_contributing_factors
import sys
import os

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
          "..",
          "ml"
    )
)
from predict import predict_risk

def build_alert(feature_row: dict):  
     probability = predict_risk(feature_row)
     risk = score_risk(probability)
     factors = top_contributing_factors(feature_row)
     return {
         "risk_level":
          risk["risk_level"],
            "probability":
         risk["probability"],

         "main_contributing_indicators": factors,
             "timestamp": feature_row.get("window")
     }
