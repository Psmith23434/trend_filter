"""GitHub Trending scraper — no API key needed."""
import httpx
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

TRENDING_URL = "https://github.com/trending"
HEADERS = {"User-Agent": "Mozilla/5.0 (trend_filter/0.1)"}


class GitHubTrendingCollector(BaseCollector):
    source_name = "github_trending"

    def __init__(self, language: str = "", since: str = "daily"):
        self.language = language
        self.since = since  # daily | weekly | monthly

    def collect(self) -> List[RawSignal]:
        signals = []
        try:
            params = {"since": self.since}
            if self.language:
                params["l"] = self.language
            resp = httpx.get(TRENDING_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            repos = soup.select("article.Box-row")
            for repo in repos:
                name_tag = repo.select_one("h2 a")
                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True).replace("\n", "").replace(" ", "")
                desc_tag = repo.select_one("p")
                desc = desc_tag.get_text(strip=True) if desc_tag else ""
                stars_tag = repo.select_one("a[href$='/stargazers']")
                stars = 0
                if stars_tag:
                    try:
                        stars = int(stars_tag.get_text(strip=True).replace(",", ""))
                    except ValueError:
                        pass
                signals.append(RawSignal(
                    source=self.source_name,
                    source_id=name,
                    title=name,
                    text=desc,
                    url=f"https://github.com/{name.strip()}",
                    published_at=datetime.now(tz=timezone.utc),
                    engagement=stars,
                    meta={"since": self.since, "language": self.language},
                ))
        except Exception as e:
            print(f"[GitHubTrending] Error: {e}")
        return signals
