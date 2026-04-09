"""Normalize and deduplicate raw signals."""
from typing import List
from pipeline.models import RawSignal


def deduplicate(signals: List[RawSignal]) -> List[RawSignal]:
    """Remove duplicate signals by source + source_id."""
    seen = set()
    unique = []
    for s in signals:
        key = f"{s.source}:{s.source_id}"
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def clean_text(text: str) -> str:
    """Basic text cleanup."""
    return " ".join(text.split()).strip()


def normalize(signals: List[RawSignal]) -> List[RawSignal]:
    for s in signals:
        s.title = clean_text(s.title)
        s.text = clean_text(s.text)
    return deduplicate(signals)
