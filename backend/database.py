from datetime import datetime, timezone

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


engine = create_engine(
    "sqlite:///./events.db",
    connect_args={"check_same_thread": False},
)

Base = declarative_base()


class MonitoringCycle(Base):
    __tablename__ = "monitoring_cycles"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)

    window_seconds = Column(Integer, default=10)

    risk_level = Column(String, index=True)
    probability = Column(Float)

    events_observed = Column(Integer, default=0)
    files_observed = Column(Integer, default=0)
    suspicious_files = Column(Integer, default=0)
    high_risk_files = Column(Integer, default=0)
    filesystem_events = Column(Integer, default=0)

    indicators = Column(String, default="")
    response_action = Column(String, default="No action")

    is_incident = Column(Boolean, default=False)


class DetectionRecord(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)

    risk_level = Column(String, index=True)
    probability = Column(Float)

    files_affected = Column(Integer, default=0)
    suspicious_files = Column(Integer, default=0)
    high_risk_files = Column(Integer, default=0)

    indicators = Column(String, default="")
    response_action = Column(String, default="Alert generated")

    cycle_id = Column(Integer)


Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
