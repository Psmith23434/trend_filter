"""Two-layer trend classification: niche + signal_type.

Niches (5):
  commerce   — sell products, Kindle, Etsy, POD, dropshipping
  business   — strategies, side hustles, SaaS, freelance models
  tech_ai    — software, AI tools, GitHub repos, dev tools
  content    — YouTube, podcasts, newsletters, creator economy
  general    — catch-all for cross-niche or ambiguous trends

Signal types:
  rising_topic      — topic gaining mentions across sources
  commercial_intent — strong buying/selling language present
  viral_content     — high engagement, spreading fast
  new_product       — a product/tool/launch detected
  search_surge      — search autocomplete / trends spike

Classification order:
  1. Source-based pre-label (instant, free)
  2. Keyword fingerprint override (fast, free)
  3. Embedding cosine similarity fallback (free, uses existing embeddings)
  4. LLM tie-break (only when top-2 niches are within 0.05 similarity)
"""

from __future__ import annotations
from typing import List, Optional
import numpy as np
from pipeline.models import TrendCluster, RawSignal

# ---------------------------------------------------------------------------
# 1. Source → niche map
# ---------------------------------------------------------------------------
SOURCE_NICHE_MAP: dict[str, str] = {
    "hackernews":       "tech_ai",
    "github_trending":  "tech_ai",
    "amazon_suggest":   "commerce",
    "etsy_suggest":     "commerce",
    "ebay_suggest":     "commerce",
    "openlibrary":      "commerce",
    "steamspy":         "tech_ai",
    "wikipedia":        "general",
    "google_trends":    "general",
    "youtube":          "content",
    "rss":              "general",
    "pinterest":        "commerce",
    "kickstarter":      "business",
    "bing_suggest":     "general",
    "ddg_suggest":      "general",
    "google_suggest":   "general",
    "google_play":      "tech_ai",
    "quora":            "general",
}

SUBREDDIT_NICHE_MAP: dict[str, str] = {
    "KindlePublishing":        "commerce",
    "selfpublishing":          "commerce",
    "Etsy":                    "commerce",
    "Flipping":                "commerce",
    "ecommerce":               "commerce",
    "printOnDemand":           "commerce",
    "dropship":                "commerce",
    "FulfillmentByAmazon":     "commerce",
    "SideProject":             "business",
    "entrepreneur":            "business",
    "passive_income":          "business",
    "startups":                "business",
    "smallbusiness":           "business",
    "freelance":               "business",
    "digitalnomad":            "business",
    "YoutubeCreators":         "content",
    "podcasting":              "content",
    "blogging":                "content",
    "NewTubers":               "content",
    "ChatGPT":                 "tech_ai",
    "ArtificialIntelligence":  "tech_ai",
    "MachineLearning":         "tech_ai",
    "LocalLLaMA":              "tech_ai",
    "programming":             "tech_ai",
    "webdev":                  "tech_ai",
    "gaming":                  "general",
    "technology":              "tech_ai",
}

# ---------------------------------------------------------------------------
# 2. Keyword fingerprints — ordered by specificity (first match wins)
# ---------------------------------------------------------------------------
NICHE_KEYWORDS: dict[str, List[str]] = {
    "commerce": [
        "kindle", "ebook", "book publish", "self-publish", "print on demand", "pod",
        "coloring book", "low content", "amazon fba", "dropship", "etsy", "ebay",
        "sell online", "resell", "product listing", "shopify", "merch", "printful",
        "redbubble", "teespring", "kdp", "kdp amazon",
    ],
    "business": [
        "side hustle", "passive income", "saas", "freelance", "agency", "consulting",
        "revenue model", "business model", "niche site", "affiliate", "solopreneur",
        "b2b", "b2c", "startup idea", "monetize", "income stream",
    ],
    "tech_ai": [
        "ai ", " ai", "llm", "chatgpt", "claude", "gemini", "openai", "prompt",
        "automation", "machine learning", "deep learning", "neural", "github",
        "open source", "developer", "api", "framework", "library", "python",
        "software", "app", "saas tool", "no-code", "low-code",
    ],
    "content": [
        "youtube", "channel", "views", "creator", "podcast", "newsletter",
        "substack", "blog", "tiktok", "instagram", "faceless", "video",
        "subscriber", "audience", "sponsor", "monetize channel",
    ],
}

SIGNAL_TYPE_KEYWORDS: dict[str, List[str]] = {
    "commercial_intent": [
        "buy", "best", "review", "price", "cheap", "deal", "discount",
        "product", "shop", "store", "sell", "purchase", "order", "cost",
    ],
    "new_product": [
        "launch", "new tool", "just released", "introducing", "announcing",
        "beta", "v1", "v2", "open source", "just shipped",
    ],
    "search_surge": [
        "google trends", "search interest", "autocomplete", "suggest", "trending search",
    ],
    "viral_content": [
        "viral", "exploding", "blowing up", "going viral", "millions of views",
    ],
}

