"""Unit tests for normalizer, embedder, clusterer, classifier."""
from pipeline.models import RawSignal
from datetime import datetime, timezone


def _make_signals():
    """
    Return RawSignal objects with enough samples across clear topic clusters
    so DBSCAN (eps=0.35, min_samples=2) reliably forms at least one cluster.
    Two clear groups: AI/LLM tools and Etsy/ecommerce.
    """
    return [
        # Cluster A: AI tools for sellers
        RawSignal(source="reddit",    source_id="1", title="AI tools for Etsy sellers",
                  text="People are using AI to automate Etsy listings.",
                  url="https://reddit.com/1", engagement=200,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="reddit",    source_id="2", title="Best AI tools Etsy 2026",
                  text="A roundup of AI tools for e-commerce sellers on Etsy.",
                  url="https://reddit.com/2", engagement=150,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="rss",       source_id="5", title="AI automation for Etsy shop owners",
                  text="How Etsy sellers are using AI to write product descriptions automatically.",
                  url="https://rss.com/1", engagement=90,
                  published_at=datetime.now(timezone.utc), meta={}),
        # Cluster B: Open source LLMs
        RawSignal(source="hackernews", source_id="3", title="Open source LLM released on GitHub",
                  text="A new open source language model was released on GitHub today.",
                  url="https://hn.com/1", engagement=500,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="hackernews", source_id="4", title="Local LLM runs on CPU without GPU",
                  text="Developers are running large language models locally without a GPU.",
                  url="https://hn.com/2", engagement=400,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="rss",       source_id="6", title="New open source language model beats GPT",
                  text="An open source LLM outperforms commercial models on several benchmarks.",
                  url="https://rss.com/2", engagement=300,
                  published_at=datetime.now(timezone.utc), meta={}),
    ]


def test_normalizer():
    from pipeline.normalizer import normalize
    signals = normalize(_make_signals())
    assert len(signals) == 6
    for s in signals:
        assert isinstance(s, RawSignal)
        assert s.title
        assert s.source


def test_embedder():
    from pipeline.normalizer import normalize
    from pipeline.embedder import embed_signals
    signals = normalize(_make_signals())
    embedded = embed_signals(signals)
    for s in embedded:
        assert s.embedding is not None
        assert len(s.embedding) > 0


def test_clusterer_returns_clusters():
    from pipeline.normalizer import normalize
    from pipeline.embedder import embed_signals
    from pipeline.clusterer import cluster_signals
    signals = normalize(_make_signals())
    signals = embed_signals(signals)
    # Use relaxed eps so small test batches still form clusters
    clusters = cluster_signals(signals, eps=0.35, min_samples=2)
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
    signals = normalize(_make_signals())
    signals = embed_signals(signals)
    clusters = cluster_signals(signals, eps=0.35, min_samples=2)
    clusters = classify_clusters(clusters)
    for c in clusters:
        assert c.niche in {"commerce", "business", "tech_ai", "content", "general"}
        assert c.signal_type in {
            "rising_topic", "commercial_intent", "viral_content", "new_product", "search_surge"
        }
