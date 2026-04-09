"""FastAPI entry point."""
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from scheduler.jobs import start_scheduler, run_pipeline
from pipeline.models import NICHES, NICHE_LABELS

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    scheduler = start_scheduler(interval_minutes=60)
    yield
    scheduler.shutdown()


app = FastAPI(title="Trend Filter", version="0.2.0", lifespan=lifespan)


def _cluster_to_dict(c) -> dict:
    return {
        "id":           c.id,
        "title":        c.representative_title,
        "score":        round(c.score, 3),
        "urgency":      c.urgency,
        "niche":        c.niche,
        "niche_label":  NICHE_LABELS.get(c.niche, c.niche),
        "signal_type":  c.signal_type,
        "sources":      c.sources,
        "brief":        c.brief,
        "product_ideas": c.product_ideas,
    }


@app.get("/")
def root():
    return {"message": "Trend Filter v0.2 is running.", "niches": NICHE_LABELS}


@app.post("/scan")
def scan_now(
    niche: str = Query(default=None, description="Filter by niche: commerce | business | tech_ai | content | general"),
    grouped: bool = Query(default=True, description="Group results by niche")
):
    """Trigger a manual pipeline run. Optionally filter by niche or return flat list."""
    clusters = run_pipeline()

    # Optional niche filter
    if niche:
        if niche not in NICHES:
            return JSONResponse({"error": f"Unknown niche '{niche}'. Valid: {NICHES}"}, status_code=400)
        clusters = [c for c in clusters if c.niche == niche]

    if grouped:
        result: dict = defaultdict(list)
        for c in clusters:
            result[c.niche].append(_cluster_to_dict(c))
        # Sort each niche group by score desc
        return JSONResponse({
            niche: sorted(items, key=lambda x: x["score"], reverse=True)
            for niche, items in result.items()
        })
    else:
        return JSONResponse([
            _cluster_to_dict(c)
            for c in sorted(clusters, key=lambda c: c.score, reverse=True)
        ])


@app.get("/niches")
def list_niches():
    """List all available niches."""
    return JSONResponse(NICHE_LABELS)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
