"""Generic RSS/Atom feed collector."""
import feedparser
from typing import List
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_FEEDS = [
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.producthunt.com/feed",
    "https://hnrss.org/frontpage",
    "https://www.theverge.com/rss/index.xml",
]


class RSSCollector(BaseCollector):
    source_name = "rss"

    def __init__(self, feed_urls: List[str] = None):
        self.feed_urls = feed_urls or DEFAULT_FEEDS

    def collect(self) -> List[RawSignal]:
        signals = []
        for url in self.feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:20]:
                    try:
                        published = parsedate_to_datetime(entry.get("published", ""))
                    except Exception:
                        published = datetime.now(tz=timezone.utc)
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=entry.get("id", entry.get("link", "")),
                        title=entry.get("title", ""),
                        text=entry.get("summary", "")[:500],
                        url=entry.get("link", ""),
                        published_at=published,
                        engagement=0,
                        meta={"feed_url": url},
                    ))
            except Exception as e:
                print(f"[RSSCollector] Error on {url}: {e}")
        return signals
