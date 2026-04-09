"""HackerNews collector — uses the public HN Firebase API."""
import httpx
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


class HackerNewsCollector(BaseCollector):
    source_name = "hackernews"

    def __init__(self, limit: int = 50):
        self.limit = limit

    def collect(self) -> List[RawSignal]:
        signals = []
        try:
            ids = httpx.get(HN_TOP_URL, timeout=10).json()[: self.limit]
            for item_id in ids:
                try:
                    item = httpx.get(HN_ITEM_URL.format(item_id), timeout=10).json()
                    if not item or item.get("type") != "story":
                        continue
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=str(item["id"]),
                        title=item.get("title", ""),
                        text=item.get("text", "")[:500],
                        url=item.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                        published_at=datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc),
                        engagement=item.get("score", 0) + item.get("descendants", 0),
                        meta={"comments": item.get("descendants", 0)},
                    ))
                except Exception as e:
                    print(f"[HN] Error on item {item_id}: {e}")
        except Exception as e:
            print(f"[HN] Error fetching top stories: {e}")
        return signals


def collect() -> List[RawSignal]:
    return HackerNewsCollector().collect()
