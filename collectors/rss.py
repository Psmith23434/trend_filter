"""Generic RSS/Atom feed collector."""
import feedparser
from typing import List
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from collectors.base import BaseCollector
from pipeline.models import RawSignal

DEFAULT_FEEDS = [

    # -------------------------------------------------------------------------
    # TECH / AI  (25 feeds)
    # -------------------------------------------------------------------------
    "https://feeds.feedburner.com/TechCrunch",
    "https://techcrunch.com/startups/feed",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.engadget.com/rss.xml",
    "https://venturebeat.com/feed",
    "https://www.zdnet.com/news/rss.xml",
    "https://www.techradar.com/rss",
    "https://openai.com/news/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://blog.google/technology/ai/rss/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://www.marktechpost.com/feed/",
    "https://rss.arxiv.org/rss/cs.AI",
    "https://www.therundown.ai/feed",
    "https://tldr.tech/api/rss/ai",
    "https://aiweekly.co/rss",
    "https://importai.substack.com/feed",
    "https://bensbites.beehiiv.com/feed",
    "https://www.deeplearning.ai/the-batch/feed/",
    "https://www.theaireport.ai/feed",
    "https://www.fast.ai/atom.xml",
    "https://lastweek.io/feed.xml",
    "https://thesequence.substack.com/feed",
    "https://www.semianalysis.com/feed",

    # -------------------------------------------------------------------------
    # PRODUCT LAUNCHES & STARTUPS  (12 feeds)
    # -------------------------------------------------------------------------
    "https://www.producthunt.com/feed",
    "https://hnrss.org/frontpage",
    "https://hnrss.org/newest?points=100",
    "https://www.starterstory.com/feed",
    "https://www.failory.com/feed",
    "https://www.thebootstrappedfounder.com/feed",
    "https://www.indiehackers.com/feed.rss",
    "https://www.saastr.com/feed/",
    "https://bothsidesofthetable.com/feed",
    "https://a16z.com/feed/",
    "https://www.ycombinator.com/blog/rss",
    "https://pitchbook.com/news/rss",

    # -------------------------------------------------------------------------
    # COMMERCE / AMAZON / ETSY / EBAY / MARKETPLACES  (14 feeds)
    # -------------------------------------------------------------------------
    "https://mywifequitherjob.com/feed/",
    "https://www.junglescout.com/blog/feed/",
    "https://news.etsy.com/feed/",
    "https://www.practicalecommerce.com/feed",
    "https://www.ecommercefuel.com/feed/",
    "https://www.webretailer.com/feed/",
    "https://www.shopify.com/blog/rss",
    "https://www.bigcommerce.com/blog/feed/",
    "https://www.2ndoffice.co/feed",
    "https://feedpress.me/sellerapp-blog",
    "https://www.repricerexpress.com/blog/feed/",
    "https://www.sellersnap.io/blog/feed/",
    "https://www.merchantwords.com/blog/feed/",
    "https://www.feedvisor.com/resources/feed/",

    # -------------------------------------------------------------------------
    # PRINT ON DEMAND / MERCH  (6 feeds)
    # -------------------------------------------------------------------------
    "https://www.printful.com/blog/feed/",
    "https://printify.com/blog/feed/",
    "https://www.redbubble.com/blog/feed/",
    "https://www.teepublic.com/blog/feed",
    "https://www.merchwizard.com/blog/feed",
    "https://podinsights.blog/feed/",

    # -------------------------------------------------------------------------
    # SIDE HUSTLES / PASSIVE INCOME / SOLOPRENEUR  (10 feeds)
    # -------------------------------------------------------------------------
    "https://www.sidehustlenation.com/feed/",
    "https://www.smartpassiveincome.com/feed/",
    "https://www.inc.com/rss",
    "https://www.entrepreneur.com/latest.rss",
    "https://www.founderpath.com/feed",
    "https://www.nichepursuits.com/feed/",
    "https://incomeschool.com/feed/",
    "https://www.moneylab.co/feed",
    "https://www.onlinedimes.com/feed/",
    "https://www.dollarsprout.com/feed/",

    # -------------------------------------------------------------------------
    # CONTENT CREATORS / YOUTUBE / SOCIAL MEDIA  (10 feeds)
    # -------------------------------------------------------------------------
    "https://creatoreconomy.so/feed",
    "https://www.tubefilter.com/feed/",
    "https://www.vidiq.com/blog/feed/",
    "https://www.socialmediaexaminer.com/feed/",
    "https://blog.buffer.com/rss/",
    "https://sproutsocial.com/insights/feed/",
    "https://www.later.com/blog/feed/",
    "https://www.hootsuite.com/resources/feed",
    "https://www.podcastinsights.com/feed/",
    "https://castos.com/blog/feed/",

    # -------------------------------------------------------------------------
    # DIGITAL PRODUCTS / KDP / COURSES / TEMPLATES  (7 feeds)
    # -------------------------------------------------------------------------
    "https://selfpublishingadvice.org/feed/",
    "https://thecreatorseries.substack.com/feed",
    "https://www.thinkific.com/blog/feed/",
    "https://www.teachable.com/blog/feed",
    "https://www.podia.com/articles/feed",
    "https://convertkit.com/newsletter/feed",
    "https://www.publishingperspectives.com/feed/",

    # -------------------------------------------------------------------------
    # SEO / SEARCH / KEYWORD TRENDS  (8 feeds)
    # -------------------------------------------------------------------------
    "https://www.semrush.com/blog/feed/",
    "https://ahrefs.com/blog/rss/",
    "https://moz.com/blog/feed",
    "https://searchengineland.com/feed",
    "https://searchenginejournal.com/feed",
    "https://www.searchenginewatch.com/feed/",
    "https://neilpatel.com/blog/feed/",
    "https://backlinko.com/blog/rss",

    # -------------------------------------------------------------------------
    # TRENDING / GENERAL NEWS  (35 feeds)
    # -------------------------------------------------------------------------
    # Google Trends RSS (official, multiple geos)
    "https://trends.google.com/trending/rss?geo=US",
    "https://trends.google.com/trending/rss?geo=GB",
    "https://trends.google.com/trending/rss?geo=DE",
    "https://trends.google.com/trending/rss?geo=AU",
    "https://trends.google.com/trending/rss?geo=CA",
    # Major wire services
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/technologyNews",
    "https://www.apnews.com/rss",
    "https://feeds.skynews.com/feeds/rss/world.xml",
    "https://feeds.skynews.com/feeds/rss/business.xml",
    # US news & business
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Upshot.xml",
    "https://www.fastcompany.com/rss",
    "https://www.forbes.com/innovation/feed2",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://feeds.finance.yahoo.com/rss/2.0/headline",
    # Pop culture / viral / lifestyle
    "https://mashable.com/feeds/rss/all",
    "https://www.buzzfeed.com/index.xml",
    "https://lifehacker.com/rss",
    "https://gizmodo.com/rss",
    "https://www.vice.com/en/rss",
    "https://bbc.com/culture/feed.rss",
    "https://www.rollingstone.com/feed/",
    # Business / economy signals
    "https://hbr.org/feed",
    "https://www.businessinsider.com/rss",
    "https://qz.com/rss",
    "https://www.economist.com/finance-and-economics/rss.xml",
    # Emerging / niche trend sites
    "https://explodingtopics.com/blog/feed",
    "https://marketingagent.blog/feed",
    "https://www.springwise.com/feed/",
    "https://trendwatching.com/feed/",

    # -------------------------------------------------------------------------
    # CRYPTO / WEB3 / FINTECH  (6 feeds)
    # -------------------------------------------------------------------------
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://techcrunch.com/category/fintech/feed",
    "https://fintechmagazine.com/rss",
    "https://www.pymnts.com/feed/",

    # -------------------------------------------------------------------------
    # REDDIT public RSS  (15 feeds)
    # -------------------------------------------------------------------------
    "https://www.reddit.com/r/entrepreneur/.rss",
    "https://www.reddit.com/r/SideProject/.rss",
    "https://www.reddit.com/r/passive_income/.rss",
    "https://www.reddit.com/r/smallbusiness/.rss",
    "https://www.reddit.com/r/business/.rss",
    "https://www.reddit.com/r/trends/.rss",
    "https://www.reddit.com/r/Flipping/.rss",
    "https://www.reddit.com/r/ecommerce/.rss",
    "https://www.reddit.com/r/FulfillmentByAmazon/.rss",
    "https://www.reddit.com/r/etsy/.rss",
    "https://www.reddit.com/r/printOnDemand/.rss",
    "https://www.reddit.com/r/juststart/.rss",
    "https://www.reddit.com/r/affiliatemarketing/.rss",
    "https://www.reddit.com/r/digital_marketing/.rss",
    "https://www.reddit.com/r/artificial/.rss",
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
