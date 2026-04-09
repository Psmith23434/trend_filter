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
from pipeline.classifier import classify_clusters, NICHE_LABELS
from llm.brief_generator import generate_brief


def run_pipeline():
    print("[Pipeline] Starting trend pipeline (no-API mode)...")

    # --- Collect ---
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
        print(f"  → Collecting [{c.source_name}]...")
        raw.extend(c.collect())

    print(f"[Pipeline] {len(raw)} raw signals. Normalizing...")
    signals = normalize(raw)
    print(f"[Pipeline] {len(signals)} after dedup. Embedding...")
    signals = embed_signals(signals)

    print("[Pipeline] Clustering...")
    clusters = cluster_signals(signals)
    print(f"[Pipeline] {len(clusters)} clusters. Scoring...")
    clusters = score_clusters(clusters)

    print("[Pipeline] Classifying niches...")
    clusters = classify_clusters(clusters)

    # --- Brief generation for top 10 ---
    top = clusters[:10]
    print(f"[Pipeline] Generating briefs for top {len(top)} trends...")
    for cluster in top:
        generate_brief(cluster)

    # --- Print grouped output ---
    from collections import defaultdict
    by_niche: dict = defaultdict(list)
    for c in top:
        by_niche[c.niche].append(c)

    print("\n" + "="*60)
    for niche, items in sorted(by_niche.items()):
        print(f"\n{NICHE_LABELS.get(niche, niche)}")
        print("-" * 40)
        for c in items:
            urgency = (c.urgency or "?").upper()
            print(f"  [{urgency}] {c.representative_title}")
            print(f"         score={c.score:.2f} | type={c.signal_type} | sources={','.join(c.sources)}")
            for idea in (c.product_ideas or []):
                print(f"         💡 {idea}")
    print("\n" + "="*60)
    print(f"[Pipeline] Done. {len(clusters)} total clusters across {len(by_niche)} niches.")
    return top


def start_scheduler(interval_minutes: int = 60):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline, "interval", minutes=interval_minutes, id="trend_pipeline")
    scheduler.start()
    print(f"[Scheduler] Pipeline scheduled every {interval_minutes} minutes.")
    return scheduler
