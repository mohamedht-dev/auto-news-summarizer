from tech_brief.models import Article, BriefingItem
from tech_brief.pipeline import BriefingPipeline


class FakeFetcher:
    errors = ["one source was unavailable"]

    @staticmethod
    def fetch_all():
        return [
            Article(title="One", link="https://example.com/1", source="Example"),
            Article(title="Two", link="https://example.com/2", source="Example"),
        ]


class FakeProcessor:
    @staticmethod
    def deduplicate(articles):
        return articles

    @staticmethod
    def extract_full_content(article):
        return article


class FakeSummarizer:
    @staticmethod
    def summarize(article):
        if article.title == "Two":
            raise RuntimeError("summary failed")
        return BriefingItem(
            headline_ar="واحد",
            summary_ar="ملخص",
            summary_en="Summary",
            key_points=["نقطة"],
            why_it_matters="مهم",
            companies=[],
            technologies=[],
            confidence=0.8,
            source_url=article.link,
        )


def test_pipeline_keeps_successful_items_and_reports_individual_failures():
    result = BriefingPipeline(FakeFetcher(), FakeProcessor(), FakeSummarizer()).run(limit=2)

    assert len(result.items) == 1
    assert result.fetched == 2
    assert result.unique == 2
    assert result.errors == ["one source was unavailable", "Two: summary failed"]


def test_pipeline_skips_links_already_saved():
    result = BriefingPipeline(FakeFetcher(), FakeProcessor(), FakeSummarizer()).run(
        limit=2,
        skip_links={"https://example.com/1"},
    )

    assert result.items == []
    assert result.skipped == 1
    assert result.errors == ["one source was unavailable", "Two: summary failed"]
