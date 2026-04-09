"""Amazon autocomplete collector — uses the public suggestions endpoint."""
import httpx
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

SEED_TERMS = [
    "AI ", "home ", "fitness ", "pet ", "baby ",
    "garden ", "kitchen ", "office ", "travel ", "self ",
]

SUGGEST_URL = "https://completion.amazon.com/api/2017/suggestions"
HEADERS = {"User-Agent": "Mozilla/5.0 (trend_filter/0.1; educational use)"}


class AmazonSuggestCollector(BaseCollector):
    source_name = "amazon_suggest"

    def __init__(self, seeds: List[str] = None):
        self.seeds = seeds or SEED_TERMS

    def collect(self) -> List[RawSignal]:
        signals = []
        for seed in self.seeds:
            try:
                resp = httpx.get(
                    SUGGEST_URL,
                    params={"limit": 10, "prefix": seed, "mid": "ATVPDKIKX0DER", "alias": "aps"},
                    headers=HEADERS,
                    timeout=10,
                )
                resp.raise_for_status()
                suggestions = resp.json().get("suggestions", [])
                for sug in suggestions:
                    value = sug.get("value", "").strip()
                    if not value:
                        continue
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=f"amz_{value.replace(' ', '_')[:40]}",
                        title=value,
                        text=f"Amazon autocomplete suggestion for seed: '{seed}'",
                        url=f"https://www.amazon.com/s?k={value.replace(' ', '+')}",
                        published_at=datetime.now(tz=timezone.utc),
                        engagement=1,
                        meta={"seed": seed},
                    ))
            except Exception as e:
                print(f"[Amazon] Error on seed '{seed}': {e}")
        return signals


def collect() -> List[RawSignal]:
    return AmazonSuggestCollector().collect()
