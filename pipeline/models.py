"""Shared data models used across the pipeline."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


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
    score: float = 0.0
    growth_score: float = 0.0
    diversity_score: float = 0.0
    commercial_score: float = 0.0
    novelty_score: float = 0.0
    persistence_score: float = 0.0
    brief: Optional[str] = None
    product_ideas: Optional[List[str]] = None
    urgency: Optional[str] = None  # low / medium / high
