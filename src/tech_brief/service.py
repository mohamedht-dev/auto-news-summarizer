"""Persistent news generation service used by the web app and sync command."""

import os
from dataclasses import dataclass
from typing import List

from .articles import ArticleProcessor
from .config import DEFAULT_MODEL
from .database import Database
from .feeds import FeedFetcher
from .pipeline import BriefingPipeline
from .summarizers import create_summarizer


@dataclass
class SyncResult:
    run_id: int
    saved: int
    fetched: int
    unique: int
    skipped: int
    errors: List[str]


class SyncAlreadyRunningError(RuntimeError):
    """Raised when another process is already synchronizing the shared archive."""


class NewsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def sync(
        self,
        limit: int = 10,
        offline: bool = False,
        model: str = DEFAULT_MODEL,
    ) -> SyncResult:
        self.database.initialize()
        lock_name = "news-sync"
        if not self.database.acquire_lock(lock_name):
            raise SyncAlreadyRunningError("another news synchronization is already running")

        run_id = None
        try:
            sources = self.database.list_sources(enabled_only=True)
            run_id = self.database.start_run()
            pipeline = BriefingPipeline(
                FeedFetcher(sources),
                ArticleProcessor(),
                create_summarizer(offline=offline, model=model),
            )
            result = pipeline.run(limit=limit, skip_links=self.database.known_links())
            provider = "extractive" if offline or not os.getenv("OPENAI_API_KEY") else "openai"
            saved = 0
            for item in result.items:
                self.database.save_item(item, summarizer=provider)
                saved += 1
            if result.errors:
                status = "partial" if saved else "failed"
            else:
                status = "success"
            self.database.finish_run(
                run_id,
                status,
                result.fetched,
                result.unique,
                result.skipped,
                saved,
                result.errors,
            )
            self._update_source_health(sources, result.errors)
            return SyncResult(
                run_id=run_id,
                saved=saved,
                fetched=result.fetched,
                unique=result.unique,
                skipped=result.skipped,
                errors=result.errors,
            )
        except Exception as exc:
            if run_id is not None:
                self.database.finish_run(run_id, "failed", 0, 0, 0, 0, [str(exc)])
            raise
        finally:
            self.database.release_lock(lock_name)

    def _update_source_health(self, sources, errors: List[str]) -> None:
        for source in sources:
            prefix = f"{source['name']}:"
            error = next((value for value in errors if value.startswith(prefix)), None)
            self.database.update_source_result(int(source["id"]), error)
