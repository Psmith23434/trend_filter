"""Smoke tests: each collector's .collect() must return a non-empty list of RawSignal objects."""
import pytest
from pipeline.models import RawSignal

REQUIRED_ATTRS = ["title", "text", "url", "source", "engagement"]


def _check(signals):
    assert isinstance(signals, list), "collect() must return a list"
    assert len(signals) > 0, "collect() returned no signals"
    for sig in signals[:3]:  # spot-check first 3
        assert isinstance(sig, RawSignal), f"Expected RawSignal, got {type(sig)}"
        for attr in REQUIRED_ATTRS:
            assert hasattr(sig, attr), f"RawSignal missing attribute: {attr}"


def test_hackernews_collector():
    from collectors.hackernews import HackerNewsCollector
    _check(HackerNewsCollector().collect())


def test_reddit_free_collector():
    from collectors.reddit_free import RedditFreeCollector
    _check(RedditFreeCollector().collect())


def test_rss_collector():
    from collectors.rss import RSSCollector
    _check(RSSCollector().collect())


def test_github_trending_collector():
    from collectors.github_trending import GitHubTrendingCollector
    _check(GitHubTrendingCollector().collect())


def test_amazon_suggest_collector():
    from collectors.amazon_suggest import AmazonSuggestCollector
    _check(AmazonSuggestCollector().collect())


def test_youtube_free_collector():
    from collectors.youtube_free import YouTubeFreeCollector
    _check(YouTubeFreeCollector().collect())


@pytest.mark.skip(reason="pytrends is flaky; skip in CI — fix later")
def test_google_trends_collector():
    from collectors.google_trends import GoogleTrendsCollector
    _check(GoogleTrendsCollector().collect())
