"""Score each TrendCluster."""
import os
from typing import List
from pipeline.models import TrendCluster

COMMERCIAL_KEYWORDS = [
    "buy", "best", "review", "price", "cheap", "deal", "product",
    "tool", "course", "template", "kit", "guide", "software", "app",
    "sell", "store", "shop", "amazon", "etsy", "gig",
]

# Scoring weights (overridable via .env)
W_GROWTH      = float(os.getenv("SCORE_WEIGHT_GROWTH",      0.30))
W_DIVERSITY   = float(os.getenv("SCORE_WEIGHT_DIVERSITY",   0.20))
W_COMMERCIAL  = float(os.getenv("SCORE_WEIGHT_COMMERCIAL",  0.20))
W_NOVELTY     = float(os.getenv("SCORE_WEIGHT_NOVELTY",     0.15))
W_PERSISTENCE = float(os.getenv("SCORE_WEIGHT_PERSISTENCE", 0.15))

ALL_SOURCES = {"reddit", "google_trends", "hackernews", "rss", "youtube", "producthunt"}


def _growth_score(cluster: TrendCluster) -> float:
    """Proxy: average engagement across signals, normalized to 0-1."""
    if not cluster.signals:
        return 0.0
    avg = sum(s.engagement for s in cluster.signals) / len(cluster.signals)
    return min(avg / 1000, 1.0)  # cap at 1000 engagement units


def _diversity_score(cluster: TrendCluster) -> float:
    """Fraction of known sources represented."""
    return len(set(cluster.sources)) / len(ALL_SOURCES)


def _commercial_score(cluster: TrendCluster) -> float:
    """Fraction of signals containing commercial keywords."""
    hits = sum(
        1 for s in cluster.signals
        if any(kw in (s.title + s.text).lower() for kw in COMMERCIAL_KEYWORDS)
    )
    return hits / max(len(cluster.signals), 1)


def _novelty_score(cluster: TrendCluster) -> float:
    """Placeholder: in production, compare against historical DB."""
    return 0.7  # default medium-novelty until DB is wired in


def _persistence_score(cluster: TrendCluster) -> float:
    """Placeholder: in production, check if cluster appeared in previous runs."""
    return 0.5


def score_clusters(clusters: List[TrendCluster]) -> List[TrendCluster]:
    for c in clusters:
        c.growth_score      = _growth_score(c)
        c.diversity_score   = _diversity_score(c)
        c.commercial_score  = _commercial_score(c)
        c.novelty_score     = _novelty_score(c)
        c.persistence_score = _persistence_score(c)
        c.score = (
            W_GROWTH      * c.growth_score +
            W_DIVERSITY   * c.diversity_score +
            W_COMMERCIAL  * c.commercial_score +
            W_NOVELTY     * c.novelty_score +
            W_PERSISTENCE * c.persistence_score
        )
    return sorted(clusters, key=lambda c: c.score, reverse=True)
