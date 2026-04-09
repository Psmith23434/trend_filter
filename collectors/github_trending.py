"""GitHub Trending collector — scrapes the trending page."""
import httpx
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timezone
from collectors.base import BaseCollector
from pipeline.models import RawSignal

HEADERS = {"User-Agent": "Mozilla/5.0 (trend_filter/0.1; educational use)"}
TRENDING_URL = "https://github.com/trending"


class GitHubTrendingCollector(BaseCollector):
    source_name = "github_trending"

    def __init__(self, since: str = "daily"):
        self.since = since  # daily | weekly | monthly

    def collect(self) -> List[RawSignal]:
        signals = []
        try:
            resp = httpx.get(
                TRENDING_URL,
                params={"since": self.since},
                headers=HEADERS,
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for repo in soup.select("article.Box-row"):
                try:
                    name_tag = repo.select_one("h2 a")
                    if not name_tag:
                        continue
                    repo_path = name_tag["href"].strip("/")
                    desc_tag = repo.select_one("p")
                    desc = desc_tag.get_text(strip=True) if desc_tag else ""
                    stars_tag = repo.select_one("a[href$='/stargazers']")
                    stars = 0
                    if stars_tag:
                        stars_text = stars_tag.get_text(strip=True).replace(",", "")
                        try:
                            stars = int(stars_text)
                        except ValueError:
                            pass
                    signals.append(RawSignal(
                        source=self.source_name,
                        source_id=repo_path.replace("/", "_"),
                        title=repo_path,
                        text=desc[:500],
                        url=f"https://github.com/{repo_path}",
                        published_at=datetime.now(tz=timezone.utc),
                        engagement=stars,
                        meta={"since": self.since},
                    ))
                except Exception as e:
                    print(f"[GitHub] Error parsing repo: {e}")
        except Exception as e:
            print(f"[GitHub] Error fetching trending: {e}")
        return signals


def collect() -> List[RawSignal]:
    return GitHubTrendingCollector().collect()
