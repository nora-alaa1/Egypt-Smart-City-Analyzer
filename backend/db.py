"""
SmartCity AI — Database connection & ORM models (SQLAlchemy).

Supports PostgreSQL (preferred) and SQLite fallback.
Maps to the following physical tables:

  areas          — id, name, latitude, longitude
  places         — id, name, category, latitude, longitude, area_id
  area_metrics   — area_id, population, avg_rent, competitor_count,
                   traffic_score, accessibility_score
"""

import os
from datetime import datetime


def init_db():
    Base.metadata.create_all(bind=_engine)



from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    ForeignKey, DateTime, create_engine, Text, text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ── Try loading .env (optional) ──
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Configuration ──
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./smartcity.db",          # fallback SQLite
)

# ── Engine ──
_engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

Base = declarative_base()


# ══════════════════════════════════════════════════════════════
#  ORM Models
# ══════════════════════════════════════════════════════════════

class Area(Base):
    __tablename__ = "areas"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    name      = Column(String(200), nullable=False)
    latitude  = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    places   = relationship("Place", back_populates="area")
    metrics  = relationship("AreaMetric", uselist=False, back_populates="area")


class Place(Base):
    __tablename__ = "places"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    name      = Column(String(300), nullable=False)
    category  = Column(String(100), nullable=False, index=True)
    latitude  = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_id   = Column(Integer, ForeignKey("areas.id"), nullable=True)

    area = relationship("Area", back_populates="places")


class AreaMetric(Base):
    __tablename__ = "area_metrics"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    area_id            = Column(Integer, ForeignKey("areas.id"), unique=True, nullable=False)
    population         = Column(Integer, default=0)
    avg_rent           = Column(Float, default=0.0)        # EGP / month
    competitor_count   = Column(Integer, default=0)
    traffic_score      = Column(Float, default=0.0)        # 0–10
    accessibility_score = Column(Float, default=0.0)       # 0–10
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    area = relationship("Area", back_populates="metrics")

class PropertySuitability(Base):
    __tablename__ = "property_suitability"

    fact_id = Column(Integer, primary_key=True)
    prop_id = Column(Integer)
    area_id = Column(Integer)
    business_type_id = Column(Integer)
    suitability_score = Column(Float)
    affordability_score = Column(Float)
    recommended = Column(Boolean)

# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def get_db():
    """FastAPI dependency: yields a session."""
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=_engine)


def drop_db():
    """Drop all tables (use with caution)."""
    Base.metadata.drop_all(bind=_engine)


def get_engine():
    return _engine

class AreaBusinessScore(Base):
    __tablename__ = "area_business_scores"

    score_id = Column(Integer, primary_key=True)
    area_id = Column(Integer)
    business_type_id = Column(Integer)
    demand_index = Column(Float)
    competitor_count = Column(Integer)
    suitability_score = Column(Float)
    recommended = Column(Boolean)


class PrecomputedRecommendation(Base):
    __tablename__ = "precomputed_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_type_id = Column(Integer, nullable=False, index=True)
    area_id = Column(Integer, nullable=False)
    suitability_score = Column(Float, default=0.0)
    rank = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    area_id = Column(Integer, nullable=True)
    business_type_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


