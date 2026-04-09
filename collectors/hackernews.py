"""Hacker News collector — fetches top and new stories."""
import httpx
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

HN_API = "https://hacker-news.firebaseio.com/v0"


class HackerNewsCollector(BaseCollector):
    source_name = "hackernews"

    def __init__(self, feed: str = "topstories", limit: int = 30):
        self.feed = feed  # topstories | newstories | beststories
        self.limit = limit

    def collect(self) -> List[RawSignal]:
        signals = []
        try:
            ids = httpx.get(f"{HN_API}/{self.feed}.json").json()[:self.limit]
            for item_id in ids:
                item = httpx.get(f"{HN_API}/item/{item_id}.json").json()
                if not item or item.get("type") != "story":
                    continue
                signals.append(RawSignal(
                    source=self.source_name,
                    source_id=str(item_id),
                    title=item.get("title", ""),
                    text=item.get("text", "")[:500],
                    url=item.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                    published_at=datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc),
                    engagement=item.get("score", 0) + item.get("descendants", 0),
                    meta={"hn_score": item.get("score", 0), "comments": item.get("descendants", 0)},
                ))
        except Exception as e:
            print(f"[HackerNewsCollector] Error: {e}")
        return signals
