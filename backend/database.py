from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

engine = create_engine("sqlite:///./events.db")
Base = declarative_base()

class AlertRecord(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    risk_level = Column(String)
    probability = Column(Float)
    factors = Column(String) # store as comma-joined string for simplicity

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)