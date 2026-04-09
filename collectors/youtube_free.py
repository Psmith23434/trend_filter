"""YouTube collector — uses public RSS search feeds, no API key needed."""
import httpx
import feedparser
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

SEARCH_TERMS = [
    "side hustle 2025", "AI tools", "passive income ideas",
    "make money online", "solopreneur", "digital products",
]


class YouTubeFreeCollector(BaseCollector):
    source_name = "youtube"

    def __init__(self, terms: List[str] = None, limit: int = 10):
        self.terms = terms or SEARCH_TERMS
        self.limit = limit

    def collect(self) -> List[RawSignal]:
        signals = []
        for term in self.terms:
            try:
                url = f"https://www.youtube.com/feeds/videos.xml?q={term.replace(' ', '+')}"
                resp = httpx.get(url, timeout=10, follow_redirects=True)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[: self.limit]:
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=entry.get("yt_videoid", entry.get("id", "")),
                        title=entry.get("title", ""),
                        text=entry.get("summary", "")[:500],
                        url=entry.get("link", ""),
                        published_at=datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        if hasattr(entry, "published_parsed") and entry.published_parsed
                        else datetime.now(tz=timezone.utc),
                        engagement=0,
                        meta={"search_term": term},
                    ))
            except Exception as e:
                print(f"[YouTube] Error on '{term}': {e}")
        return signals


def collect() -> List[RawSignal]:
    return YouTubeFreeCollector().collect()
