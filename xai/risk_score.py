def score_risk(probability: float) -> dict:
   if probability < 0.35:
       level = "Safe"
   elif probability < 0.7:
       level = "Suspicious"
   else:
       level = "High Risk"
   return {
       "probability":
 round(probability, 3),
       "risk_level": level
}
if __name__ == "__main__":
    print(score_risk(0.20))
    print(score_risk(0.50))
    print(score_risk(0.85))