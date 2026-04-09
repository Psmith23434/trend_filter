"""Shared data models used across the pipeline."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

NICHES = ["commerce", "business", "tech_ai", "content", "general"]

NICHE_LABELS = {
    "commerce":  "🛒 Commerce",
    "business":  "💡 Business",
    "tech_ai":   "🤖 Tech & AI",
    "content":   "🎬 Content",
    "general":   "🌍 General",
}

SIGNAL_TYPES = [
    "rising_topic",
    "commercial_intent",
    "viral_content",
    "new_product",
    "search_surge",
]


@dataclass
class RawSignal:
    """A single raw signal from any source."""
    source: str
    source_id: str
    title: str
    text: str
    url: str
    published_at: datetime
    engagement: int
    meta: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class TrendCluster:
    """A group of similar signals representing one trend."""
    id: str
    signals: List[RawSignal]
    representative_title: str
    keywords: List[str]
    sources: List[str]
    # Scores
    score: float = 0.0
    growth_score: float = 0.0
    diversity_score: float = 0.0
    commercial_score: float = 0.0
    novelty_score: float = 0.0
    persistence_score: float = 0.0
    # Classification
    niche: str = "general"           # commerce | business | tech_ai | content | general
    signal_type: str = "rising_topic" # rising_topic | commercial_intent | viral_content | new_product | search_surge
    # LLM brief
    brief: Optional[str] = None
    product_ideas: Optional[List[str]] = None
    urgency: Optional[str] = None    # low | medium | high
