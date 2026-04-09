"""FastAPI entry point — Phase 2 edition with DB persistence + CSV export."""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from db import get_db, Base, engine
from db import crud
from api.export import trends_to_csv

# Create tables on startup (idempotent — use Alembic for real migrations)
Base.metadata.create_all(bind=engine)

NICHES = {
    "commerce": "🛒 Commerce",
    "business": "💡 Business",
    "tech_ai": "🤖 Tech & AI",
    "content": "🎬 Content",
    "general": "🌍 General",
}

SIGNAL_TYPES = [
    "rising_topic",
    "commercial_intent",
    "viral_content",
    "new_product",
    "search_surge",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background scheduler on boot."""
    interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "60"))
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        from scheduler.jobs import start_scheduler
        start_scheduler(interval_minutes=interval)
    yield


app = FastAPI(
    title="Trend Filter API",
    description="Self-hosted trend discovery — Phase 2 with DB persistence.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve dashboard at /dashboard/ ──────────────────────────────────────────────
_dashboard_dir = Path(__file__).parent.parent / "dashboard"
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")


# ── Status ──────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "version": "2.0.0",
        "niches": list(NICHES.keys()),
        "dashboard": "/dashboard/",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/niches")
def list_niches():
    return [{"id": k, "label": v} for k, v in NICHES.items()]


# ── Scan ────────────────────────────────────────────────────────────────────────

@app.post("/scan")
def run_scan(
    niche: Optional[str] = Query(None),
    grouped: bool = Query(True),
    save: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Run the full pipeline.
    - niche: filter output to one niche
    - grouped: group results by niche (default True)
    - save: persist results to DB (default True)
    """
    from pipeline.runner import run_pipeline

    run_record = crud.create_scan_run(db) if save else None

    try:
        results = run_pipeline(niche_filter=niche, db=db if save else None)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if save and run_record:
        for trend in results:
            crud.save_trend(db, run_record.id, trend)
        crud.finish_scan_run(
            db, run_record.id,
            signal_count=sum(t.get("signal_count", 1) for t in results),
            cluster_count=len(results),
        )

    if grouped:
        output: dict = {}
        for niche_id in NICHES:
            output[niche_id] = [t for t in results if t.get("niche") == niche_id]
        return {"scan_run_id": run_record.id if run_record else None, "grouped": output}

    return {"scan_run_id": run_record.id if run_record else None, "trends": results}


# ── Trends (DB read) ────────────────────────────────────────────────────────────

@app.get("/trends")
def get_trends(
    niche: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    since_hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Return stored trends from DB with optional filters."""
    trends = crud.get_trends(
        db, niche=niche, signal_type=signal_type,
        urgency=urgency, limit=limit, since_hours=since_hours,
    )
    return {"count": len(trends), "trends": [
        {
            "id": t.id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "niche": t.niche,
            "signal_type": t.signal_type,
            "urgency": t.urgency,
            "score": t.score,
            "title": t.title,
            "label": t.label,
            "brief": t.brief,
            "growth": t.growth,
            "source_diversity": t.source_diversity,
            "commercial_intent": t.commercial_intent,
            "novelty": t.novelty,
            "persistence": t.persistence,
            "signal_count": t.signal_count_in_cluster,
            "sources": t.sources,
            "keywords": t.keywords,
            "evidence_urls": t.evidence_urls,
            "product_ideas": t.product_ideas,
            "action_plan": t.action_plan,
        }
        for t in trends
    ]}


@app.get("/trends/{trend_id}")
def get_trend(trend_id: int, db: Session = Depends(get_db)):
    trend = crud.get_trend_by_id(db, trend_id)
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")
    return trend


# ── Export ──────────────────────────────────────────────────────────────────────

@app.get("/trends/export/csv")
def export_csv(
    niche: Optional[str] = Query(None),
    since_hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Download all matching trends as a CSV file."""
    trends = crud.get_trends(db, niche=niche, limit=500, since_hours=since_hours)
    csv_data = trends_to_csv(trends)
    filename = f"trends_{niche or 'all'}.csv"
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Scan history ────────────────────────────────────────────────────────────────

@app.get("/runs")
def list_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    runs = crud.get_recent_runs(db, limit=limit)
    return {"runs": [
        {
            "id": r.id,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "signal_count": r.signal_count,
            "cluster_count": r.cluster_count,
        }
        for r in runs
    ]}
