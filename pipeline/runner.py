"""Top-level pipeline runner — orchestrates collectors → normalize → embed → cluster → classify → score → brief.

Collector toggles (set in .env or environment):
  COLLECTOR_RSS=true        # default ON
  COLLECTOR_REDDIT=false    # default OFF
  COLLECTOR_HN=false        # default OFF
  COLLECTOR_GOOGLE=false    # default OFF
  COLLECTOR_YOUTUBE=false   # default OFF
  COLLECTOR_GITHUB=false    # default OFF
  COLLECTOR_AMAZON=false    # default OFF
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional

log = logging.getLogger(__name__)


def _flag(name: str, default: bool) -> bool:
    """Read a boolean env var; fall back to *default*."""
    val = os.getenv(name, "").strip().lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


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
        "growth":           min(avg_engagement / 1000, 1.0),
        "source_diversity": len(set(sources)) / len(all_sources),
        "commercial_intent": commercial_hits / max(len(signals), 1),
        "novelty":          0.7,
        "persistence":      0.5,
        "signal_count":     len(signals),
    }


def run_pipeline(niche_filter: Optional[str] = None, db=None) -> List[dict]:
    """Run full pipeline; return list of scored trend dicts."""

    # ── 1. Collect — respect per-collector toggles from .env ───────────────────────────
    collectors_to_run = []

    if _flag("COLLECTOR_RSS",     default=True):
        from collectors.rss           import collect as rss_collect
        collectors_to_run.append(("rss",     rss_collect))

    if _flag("COLLECTOR_REDDIT",  default=False):
        from collectors.reddit_free   import collect as reddit_collect
        collectors_to_run.append(("reddit",  reddit_collect))

    if _flag("COLLECTOR_HN",      default=False):
        from collectors.hackernews    import collect as hn_collect
        collectors_to_run.append(("hn",      hn_collect))

    if _flag("COLLECTOR_GOOGLE",  default=False):
        from collectors.google_trends import collect as gt_collect
        collectors_to_run.append(("google",  gt_collect))

    if _flag("COLLECTOR_YOUTUBE", default=False):
        from collectors.youtube_free  import collect as yt_collect
        collectors_to_run.append(("youtube", yt_collect))

    if _flag("COLLECTOR_GITHUB",  default=False):
        from collectors.github_trending import collect as gh_collect
        collectors_to_run.append(("github",  gh_collect))

    if _flag("COLLECTOR_AMAZON",  default=False):
        from collectors.amazon_suggest  import collect as amz_collect
        collectors_to_run.append(("amazon",  amz_collect))

    if not collectors_to_run:
        log.warning("All collectors are disabled — nothing to scan.")
        return []

    log.info("Active collectors: %s", [name for name, _ in collectors_to_run])

    raw_signals: List[dict] = []
    for name, fn in collectors_to_run:
        try:
            results = fn()
            log.info("  [%s] %d signals", name, len(results))
            raw_signals.extend(results)
        except Exception as e:
            log.warning("Collector [%s] failed: %s", name, e)

    log.info("Collected %d raw signals total", len(raw_signals))

    if not raw_signals:
        log.warning("No signals collected — aborting pipeline.")
        return []

    # ── 2. Normalize ─────────────────────────────────────────────────────────────────
    from pipeline.normalizer import normalize
    signals = normalize(raw_signals)
    log.info("Normalized to %d signals", len(signals))

    # ── 3. Embed ──────────────────────────────────────────────────────────────────────
    from pipeline.embedder import embed_signals
    signals = embed_signals(signals)

    # ── 4. Cluster ────────────────────────────────────────────────────────────────────
    from pipeline.clusterer import cluster_signals
    clusters = cluster_signals(signals)
    log.info("Found %d clusters", len(clusters))

    # ── 5. Classify ──────────────────────────────────────────────────────────────────
    from pipeline.classifier import classify_clusters
    clusters = classify_clusters(clusters)

    # ── 6. Convert TrendCluster → dict ────────────────────────────────────────────────
    cluster_dicts = [_cluster_to_dict(c) for c in clusters]

    # ── 7. Score ─────────────────────────────────────────────────────────────────────
    from pipeline.scorer_db import score_clusters_with_db
    cluster_dicts = score_clusters_with_db(cluster_dicts, db=db)

    # ── 8. Filter by niche ──────────────────────────────────────────────────────────
    if niche_filter:
        cluster_dicts = [c for c in cluster_dicts if c.get("niche") == niche_filter]

    # ── 9. LLM briefs (top 10 only) ──────────────────────────────────────────────────
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
