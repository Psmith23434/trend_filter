"""Amazon search suggestion scraper — no API key needed."""
import httpx
import json
from typing import List
from datetime import datetime, timezone
from urllib.parse import quote_plus
from collectors.base import BaseCollector
from pipeline.models import RawSignal

SEED_KEYWORDS = [
    "how to make", "best tool for", "ai ", "passive income",
    "print on demand", "digital planner", "prompt", "notion template",
    "kindle", "journal", "coloring book", "low content",
]

SUGGEST_URL = "https://completion.amazon.com/api/2017/suggestions?session-id=trend_filter&customer-id=0&request-id=0&page-type=Search&lop=en_US&site-variant=desktop&client-info=amazon-search-ui&mid=ATVPDKIKX0DER&alias=aps&b2b=0&fresh=0&ks=80&prefix={query}&event=onKeyPress&limit=11&fb=1"


class AmazonSuggestCollector(BaseCollector):
    source_name = "amazon_suggest"

    def __init__(self, seeds: List[str] = None):
        self.seeds = seeds or SEED_KEYWORDS

    def collect(self) -> List[RawSignal]:
        signals = []
        headers = {"User-Agent": "Mozilla/5.0 (trend_filter/0.1)"}
        for seed in self.seeds:
            try:
                url = SUGGEST_URL.format(query=quote_plus(seed))
                resp = httpx.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                suggestions = data.get("suggestions", [])
                for s in suggestions:
                    value = s.get("value", "")
                    if not value or value == seed:
                        continue
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=f"amz_{quote_plus(value)}",
                        title=value,
                        text=f"Amazon autocomplete suggestion for seed: '{seed}'",
                        url=f"https://www.amazon.com/s?k={quote_plus(value)}",
                        published_at=datetime.now(tz=timezone.utc),
                        engagement=0,
                        meta={"seed": seed},
                    ))
            except Exception as e:
                print(f"[AmazonSuggest] Error on seed '{seed}': {e}")
        return signals
