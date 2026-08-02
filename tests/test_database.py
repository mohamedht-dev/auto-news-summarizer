from tech_brief.database import Database
from tech_brief.models import BriefingItem


def briefing_item(link="https://example.com/news/1"):
    return BriefingItem(
        original_title="A useful AI launch",
        headline_ar="إطلاق مفيد في الذكاء الاصطناعي",
        summary_ar="ملخص عربي واضح للخبر.",
        summary_en="A clear English summary.",
        key_points=["النقطة الأولى", "النقطة الثانية"],
        why_it_matters="لأنه يحسن أدوات المطورين.",
        companies=["OpenAI"],
        technologies=["AI"],
        confidence=0.91,
        source_url=link,
        source_name="OpenAI",
        published="2026-08-02T08:00:00+00:00",
        category="artificial-intelligence",
    )


def test_database_persists_and_searches_articles(tmp_path):
    database = Database(str(tmp_path / "brief.db"))
    database.initialize()

    article_id = database.save_item(briefing_item(), summarizer="extractive")
    articles, total = database.list_articles(query="الذكاء")
    article = database.get_article(article_id)

    assert total == 1
    assert articles[0]["id"] == article_id
    assert article["companies"] == ["OpenAI"]
    assert article["key_points"] == ["النقطة الأولى", "النقطة الثانية"]
    assert article["reading_minutes"] == 1
    assert database.known_links() == {"https://example.com/news/1"}
    assert database.categories() == ["artificial-intelligence"]
    assert database.stats() == {"articles": 1, "sources": 2, "categories": 1}
    assert database.top_topics() == [
        {"name": "OpenAI", "count": 1},
        {"name": "AI", "count": 1},
    ]


def test_database_manages_sources_and_runs(tmp_path):
    database = Database(str(tmp_path / "brief.db"))
    database.initialize()
    source_id = database.add_source(
        "Example", "https://example.com/feed.xml", "cybersecurity"
    )

    database.toggle_source(source_id)
    source = next(item for item in database.list_sources() if item["id"] == source_id)
    assert source["enabled"] == 0

    run_id = database.start_run()
    database.finish_run(run_id, "success", 4, 3, 1, 2, ["one warning"])
    run = database.list_runs()[0]
    assert run["status"] == "success"
    assert run["errors"] == ["one warning"]

    database.delete_source(source_id)
    assert all(item["id"] != source_id for item in database.list_sources())


def test_database_upserts_existing_link(tmp_path):
    database = Database(str(tmp_path / "brief.db"))
    database.initialize()
    first_id = database.save_item(briefing_item(), summarizer="extractive")
    changed = briefing_item()
    changed.headline_ar = "عنوان محدث"

    second_id = database.save_item(changed, summarizer="openai")

    assert second_id == first_id
    assert database.get_article(first_id)["headline_ar"] == "عنوان محدث"


def test_database_uses_sources_when_articles_have_no_entity_topics(tmp_path):
    database = Database(str(tmp_path / "brief.db"))
    database.initialize()
    item = briefing_item()
    item.companies = []
    item.technologies = []
    database.save_item(item, summarizer="extractive")

    assert database.top_topics() == [{"name": "OpenAI", "count": 1}]


def test_database_lock_prevents_concurrent_syncs(tmp_path):
    database = Database(str(tmp_path / "brief.db"))
    database.initialize()

    assert database.acquire_lock("news-sync") is True
    assert database.acquire_lock("news-sync") is False

    database.release_lock("news-sync")
    assert database.acquire_lock("news-sync") is True
