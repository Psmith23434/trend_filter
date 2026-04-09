"""RSS/Atom feed collector."""
import feedparser
import httpx
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_FEEDS = [
    # Tech & AI
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.theverge.com/rss/index.xml",
    "https://hnrss.org/frontpage",
    # Business & Commerce
    "https://feeds.feedburner.com/entrepreneur/latest",
    "https://www.indiehackers.com/feed.rss",
    # Product Hunt
    "https://www.producthunt.com/feed",
    # Marketing
    "https://feeds.feedblitz.com/moz/YouMoz",
]


class RSSCollector(BaseCollector):
    source_name = "rss"

    def __init__(self, feed_urls: List[str] = None, limit_per_feed: int = 20):
        self.feed_urls = feed_urls or DEFAULT_FEEDS
        self.limit_per_feed = limit_per_feed

    def collect(self) -> List[RawSignal]:
        signals = []
        for url in self.feed_urls:
            try:
                resp = httpx.get(url, timeout=15, follow_redirects=True,
                                 headers={"User-Agent": "Mozilla/5.0 (trend_filter/0.1)"})
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[: self.limit_per_feed]:
                    pub = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        try:
                            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        except Exception:
                            pass
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=entry.get("id", entry.get("link", ""))[:100],
                        title=entry.get("title", ""),
                        text=(entry.get("summary") or "")[:500],
                        url=entry.get("link", ""),
                        published_at=pub or datetime.now(tz=timezone.utc),
                        engagement=0,
                        meta={"feed_url": url},
                    ))
            except Exception as e:
                print(f"[RSS] Error on {url}: {e}")
        return signals


def collect() -> List[RawSignal]:
    return RSSCollector().collect()
