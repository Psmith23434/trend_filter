from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import ScanRun, TrendRecord


# ── Scan runs ──────────────────────────────────────────────────────────────────

def create_scan_run(db: Session) -> ScanRun:
    run = ScanRun(started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_scan_run(db: Session, run_id: int, signal_count: int, cluster_count: int) -> ScanRun:
    run = db.query(ScanRun).filter(ScanRun.id == run_id).first()
    if run:
        run.finished_at = datetime.utcnow()
        run.signal_count = signal_count
        run.cluster_count = cluster_count
        db.commit()
        db.refresh(run)
    return run


def get_recent_runs(db: Session, limit: int = 20) -> List[ScanRun]:
    return db.query(ScanRun).order_by(ScanRun.started_at.desc()).limit(limit).all()


# ── Trend records ──────────────────────────────────────────────────────────────

def save_trend(db: Session, scan_run_id: int, trend: dict) -> TrendRecord:
    record = TrendRecord(
        scan_run_id=scan_run_id,
        title=trend.get("title", ""),
        label=trend.get("label", trend.get("title", "")),
        niche=trend.get("niche", "general"),
        signal_type=trend.get("signal_type", "rising_topic"),
        score=trend.get("score", 0.0),
        growth=trend.get("growth", 0.0),
        source_diversity=trend.get("source_diversity", 0.0),
        commercial_intent=trend.get("commercial_intent", 0.0),
        novelty=trend.get("novelty", 0.0),
        persistence=trend.get("persistence", 0.0),
        urgency=trend.get("urgency", "low"),
        sources=trend.get("sources", []),
        evidence_urls=trend.get("evidence_urls", []),
        keywords=trend.get("keywords", []),
        signal_count_in_cluster=trend.get("signal_count", 1),
        brief=trend.get("brief", ""),
        product_ideas=trend.get("product_ideas", []),
        action_plan=trend.get("action_plan", []),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_trends(
    db: Session,
    niche: Optional[str] = None,
    signal_type: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 50,
    since_hours: int = 24,
) -> List[TrendRecord]:
    cutoff = datetime.utcnow() - timedelta(hours=since_hours)
    q = db.query(TrendRecord).filter(TrendRecord.created_at >= cutoff)
    if niche:
        q = q.filter(TrendRecord.niche == niche)
    if signal_type:
        q = q.filter(TrendRecord.signal_type == signal_type)
    if urgency:
        q = q.filter(TrendRecord.urgency == urgency)
    return q.order_by(TrendRecord.score.desc()).limit(limit).all()


def get_trend_by_id(db: Session, trend_id: int) -> Optional[TrendRecord]:
    return db.query(TrendRecord).filter(TrendRecord.id == trend_id).first()


# ── Historical helpers for scorer ──────────────────────────────────────────────

def title_seen_before(db: Session, title: str, lookback_days: int = 7) -> int:
    """Return how many times this title appeared in the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    return (
        db.query(func.count(TrendRecord.id))
        .filter(TrendRecord.title == title, TrendRecord.created_at >= cutoff)
        .scalar()
        or 0
    )


def title_persistence_score(db: Session, title: str, lookback_days: int = 30) -> float:
    """0-1 persistence: fraction of days in lookback window where title appeared."""
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    days_seen = (
        db.query(
            func.count(
                func.distinct(
                    func.date_trunc("day", TrendRecord.created_at)
                )
            )
        )
        .filter(TrendRecord.title == title, TrendRecord.created_at >= cutoff)
        .scalar()
        or 0
    )
    return min(days_seen / lookback_days, 1.0)
