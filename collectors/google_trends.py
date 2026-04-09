"""Google Trends collector — uses pytrends (no API key required)."""
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal


class GoogleTrendsCollector(BaseCollector):
    source_name = "google_trends"

    def __init__(self, keywords: List[str] = None, geo: str = "US"):
        self.keywords = keywords or [
            "side hustle", "AI tools", "passive income", "print on demand",
            "dropshipping", "content creator", "no code", "solopreneur",
        ]
        self.geo = geo

    def collect(self) -> List[RawSignal]:
        signals = []
        try:
            from pytrends.request import TrendReq
            pt = TrendReq(hl="en-US", tz=0)
            for kw in self.keywords:
                try:
                    pt.build_payload([kw], timeframe="now 7-d", geo=self.geo)
                    data = pt.interest_over_time()
                    if data.empty:
                        continue
                    latest = int(data[kw].iloc[-1])
                    avg = float(data[kw].mean())
                    growth = (latest - avg) / max(avg, 1)
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=f"gt_{kw.replace(' ', '_')}",
                        title=kw,
                        text=f"Google Trends interest: {latest}/100 (7-day avg {avg:.0f})",
                        url=f"https://trends.google.com/trends/explore?q={kw.replace(' ', '+')}",
                        published_at=datetime.now(tz=timezone.utc),
                        engagement=latest,
                        meta={"growth": growth, "avg": avg},
                    ))
                except Exception as e:
                    print(f"[GoogleTrends] Error on '{kw}': {e}")
        except ImportError:
            print("[GoogleTrends] pytrends not installed, skipping.")
        return signals


def collect() -> List[RawSignal]:
    return GoogleTrendsCollector().collect()
