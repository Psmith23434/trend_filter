from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from .session import Base


class ScanRun(Base):
    """One full pipeline execution."""
    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    signal_count = Column(Integer, default=0)
    cluster_count = Column(Integer, default=0)


class TrendRecord(Base):
    """One scored trend cluster from a scan run."""
    __tablename__ = "trend_records"

    id = Column(Integer, primary_key=True, index=True)
    scan_run_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Identity
    title = Column(String(512))
    label = Column(String(512))  # display label / best keyword
    niche = Column(String(64), index=True)  # commerce/business/tech_ai/content/general
    signal_type = Column(String(64))        # rising_topic / commercial_intent / etc.

    # Scores
    score = Column(Float, default=0.0)
    growth = Column(Float, default=0.0)
    source_diversity = Column(Float, default=0.0)
    commercial_intent = Column(Float, default=0.0)
    novelty = Column(Float, default=0.0)
    persistence = Column(Float, default=0.0)
    urgency = Column(String(16), default="low")  # low / medium / high

    # Evidence
    sources = Column(JSON, default=list)       # list of source names
    evidence_urls = Column(JSON, default=list)  # list of URLs
    keywords = Column(JSON, default=list)
    signal_count_in_cluster = Column(Integer, default=1)

    # LLM output
    brief = Column(Text, nullable=True)
    product_ideas = Column(JSON, default=list)  # list of strings
    action_plan = Column(JSON, default=list)    # list of steps
