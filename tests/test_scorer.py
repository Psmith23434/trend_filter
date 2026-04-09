"""Unit tests for scorer_db — no real DB needed (db=None path)."""
from pipeline.scorer_db import score_clusters_with_db


SAMPLE_CLUSTERS = [
    {
        "id": "aaa", "title": "AI image generators",
        "niche": "tech_ai", "signal_type": "rising_topic",
        "sources": ["reddit", "hackernews"],
        "evidence_urls": [], "keywords": [],
        "growth": 0.8, "source_diversity": 0.4,
        "commercial_intent": 0.6, "novelty": 0.7, "persistence": 0.5,
        "signal_count": 5,
    },
    {
        "id": "bbb", "title": "Cheap Etsy print products",
        "niche": "commerce", "signal_type": "commercial_intent",
        "sources": ["amazon_suggest"],
        "evidence_urls": [], "keywords": [],
        "growth": 0.3, "source_diversity": 0.2,
        "commercial_intent": 0.9, "novelty": 0.5, "persistence": 0.3,
        "signal_count": 2,
    },
]


def test_scorer_returns_all_clusters():
    results = score_clusters_with_db(SAMPLE_CLUSTERS, db=None)
    assert len(results) == 2


def test_scorer_adds_score_field():
    results = score_clusters_with_db(SAMPLE_CLUSTERS, db=None)
    for r in results:
        assert "score" in r
        assert 0.0 <= r["score"] <= 1.0


def test_scorer_adds_urgency():
    results = score_clusters_with_db(SAMPLE_CLUSTERS, db=None)
    for r in results:
        assert r["urgency"] in {"high", "medium", "low"}


def test_scorer_sorts_descending():
    results = score_clusters_with_db(SAMPLE_CLUSTERS, db=None)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_scorer_no_db_uses_placeholder_novelty():
    """Without a DB session, novelty and persistence come from the input dict."""
    results = score_clusters_with_db(SAMPLE_CLUSTERS, db=None)
    # novelty should equal input value since db=None
    for r in results:
        assert r["novelty"] == 0.7 or r["novelty"] == 0.5  # matches sample data
