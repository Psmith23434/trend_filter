"""Generic RSS/Atom feed collector."""
import feedparser
from typing import List
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_FEEDS = [

    # -------------------------------------------------------------------------
    # TECH / AI
    # -------------------------------------------------------------------------
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.theverge.com/rss/index.xml",
    "https://openai.com/blog/rss/",
    "https://huggingface.co/blog/feed.xml",
    "https://www.therundown.ai/feed",
    "https://tldr.tech/api/rss/ai",
    "https://aiweekly.co/rss",
    "https://importai.substack.com/feed",
    "https://bensbites.beehiiv.com/feed",
    "https://www.deeplearning.ai/the-batch/feed/",
    "https://www.wired.com/feed/rss",

    # -------------------------------------------------------------------------
    # PRODUCT LAUNCHES & STARTUPS
    # -------------------------------------------------------------------------
    "https://www.producthunt.com/feed",
    "https://hnrss.org/frontpage",
    "https://www.starterstory.com/feed",
    "https://www.failory.com/feed",
    "https://www.thebootstrappedfounder.com/feed",
    "https://www.indiehackers.com/feed.rss",

    # -------------------------------------------------------------------------
    # COMMERCE / AMAZON / ETSY / POD
    # -------------------------------------------------------------------------
    "https://mywifequitherjob.com/feed/",
    "https://www.junglescout.com/blog/feed/",
    "https://news.etsy.com/feed/",
    "https://www.practicalecommerce.com/feed",
    "https://www.ecommercefuel.com/feed/",
    "https://www.webretailer.com/feed/",
    "https://www.printful.com/blog/feed/",
    "https://www.shopify.com/blog/rss",

    # -------------------------------------------------------------------------
    # SIDE HUSTLES / PASSIVE INCOME / BUSINESS
    # -------------------------------------------------------------------------
    "https://www.sidehustlenation.com/feed/",
    "https://www.smartpassiveincome.com/feed/",
    "https://www.inc.com/rss",
    "https://feeds.feedburner.com/entrepreneur/latest",
    "https://www.founderpath.com/feed",

    # -------------------------------------------------------------------------
    # CONTENT CREATORS / YOUTUBE / SOCIAL
    # -------------------------------------------------------------------------
    "https://creatoreconomy.so/feed",
    "https://www.tubefilter.com/feed/",
    "https://www.vidiq.com/blog/feed/",
    "https://www.socialmediaexaminer.com/feed/",
    "https://blog.buffer.com/rss/",

    # -------------------------------------------------------------------------
    # SEO / SEARCH TRENDS
    # -------------------------------------------------------------------------
    "https://www.semrush.com/blog/feed/",
    "https://ahrefs.com/blog/rss/",
    "https://moz.com/blog/feed",

    # -------------------------------------------------------------------------
    # TRENDING / GENERAL
    # -------------------------------------------------------------------------
    "https://trends.google.com/trending/rss?geo=US",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://mashable.com/feeds/rss/all",

    # -------------------------------------------------------------------------
    # REDDIT (public RSS — cross-confirms reddit_free collector signals)
    # -------------------------------------------------------------------------
    "https://www.reddit.com/r/entrepreneur/.rss",
    "https://www.reddit.com/r/SideProject/.rss",
    "https://www.reddit.com/r/passive_income/.rss",
    "https://www.reddit.com/r/smallbusiness/.rss",
    "https://www.reddit.com/r/business/.rss",
    "https://www.reddit.com/r/trends/.rss",
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
