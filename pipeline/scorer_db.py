"""DB-aware scorer: wraps pipeline/scorer.py and injects real novelty + persistence."""
from __future__ import annotations
import os
from typing import List

W_GROWTH = float(os.getenv("W_GROWTH", "0.30"))
W_DIVERSITY = float(os.getenv("W_DIVERSITY", "0.20"))
W_COMMERCIAL = float(os.getenv("W_COMMERCIAL", "0.20"))
W_NOVELTY = float(os.getenv("W_NOVELTY", "0.15"))
W_PERSISTENCE = float(os.getenv("W_PERSISTENCE", "0.15"))

URGENCY_HIGH = float(os.getenv("URGENCY_HIGH", "0.70"))
URGENCY_MED = float(os.getenv("URGENCY_MED", "0.45"))


def _urgency(score: float) -> str:
    if score >= URGENCY_HIGH:
        return "high"
    if score >= URGENCY_MED:
        return "medium"
    return "low"


def score_clusters_with_db(clusters: List[dict], db=None) -> List[dict]:
    """
    Re-score clusters using real historical novelty + persistence from DB.
    Falls back to static scorer values when db is None.
    """
    from db.crud import title_seen_before, title_persistence_score

    results = []
    for cluster in clusters:
        title = cluster.get("title", "")

        growth = float(cluster.get("growth", 0.5))
        diversity = float(cluster.get("source_diversity", 0.5))
        commercial = float(cluster.get("commercial_intent", 0.5))

        if db is not None:
            seen = title_seen_before(db, title, lookback_days=7)
            novelty = max(0.0, 1.0 - (seen / 10.0))  # 0 seen → 1.0 novelty
            persistence = title_persistence_score(db, title, lookback_days=30)
        else:
            novelty = float(cluster.get("novelty", 0.5))
            persistence = float(cluster.get("persistence", 0.5))

        score = (
            W_GROWTH * growth
            + W_DIVERSITY * diversity
            + W_COMMERCIAL * commercial
            + W_NOVELTY * novelty
            + W_PERSISTENCE * persistence
        )
        score = round(min(score, 1.0), 4)

        updated = dict(cluster)
        updated["novelty"] = round(novelty, 4)
        updated["persistence"] = round(persistence, 4)
        updated["score"] = score
        updated["urgency"] = _urgency(score)
        results.append(updated)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
