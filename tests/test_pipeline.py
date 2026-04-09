"""Unit tests for normalizer, embedder, clusterer, classifier."""
import pytest
from pipeline.models import RawSignal


SAMPLE_RAW = [
    {"title": "AI tools for Etsy sellers", "text": "People are using AI to automate Etsy listings.",
     "url": "https://reddit.com/1", "source": "reddit", "engagement": 200, "published_at": None, "meta": {}},
    {"title": "Best AI tools Etsy 2026", "text": "A roundup of AI tools for e-commerce sellers.",
     "url": "https://reddit.com/2", "source": "reddit", "engagement": 150, "published_at": None, "meta": {}},
    {"title": "Open source LLM released", "text": "A new open source language model was released on GitHub.",
     "url": "https://hn.com/1", "source": "hackernews", "engagement": 500, "published_at": None, "meta": {}},
    {"title": "Local LLM runs on CPU", "text": "Developers are running LLMs locally without a GPU.",
     "url": "https://hn.com/2", "source": "hackernews", "engagement": 400, "published_at": None, "meta": {}},
]


def test_normalizer():
    from pipeline.normalizer import normalize
    signals = normalize(SAMPLE_RAW)
    assert len(signals) == len(SAMPLE_RAW)
    for s in signals:
        assert isinstance(s, RawSignal)
        assert s.title
        assert s.source


def test_embedder():
    from pipeline.normalizer import normalize
    from pipeline.embedder import embed_signals
    signals = normalize(SAMPLE_RAW)
    embedded = embed_signals(signals)
    for s in embedded:
        assert s.embedding is not None
        assert len(s.embedding) > 0


def test_clusterer_returns_clusters():
    from pipeline.normalizer import normalize
    from pipeline.embedder import embed_signals
    from pipeline.clusterer import cluster_signals
    signals = normalize(SAMPLE_RAW)
    signals = embed_signals(signals)
    clusters = cluster_signals(signals)
    # With 4 clearly related signals we expect at least 1 cluster
    assert len(clusters) >= 1
    for c in clusters:
        assert c.id
        assert c.representative_title
        assert len(c.signals) >= 1


def test_classifier_assigns_niche():
    from pipeline.normalizer import normalize
    from pipeline.embedder import embed_signals
    from pipeline.clusterer import cluster_signals
    from pipeline.classifier import classify_clusters
    signals = normalize(SAMPLE_RAW)
    signals = embed_signals(signals)
    clusters = cluster_signals(signals)
    clusters = classify_clusters(clusters)
    for c in clusters:
        assert c.niche in {"commerce", "business", "tech_ai", "content", "general"}
        assert c.signal_type in {
            "rising_topic", "commercial_intent", "viral_content", "new_product", "search_surge"
        }
