from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(BASE_DIR, "ml"))
sys.path.insert(1, os.path.join(BASE_DIR, "xai"))
sys.path.insert(2, os.path.join(BASE_DIR, "backend"))

from alert_builder import build_alert
from database import SessionLocal, MonitoringCycle, DetectionRecord
from response.response_handler import handle_response


app = FastAPI(
    title="AI-Based Early Ransomware Detection API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_utc():
    return datetime.utcnow()


def indicators_to_text(indicators):
    if not indicators:
        return ""
    return ", ".join(str(x) for x in indicators)


def cycle_to_dict(cycle):
    return {
        "id": cycle.id,
        "timestamp": cycle.timestamp.isoformat() if cycle.timestamp else None,
        "window_seconds": cycle.window_seconds,
        "risk_level": cycle.risk_level,
        "probability": cycle.probability,
        "events_observed": cycle.events_observed,
        "files_observed": cycle.files_observed,
        "suspicious_files": cycle.suspicious_files,
        "high_risk_files": cycle.high_risk_files,
        "filesystem_events": cycle.filesystem_events,
        "indicators": (
            cycle.indicators.split(", ")
            if cycle.indicators
            else []
        ),
        "response_action": cycle.response_action,
        "is_incident": cycle.is_incident,
    }


@app.get("/health")
def health():
    return {
        "status": "online",
        "service": "ransomware-detection-api",
    }


@app.post("/analyze")
def analyze(feature_row: dict):
    alert = build_alert(feature_row)

    risk_level = alert.get("risk_level", "Safe")
    probability = float(alert.get("probability", 0.0))
    indicators = alert.get("main_contributing_indicators", [])

    events_observed = int(feature_row.get("events_observed", 0) or 0)
    files_observed = int(feature_row.get("files_observed", 0) or 0)
    suspicious_files = int(feature_row.get("suspicious_files", 0) or 0)
    high_risk_files = int(feature_row.get("high_risk_files", 0) or 0)
    filesystem_events = int(
        feature_row.get("filesystem_events", 0) or 0
    )

    db = SessionLocal()

    try:
        previous = (
            db.query(MonitoringCycle)
            .order_by(MonitoringCycle.id.desc())
            .first()
        )

        incident = False

        if risk_level == "High Risk":
            if previous is None:
                incident = True
            elif previous.risk_level != "High Risk":
                incident = True
            elif previous.timestamp:
                if now_utc() - previous.timestamp > timedelta(seconds=60):
                    incident = True

        # Execute the controlled response layer.
        # No process name is supplied here, so the API cannot
        # terminate arbitrary processes.
        response_result = handle_response(alert)

        response_action = response_result.get("action", "none")

        if response_result.get("mitigation"):
            response_action = (
                f"{response_action} | "
                f"{response_result['mitigation']}"
            )
        elif response_result.get("message"):
            response_action = response_result["message"]

        cycle = MonitoringCycle(
            risk_level=risk_level,
            probability=probability,
            events_observed=events_observed,
            files_observed=files_observed,
            suspicious_files=suspicious_files,
            high_risk_files=high_risk_files,
            filesystem_events=filesystem_events,
            indicators=indicators_to_text(indicators),
            response_action=response_action,
            is_incident=incident,
        )

        db.add(cycle)
        db.commit()
        db.refresh(cycle)

        if risk_level != "Safe":
            detection = DetectionRecord(
                risk_level=risk_level,
                probability=probability,
                files_affected=files_observed,
                suspicious_files=suspicious_files,
                high_risk_files=high_risk_files,
                indicators=indicators_to_text(indicators),
                response_action=response_action,
                cycle_id=cycle.id,
            )

            db.add(detection)
            db.commit()

        result = dict(alert)

        result.update(
            {
                "cycle_id": cycle.id,
                "events_observed": events_observed,
                "files_observed": files_observed,
                "suspicious_files": suspicious_files,
                "high_risk_files": high_risk_files,
                "filesystem_events": filesystem_events,
                "is_incident": incident,
                "response_action": response_action,
            }
        )

        return result

    finally:
        db.close()


@app.get("/alerts")
def get_alerts(limit: int = 20):
    limit = max(1, min(limit, 200))

    db = SessionLocal()

    try:
        records = (
            db.query(DetectionRecord)
            .order_by(DetectionRecord.id.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": r.id,
                "timestamp": (
                    r.timestamp.isoformat()
                    if r.timestamp
                    else None
                ),
                "risk_level": r.risk_level,
                "probability": r.probability,
                "files_affected": r.files_affected,
                "suspicious_files": r.suspicious_files,
                "high_risk_files": r.high_risk_files,
                "indicators": (
                    r.indicators.split(", ")
                    if r.indicators
                    else []
                ),
                "response_action": r.response_action,
                "cycle_id": r.cycle_id,
            }
            for r in records
        ]

    finally:
        db.close()


@app.get("/history")
def get_history(hours: int = 24, limit: int = 200):
    hours = max(1, min(hours, 168))
    limit = max(1, min(limit, 1000))

    cutoff = now_utc() - timedelta(hours=hours)

    db = SessionLocal()

    try:
        records = (
            db.query(MonitoringCycle)
            .filter(MonitoringCycle.timestamp >= cutoff)
            .order_by(MonitoringCycle.timestamp.desc())
            .limit(limit)
            .all()
        )

        return {
            "hours": hours,
            "count": len(records),
            "items": [cycle_to_dict(r) for r in records],
        }

    finally:
        db.close()


@app.get("/stats")
def get_stats(hours: int = 24):
    hours = max(1, min(hours, 168))

    cutoff = now_utc() - timedelta(hours=hours)

    db = SessionLocal()

    try:
        cycles = (
            db.query(MonitoringCycle)
            .filter(MonitoringCycle.timestamp >= cutoff)
            .all()
        )

        total_cycles = len(cycles)

        events_observed = sum(
            c.events_observed or 0 for c in cycles
        )

        files_observed = sum(
            c.files_observed or 0 for c in cycles
        )

        suspicious_activities = sum(
            1 for c in cycles
            if c.risk_level == "Suspicious"
        )

        high_risk_detections = sum(
            1 for c in cycles
            if c.risk_level == "High Risk"
        )

        ransomware_incidents = sum(
            1 for c in cycles
            if c.is_incident
        )

        filesystem_events = sum(
            c.filesystem_events or 0 for c in cycles
        )

        probabilities = [
            float(c.probability)
            for c in cycles
            if c.probability is not None
        ]

        latest = max(
            cycles,
            key=lambda c: c.timestamp
        ) if cycles else None

        return {
            "hours": hours,
            "total_cycles": total_cycles,
            "events_observed": events_observed,
            "files_observed": files_observed,
            "filesystem_events": filesystem_events,
            "suspicious_activities": suspicious_activities,
            "high_risk_detections": high_risk_detections,
            "ransomware_incidents": ransomware_incidents,
            "average_probability": (
                round(sum(probabilities) / len(probabilities), 3)
                if probabilities
                else 0.0
            ),
            "latest": (
                cycle_to_dict(latest)
                if latest
                else None
            ),
        }

    finally:
        db.close()


@app.get("/status")
def status():
    db = SessionLocal()

    try:
        latest = (
            db.query(MonitoringCycle)
            .order_by(MonitoringCycle.id.desc())
            .first()
        )

        if latest is None:
            return {
                "monitoring_active": False,
                "latest_risk": "No data yet",
                "latest_probability": 0.0,
                "latest_timestamp": None,
            }

        age_seconds = (
            now_utc() - latest.timestamp
        ).total_seconds()

        return {
            "monitoring_active": age_seconds <= 30,
            "latest_risk": latest.risk_level,
            "latest_probability": latest.probability,
            "latest_timestamp": latest.timestamp.isoformat(),
            "last_cycle": cycle_to_dict(latest),
        }

    finally:
        db.close()
