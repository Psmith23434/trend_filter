"""Top-level pipeline runner — orchestrates collectors → normalize → embed → cluster → classify → score → brief."""
from __future__ import annotations
import logging
from typing import List, Optional

log = logging.getLogger(__name__)


def run_pipeline(niche_filter: Optional[str] = None, db=None) -> List[dict]:
    """Run full pipeline; return list of scored trend dicts."""
    # 1. Collect
    from collectors.reddit_free import collect as reddit_collect
    from collectors.hackernews import collect as hn_collect
    from collectors.rss import collect as rss_collect
    from collectors.google_trends import collect as gt_collect
    from collectors.youtube_free import collect as yt_collect
    from collectors.github_trending import collect as gh_collect
    from collectors.amazon_suggest import collect as amz_collect

    raw_signals: List[dict] = []
    for fn in (reddit_collect, hn_collect, rss_collect, gt_collect, yt_collect, gh_collect, amz_collect):
        try:
            raw_signals.extend(fn())
        except Exception as e:
            log.warning("Collector %s failed: %s", fn.__module__, e)

    log.info("Collected %d raw signals", len(raw_signals))

    # 2. Normalize
    from pipeline.normalizer import normalize
    signals = normalize(raw_signals)
    log.info("Normalized to %d signals", len(signals))

    # 3. Embed
    from pipeline.embedder import embed_signals
    signals = embed_signals(signals)

    # 4. Cluster
    from pipeline.clusterer import cluster_signals
    clusters = cluster_signals(signals)
    log.info("Found %d clusters", len(clusters))

    # 5. Classify
    from pipeline.classifier import classify_clusters
    clusters = classify_clusters(clusters)

    # 6. Score (DB-aware if db provided)
    from pipeline.scorer_db import score_clusters_with_db
    clusters = score_clusters_with_db(clusters, db=db)

    # 7. Filter by niche
    if niche_filter:
        clusters = [c for c in clusters if c.get("niche") == niche_filter]

    # 8. Generate LLM briefs (top 10 only to save cost/time)
    from llm.brief import generate_brief
    for cluster in clusters[:10]:
        try:
            brief_data = generate_brief(cluster)
            cluster["brief"] = brief_data.get("brief", "")
            cluster["product_ideas"] = brief_data.get("product_ideas", [])
            cluster["action_plan"] = brief_data.get("action_plan", [])
        except Exception as e:
            log.warning("Brief generation failed: %s", e)
            cluster.setdefault("brief", "")
            cluster.setdefault("product_ideas", [])
            cluster.setdefault("action_plan", [])

    return clusters
