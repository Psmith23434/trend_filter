"""Google Trends collector using pytrends."""
from pytrends.request import TrendReq
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal


class GoogleTrendsCollector(BaseCollector):
    source_name = "google_trends"

    def __init__(self, keywords: List[str] = None, timeframe: str = "now 7-d"):
        self.keywords = keywords or []
        self.timeframe = timeframe
        self.pytrends = TrendReq(hl="en-US", tz=360)

    def collect(self) -> List[RawSignal]:
        signals = []
        # Fetch trending searches if no keywords provided
        if not self.keywords:
            try:
                trending = self.pytrends.trending_searches(pn="united_states")
                self.keywords = trending[0].tolist()[:20]
            except Exception as e:
                print(f"[GoogleTrendsCollector] Error fetching trending: {e}")
                return signals

        batch = self.keywords[:5]  # pytrends max 5 per request
        try:
            self.pytrends.build_payload(batch, timeframe=self.timeframe)
            interest = self.pytrends.interest_over_time()
            for kw in batch:
                if kw in interest.columns:
                    score = int(interest[kw].iloc[-1])
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=f"gtrends_{kw}",
                        title=kw,
                        text=f"Google search interest score: {score}/100",
                        url=f"https://trends.google.com/trends/explore?q={kw}",
                        published_at=datetime.now(tz=timezone.utc),
                        engagement=score,
                        meta={"interest_score": score},
                    ))
        except Exception as e:
            print(f"[GoogleTrendsCollector] Error: {e}")
        return signals
