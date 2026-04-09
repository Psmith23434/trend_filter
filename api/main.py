"""FastAPI entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from scheduler.jobs import start_scheduler, run_pipeline

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    scheduler = start_scheduler(interval_minutes=60)
    yield
    scheduler.shutdown()


app = FastAPI(title="Trend Filter", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Trend Filter is running."}


@app.post("/scan")
def scan_now():
    """Trigger a manual pipeline run and return top trends."""
    clusters = run_pipeline()
    return JSONResponse([
        {
            "title": c.representative_title,
            "score": round(c.score, 3),
            "urgency": c.urgency,
            "sources": c.sources,
            "brief": c.brief,
            "product_ideas": c.product_ideas,
        }
        for c in clusters
    ])


@app.get("/health")
def health():
    return {"status": "ok"}
