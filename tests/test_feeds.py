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


def test_fetch_all_interleaves_sources_for_a_balanced_brief(monkeypatch):
    def parse(url):
        name = "Alpha" if "alpha" in url else "Beta"
        return SimpleNamespace(
            status=200,
            entries=[
                {"title": f"{name} {number}", "link": f"https://{name}.test/{number}"}
                for number in range(2)
            ],
        )

    monkeypatch.setattr("tech_brief.feeds.feedparser.parse", parse)
    fetcher = FeedFetcher(
        [
            {"name": "Alpha", "url": "https://alpha.test/rss", "category": "ai"},
            {"name": "Beta", "url": "https://beta.test/rss", "category": "tech"},
        ]
    )

    assert [article.source for article in fetcher.fetch_all()] == [
        "Alpha",
        "Beta",
        "Alpha",
        "Beta",
    ]
