"""Reddit collector — uses public .json endpoints, no API key or PRAW needed."""
import httpx
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_SUBREDDITS = [
    "entrepreneur", "SideProject", "startups", "Etsy", "KindlePublishing",
    "digitalnomad", "passive_income", "Flipping", "ecommerce", "ChatGPT",
    "ArtificialIntelligence", "Notion", "productivity", "YoutubeCreators", "selfpublishing"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (trend_filter/0.1; educational use)"}


class RedditFreeCollector(BaseCollector):
    source_name = "reddit"

    def __init__(self, subreddits: List[str] = None, feed: str = "rising", limit: int = 25):
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.feed = feed   # rising | hot | new
        self.limit = limit

    def collect(self) -> List[RawSignal]:
        signals = []
        for sub in self.subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/{self.feed}.json?limit={self.limit}"
                resp = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
                resp.raise_for_status()
                posts = resp.json()["data"]["children"]
                for post in posts:
                    d = post["data"]
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=d["id"],
                        title=d["title"],
                        text=(d.get("selftext") or "")[:500],
                        url=f"https://reddit.com{d['permalink']}",
                        published_at=datetime.fromtimestamp(d["created_utc"], tz=timezone.utc),
                        engagement=d["score"] + d["num_comments"],
                        meta={"subreddit": sub, "upvote_ratio": d.get("upvote_ratio", 0)},
                    ))
            except Exception as e:
                print(f"[RedditFree] Error on r/{sub}: {e}")
        return signals
