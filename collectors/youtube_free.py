"""YouTube collector — scrapes search suggestions and trending RSS, no API key needed."""
import httpx
import feedparser
from typing import List
from datetime import datetime, timezone
from urllib.parse import quote_plus
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_QUERIES = [
    "how to make money online 2026", "AI tools", "side hustle",
    "passive income", "print on demand", "kindle publishing",
    "digital products", "dropshipping", "faceless youtube channel",
]

YT_SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={query}"
YT_RSS = "https://www.youtube.com/feeds/videos.xml?search_query={query}"


class YouTubeFreeCollector(BaseCollector):
    source_name = "youtube"

    def __init__(self, queries: List[str] = None):
        self.queries = queries or DEFAULT_QUERIES

    def collect(self) -> List[RawSignal]:
        signals = []
        for query in self.queries:
            signals.extend(self._rss_signals(query))
        return signals

    def _rss_signals(self, query: str) -> List[RawSignal]:
        """Use YouTube's public RSS search feed."""
        signals = []
        try:
            url = YT_RSS.format(query=quote_plus(query))
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                published = datetime.now(tz=timezone.utc)
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
                signals.append(RawSignal(
                    source=self.source_name,
                    source_id=entry.get("yt_videoid", entry.get("id", "")),
                    title=entry.get("title", ""),
                    text=entry.get("summary", "")[:500],
                    url=entry.get("link", ""),
                    published_at=published,
                    engagement=0,
                    meta={"query": query, "author": entry.get("author", "")},
                ))
        except Exception as e:
            print(f"[YouTubeFree] Error on query '{query}': {e}")
        return signals
