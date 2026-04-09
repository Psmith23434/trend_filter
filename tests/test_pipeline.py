"""Unit tests for normalizer, embedder, clusterer, classifier."""
from pipeline.models import RawSignal
from datetime import datetime, timezone


def _make_signals():
    """
    Two clear semantic clusters so DBSCAN reliably groups them.

    After L2-normalisation, DBSCAN uses euclidean distance which equals
    sqrt(2 * (1 - cosine_similarity)).  Two sentences with cosine_sim=0.6
    produce euclidean distance ≈ 0.89.  We therefore use eps=0.80 in the
    clusterer tests, which accepts pairs with cosine_sim >= ~0.68.
    """
    return [
        # Cluster A: AI tools for Etsy / e-commerce
        RawSignal(source="reddit",     source_id="1",
                  title="AI tools for Etsy sellers",
                  text="People are using AI to automate Etsy product listings and descriptions.",
                  url="https://reddit.com/1", engagement=200,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="reddit",     source_id="2",
                  title="Best AI tools for Etsy shop owners 2026",
                  text="A roundup of the best AI tools for Etsy e-commerce sellers.",
                  url="https://reddit.com/2", engagement=150,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="rss",        source_id="5",
                  title="AI automation for Etsy sellers",
                  text="Etsy sellers are using AI automation to write product descriptions faster.",
                  url="https://rss.com/1", engagement=90,
                  published_at=datetime.now(timezone.utc), meta={}),
        # Cluster B: Open-source LLMs
        RawSignal(source="hackernews", source_id="3",
                  title="Open source LLM released on GitHub",
                  text="A new open source large language model was released on GitHub today.",
                  url="https://hn.com/1", engagement=500,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="hackernews", source_id="4",
                  title="Run a local LLM on CPU without a GPU",
                  text="Developers are running open source large language models on CPU hardware.",
                  url="https://hn.com/2", engagement=400,
                  published_at=datetime.now(timezone.utc), meta={}),
        RawSignal(source="rss",        source_id="6",
                  title="Open source language model beats GPT on benchmarks",
                  text="An open source LLM outperforms commercial language models on key benchmarks.",
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
    # eps=0.80 ↔ cosine_sim >= ~0.68 (correct for small test batches;
    # production uses eps=0.25 which is fine with hundreds of signals)
    clusters = cluster_signals(signals, eps=0.80, min_samples=2)
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
    clusters = cluster_signals(signals, eps=0.80, min_samples=2)
    clusters = classify_clusters(clusters)
    for c in clusters:
        assert c.niche in {"commerce", "business", "tech_ai", "content", "general"}
        assert c.signal_type in {
            "rising_topic", "commercial_intent", "viral_content", "new_product", "search_surge"
        }
