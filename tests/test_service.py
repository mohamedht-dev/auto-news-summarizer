import pytest

from tech_brief.database import Database
from tech_brief.models import BriefingItem
from tech_brief.pipeline import PipelineResult
from tech_brief.service import NewsService, SyncAlreadyRunningError


def generated_item():
    return BriefingItem(
        original_title="AI release",
        headline_ar="إطلاق جديد",
        summary_ar="ملخص عربي.",
        summary_en="English summary.",
        key_points=["نقطة"],
        why_it_matters="مهم للمطورين.",
        companies=["OpenAI"],
        technologies=["AI"],
        confidence=0.9,
        source_url="https://example.com/release",
        source_name="OpenAI",
        published="2026-08-02",
        category="artificial-intelligence",
    )


def test_service_persists_pipeline_result_and_releases_lock(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "service.db"))
    monkeypatch.setattr("tech_brief.service.create_summarizer", lambda **kwargs: object())
    monkeypatch.setattr(
        "tech_brief.service.BriefingPipeline.run",
        lambda self, limit, skip_links: PipelineResult(
            items=[generated_item()], fetched=4, unique=3, skipped=1
        ),
    )

    result = NewsService(database).sync(limit=5, offline=True)

    assert result.saved == 1
    assert database.stats()["articles"] == 1
    assert database.list_runs()[0]["status"] == "success"
    assert database.acquire_lock("news-sync") is True


def test_service_rejects_concurrent_sync(tmp_path):
    database = Database(str(tmp_path / "service.db"))
    database.initialize()
    assert database.acquire_lock("news-sync") is True

    with pytest.raises(SyncAlreadyRunningError):
        NewsService(database).sync(offline=True)


def test_service_records_failed_pipeline_and_releases_lock(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "service.db"))
    monkeypatch.setattr("tech_brief.service.create_summarizer", lambda **kwargs: object())

    def fail_run(self, limit, skip_links):
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr("tech_brief.service.BriefingPipeline.run", fail_run)

    with pytest.raises(RuntimeError, match="pipeline failed"):
        NewsService(database).sync(offline=True)

    run = database.list_runs()[0]
    assert run["status"] == "failed"
    assert run["errors"] == ["pipeline failed"]
    assert database.acquire_lock("news-sync") is True