# ---------------------------------------------------------------------------
# 3. Niche centroid phrases for embedding fallback
# ---------------------------------------------------------------------------
NICHE_CENTROID_PHRASES: dict[str, str] = {
    "commerce":  "sell products online etsy amazon kindle ebook print on demand dropshipping store",
    "business":  "side hustle passive income startup saas freelance agency revenue business model",
    "tech_ai":   "artificial intelligence LLM software developer open source github automation tool",
    "content":   "youtube channel creator podcast newsletter video subscribers audience blog",
    "general":   "news trending topic world events popular culture current events",
}

_centroid_embeddings: Optional[dict[str, np.ndarray]] = None


def _get_centroid_embeddings() -> dict[str, np.ndarray]:
    global _centroid_embeddings
    if _centroid_embeddings is None:
        from pipeline.embedder import get_model
        model = get_model()
        _centroid_embeddings = {
            niche: model.encode(phrase)
            for niche, phrase in NICHE_CENTROID_PHRASES.items()
        }
    return _centroid_embeddings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_niche(cluster: TrendCluster) -> str:
    """Return the best-fit niche for a cluster."""
    text = (cluster.representative_title + " " +
            " ".join(s.title for s in cluster.signals[:5])).lower()

    # Step 1 — source pre-label (majority vote across signals)
    source_votes: dict[str, int] = {}
    for signal in cluster.signals:
        niche = _niche_from_signal(signal)
        if niche:
            source_votes[niche] = source_votes.get(niche, 0) + 1
    source_niche = max(source_votes, key=source_votes.get) if source_votes else None

    # Step 2 — keyword override
    keyword_niche = _keyword_niche(text)

    # If both agree → confident
    if keyword_niche and source_niche and keyword_niche == source_niche:
        return keyword_niche

    # Keyword wins over source when present (more specific)
    if keyword_niche:
        return keyword_niche

    if source_niche and source_niche != "general":
        return source_niche

    # Step 3 — embedding fallback
    if cluster.signals and cluster.signals[0].embedding:
        embedding_niche = _embedding_niche(cluster)
        if embedding_niche:
            return embedding_niche

    return source_niche or "general"


def classify_signal_type(cluster: TrendCluster) -> str:
    """Classify what kind of trend signal this cluster represents."""
    text = (cluster.representative_title + " " +
            " ".join(s.title + " " + s.text for s in cluster.signals[:3])).lower()

    for stype, keywords in SIGNAL_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return stype

    # Fallback based on dominant source
    dominant = cluster.sources[0] if cluster.sources else ""
    if dominant in ("google_trends", "bing_suggest", "ddg_suggest",
                    "google_suggest", "amazon_suggest", "etsy_suggest"):
        return "search_surge"
    if dominant in ("youtube",):
        return "viral_content"
    if dominant in ("github_trending", "hackernews"):
        return "new_product"

    return "rising_topic"


def classify_clusters(clusters: List[TrendCluster]) -> List[TrendCluster]:
    """Assign niche + signal_type to every cluster in-place."""
    for c in clusters:
        c.niche = classify_niche(c)
        c.signal_type = classify_signal_type(c)
    return clusters


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _niche_from_signal(signal: RawSignal) -> Optional[str]:
    # Check subreddit first
    subreddit = signal.meta.get("subreddit", "")
    if subreddit and subreddit in SUBREDDIT_NICHE_MAP:
        return SUBREDDIT_NICHE_MAP[subreddit]
    return SOURCE_NICHE_MAP.get(signal.source)


def _keyword_niche(text: str) -> Optional[str]:
    for niche, keywords in NICHE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return niche
    return None


def _embedding_niche(cluster: TrendCluster) -> Optional[str]:
    centroids = _get_centroid_embeddings()
    # Average cluster embedding
    vectors = np.array([s.embedding for s in cluster.signals if s.embedding])
    if len(vectors) == 0:
        return None
    cluster_vec = vectors.mean(axis=0)
    cluster_vec = cluster_vec / np.linalg.norm(cluster_vec)

    scores: dict[str, float] = {}
    for niche, centroid in centroids.items():
        centroid_norm = centroid / np.linalg.norm(centroid)
        scores[niche] = float(np.dot(cluster_vec, centroid_norm))

    sorted_niches = sorted(scores, key=scores.get, reverse=True)
    top, second = sorted_niches[0], sorted_niches[1]

    # If top-2 are within 0.05 → ambiguous, return general
    if scores[top] - scores[second] < 0.05:
        return "general"
    return top
