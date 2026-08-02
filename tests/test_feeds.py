from types import SimpleNamespace

from tech_brief.feeds import FeedFetcher


def test_fetch_all_normalizes_rss_entries(monkeypatch):
    feed = SimpleNamespace(
        status=200,
        entries=[
            {
                "title": "New model",
                "link": "https://example.com/model",
                "summary": "Details",
                "published": "2026-08-02",
            }
        ],
    )
    monkeypatch.setattr("tech_brief.feeds.feedparser.parse", lambda _: feed)

    fetcher = FeedFetcher(
        [{"name": "Example", "url": "https://example.com/rss", "category": "ai"}]
    )
    articles = fetcher.fetch_all()

    assert len(articles) == 1
    assert articles[0].source == "Example"
    assert articles[0].category == "ai"
    assert fetcher.errors == []


def test_fetch_all_records_source_errors(monkeypatch):
    monkeypatch.setattr(
        "tech_brief.feeds.feedparser.parse",
        lambda _: SimpleNamespace(status=503, entries=[]),
    )
    fetcher = FeedFetcher([{"name": "Broken", "url": "https://example.com/rss"}])

    assert fetcher.fetch_all() == []
    assert "HTTP 503" in fetcher.errors[0]
