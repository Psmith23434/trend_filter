"""APScheduler jobs — runs the full pipeline on a schedule."""
from apscheduler.schedulers.background import BackgroundScheduler
from collectors.reddit_free import RedditFreeCollector
from collectors.hackernews import HackerNewsCollector
from collectors.rss import RSSCollector
from collectors.google_trends import GoogleTrendsCollector
from collectors.youtube_free import YouTubeFreeCollector
from collectors.github_trending import GitHubTrendingCollector
from collectors.amazon_suggest import AmazonSuggestCollector
from pipeline.normalizer import normalize
from pipeline.embedder import embed_signals
from pipeline.clusterer import cluster_signals
from pipeline.scorer import score_clusters
from llm.brief_generator import generate_brief


def run_pipeline():
    print("[Scheduler] Running trend pipeline (no-API mode)...")
    collectors = [
        RedditFreeCollector(),
        HackerNewsCollector(),
        RSSCollector(),
        GoogleTrendsCollector(),
        YouTubeFreeCollector(),
        GitHubTrendingCollector(),
        AmazonSuggestCollector(),
    ]
    raw = []
    for c in collectors:
        print(f"  → Collecting from {c.source_name}...")
        raw.extend(c.collect())

    print(f"[Scheduler] {len(raw)} raw signals collected. Normalizing...")
    signals = normalize(raw)
    print(f"[Scheduler] {len(signals)} signals after dedup. Embedding...")
    signals = embed_signals(signals)
    print("[Scheduler] Clustering...")
    clusters = cluster_signals(signals)
    print(f"[Scheduler] {len(clusters)} clusters found. Scoring...")
    clusters = score_clusters(clusters)

    top = clusters[:10]
    print(f"[Scheduler] Generating briefs for top {len(top)} trends...")
    for cluster in top:
        generate_brief(cluster)
        urgency = (cluster.urgency or "?").upper()
        print(f"  [{urgency}] {cluster.representative_title} (score={cluster.score:.2f})")
        for idea in (cluster.product_ideas or []):
            print(f"    💡 {idea}")

    print(f"[Scheduler] Done.")
    return top


def start_scheduler(interval_minutes: int = 60):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "interval", minutes=interval_minutes, id="trend_pipeline")
    scheduler.start()
    print(f"[Scheduler] Pipeline scheduled every {interval_minutes} minutes.")
    return scheduler
