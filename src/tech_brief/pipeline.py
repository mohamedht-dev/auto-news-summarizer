"""Orchestration for collecting and summarizing articles."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from .articles import ArticleProcessor
from .feeds import FeedFetcher
from .models import BriefingItem
from .summarizers.base import Summarizer


@dataclass
class PipelineResult:
    items: List[BriefingItem]
    errors: List[str] = field(default_factory=list)
    fetched: int = 0
    unique: int = 0
    skipped: int = 0


class BriefingPipeline:
    def __init__(
        self,
        fetcher: FeedFetcher,
        processor: ArticleProcessor,
        summarizer: Summarizer,
    ) -> None:
        self.fetcher = fetcher
        self.processor = processor
        self.summarizer = summarizer

    def run(self, limit: int, skip_links: Optional[Set[str]] = None) -> PipelineResult:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        articles = self.fetcher.fetch_all()
        unique_articles = self.processor.deduplicate(articles)
        known_links = skip_links or set()
        candidates = [article for article in unique_articles if article.link not in known_links]
        result = PipelineResult(
            items=[],
            errors=list(self.fetcher.errors),
            fetched=len(articles),
            unique=len(unique_articles),
            skipped=len(unique_articles) - len(candidates),
        )

        for article in candidates[:limit]:
            try:
                enriched = self.processor.extract_full_content(article)
                result.items.append(self.summarizer.summarize(enriched))
            except Exception as exc:  # Keep the daily run useful when one article fails.
                result.errors.append(f"{article.title}: {exc}")

        return result
