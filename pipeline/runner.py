"""Top-level pipeline runner — orchestrates collectors → normalize → embed → cluster → classify → score → brief."""
from __future__ import annotations
import logging
from typing import List, Optional

log = logging.getLogger(__name__)


def _cluster_to_dict(cluster) -> dict:
    """Convert a TrendCluster dataclass into the plain dict scorer_db expects."""
    signals = cluster.signals or []
    sources = list({s.source for s in signals})
    avg_engagement = sum(s.engagement for s in signals) / max(len(signals), 1)
    commercial_kws = {
        "buy", "best", "review", "price", "cheap", "deal", "product",
        "tool", "course", "template", "kit", "guide", "software", "app",
        "sell", "store", "shop", "amazon", "etsy", "gig",
    }
    commercial_hits = sum(
        1 for s in signals
        if any(kw in (s.title + " " + s.text).lower() for kw in commercial_kws)
    )
    all_sources = {"reddit", "google_trends", "hackernews", "rss", "youtube", "producthunt"}
    return {
        "id":               cluster.id,
        "title":            cluster.representative_title,
        "niche":            getattr(cluster, "niche", "general"),
        "signal_type":      getattr(cluster, "signal_type", "rising_topic"),
        "sources":          sources,
        "evidence_urls":    [s.url for s in signals if s.url],
        "keywords":         cluster.keywords or [],
        # Pre-computed sub-scores (scorer_db may override novelty + persistence)
        "growth":           min(avg_engagement / 1000, 1.0),
        "source_diversity": len(set(sources)) / len(all_sources),
        "commercial_intent": commercial_hits / max(len(signals), 1),
        "novelty":          0.7,   # placeholder — overridden by scorer_db when DB present
        "persistence":      0.5,   # placeholder — overridden by scorer_db when DB present
        "signal_count":     len(signals),
    }


def run_pipeline(niche_filter: Optional[str] = None, db=None) -> List[dict]:
    """Run full pipeline; return list of scored trend dicts."""
    # 1. Collect — uses reddit_free (no API credentials required)
    from collectors.reddit_free  import collect as reddit_collect
    from collectors.hackernews   import collect as hn_collect
    from collectors.rss          import collect as rss_collect
    from collectors.google_trends import collect as gt_collect
    from collectors.youtube_free  import collect as yt_collect
    from collectors.github_trending import collect as gh_collect
    from collectors.amazon_suggest  import collect as amz_collect

    raw_signals: List[dict] = []
    for fn in (reddit_collect, hn_collect, rss_collect, gt_collect,
               yt_collect, gh_collect, amz_collect):
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

    # 4. Cluster → returns List[TrendCluster]
    from pipeline.clusterer import cluster_signals
    clusters = cluster_signals(signals)
    log.info("Found %d clusters", len(clusters))

    # 5. Classify (niche + signal_type) — still operates on TrendCluster objects
    from pipeline.classifier import classify_clusters
    clusters = classify_clusters(clusters)

    # 6. Convert TrendCluster → dict (scorer_db works with plain dicts)
    cluster_dicts = [_cluster_to_dict(c) for c in clusters]

    # 7. Score (DB-aware: real novelty + persistence when db is provided)
    from pipeline.scorer_db import score_clusters_with_db
    cluster_dicts = score_clusters_with_db(cluster_dicts, db=db)

    # 8. Filter by niche
    if niche_filter:
        cluster_dicts = [c for c in cluster_dicts if c.get("niche") == niche_filter]

    # 9. Generate LLM briefs (top 10 only to save cost/time)
    from llm.brief_generator import generate_brief
    for cluster in cluster_dicts[:10]:
        try:
            brief_data = generate_brief(cluster)
            cluster["brief"]         = brief_data.get("brief", "")
            cluster["product_ideas"] = brief_data.get("product_ideas", [])
            cluster["action_plan"]   = brief_data.get("action_plan", [])
        except Exception as e:
            log.warning("Brief generation failed: %s", e)
            cluster.setdefault("brief", "")
            cluster.setdefault("product_ideas", [])
            cluster.setdefault("action_plan", [])

    return cluster_dicts
