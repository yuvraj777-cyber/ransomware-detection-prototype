from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "xai"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
from alert_builder import build_alert
from database import SessionLocal, AlertRecord

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # tighten this before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
def analyze(feature_row: dict):
    """Receives one window of extracted features, returns + stores an alert."""
    alert = build_alert(feature_row)
    db = SessionLocal()
    record = AlertRecord(
        risk_level=alert["risk_level"],
        probability=alert["probability"],
        factors=", ".join(alert["main_contributing_indicators"])
    )
    db.add(record)
    db.commit()
    db.close()
    return alert

@app.get("/alerts")
def get_alerts(limit: int = 20):
    db = SessionLocal()
    records = db.query(AlertRecord).order_by(AlertRecord.id.desc()).limit(limit).all()
    db.close()
    return [
        {
            "id": r.id, "timestamp": str(r.timestamp), "risk_level": r.risk_level,
            "probability": r.probability, "factors": r.factors.split(", ")
        } for r in records
    ]

@app.get("/status")
def status():
    db = SessionLocal()
    latest = db.query(AlertRecord).order_by(AlertRecord.id.desc()).first()
    db.close()
    return {"latest_risk": latest.risk_level if latest else "No data yet"}