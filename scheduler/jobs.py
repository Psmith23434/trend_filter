"""APScheduler jobs — runs the full pipeline on a schedule."""
from apscheduler.schedulers.background import BackgroundScheduler
from collectors.reddit import RedditCollector
from collectors.hackernews import HackerNewsCollector
from collectors.rss import RSSCollector
from pipeline.normalizer import normalize
from pipeline.embedder import embed_signals
from pipeline.clusterer import cluster_signals
from pipeline.scorer import score_clusters
from llm.brief_generator import generate_brief


def run_pipeline():
    print("[Scheduler] Running trend pipeline...")
    collectors = [
        RedditCollector(),
        HackerNewsCollector(),
        RSSCollector(),
    ]
    raw = []
    for c in collectors:
        raw.extend(c.collect())

    signals = normalize(raw)
    signals = embed_signals(signals)
    clusters = cluster_signals(signals)
    clusters = score_clusters(clusters)

    top = clusters[:10]
    for cluster in top:
        generate_brief(cluster)
        print(f"[{cluster.urgency.upper()}] {cluster.representative_title} (score={cluster.score:.2f})")
        for idea in (cluster.product_ideas or []):
            print(f"  💡 {idea}")

    print(f"[Scheduler] Done. Found {len(clusters)} clusters, showing top {len(top)}.")
    return top


def start_scheduler(interval_minutes: int = 60):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "interval", minutes=interval_minutes, id="trend_pipeline")
    scheduler.start()
    return scheduler
