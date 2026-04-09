"""Smoke tests: each collector must return a non-empty list of dicts with required keys."""
import pytest

REQUIRED_KEYS = {"title", "text", "url", "source", "engagement"}


def _check(signals):
    assert isinstance(signals, list), "Collector must return a list"
    assert len(signals) > 0, "Collector returned no signals"
    for sig in signals[:3]:  # spot-check first 3
        missing = REQUIRED_KEYS - sig.keys()
        assert not missing, f"Signal missing keys: {missing}\n{sig}"


def test_hackernews_collector():
    from collectors.hackernews import collect
    _check(collect())


def test_reddit_free_collector():
    from collectors.reddit_free import collect
    _check(collect())


def test_rss_collector():
    from collectors.rss import collect
    _check(collect())


def test_github_trending_collector():
    from collectors.github_trending import collect
    _check(collect())


def test_amazon_suggest_collector():
    from collectors.amazon_suggest import collect
    _check(collect())


def test_youtube_free_collector():
    from collectors.youtube_free import collect
    _check(collect())


@pytest.mark.skip(reason="pytrends is flaky; skip in CI — fix later")
def test_google_trends_collector():
    from collectors.google_trends import collect
    _check(collect())
