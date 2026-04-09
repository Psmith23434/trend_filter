"""Reddit collector — monitors configurable subreddits for rising posts."""
import os
import praw
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_SUBREDDITS = [
    "entrepreneur", "SideProject", "startups", "Etsy", "KindlePublishing",
    "digitalnomad", "passive_income", "Flipping", "ecommerce", "ChatGPT"
]


class RedditCollector(BaseCollector):
    source_name = "reddit"

    def __init__(self, subreddits: List[str] = None, limit: int = 50):
        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.limit = limit
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT", "trend_filter/0.1"),
        )

    def collect(self) -> List[RawSignal]:
        signals = []
        for sub in self.subreddits:
            try:
                subreddit = self.reddit.subreddit(sub)
                for post in subreddit.rising(limit=self.limit):
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=post.id,
                        title=post.title,
                        text=post.selftext[:500] if post.selftext else "",
                        url=f"https://reddit.com{post.permalink}",
                        published_at=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                        engagement=post.score + post.num_comments,
                        meta={"subreddit": sub, "upvote_ratio": post.upvote_ratio},
                    ))
            except Exception as e:
                print(f"[RedditCollector] Error on r/{sub}: {e}")
        return signals
