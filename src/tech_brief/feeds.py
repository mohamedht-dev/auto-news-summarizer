"""RSS feed collection."""

from typing import Dict, Iterable, List, Mapping

import feedparser

from .config import DEFAULT_PER_SOURCE
from .models import Article


class FeedFetcher:
    def __init__(self, sources: Iterable[Mapping[str, str]], per_source: int = DEFAULT_PER_SOURCE):
        self.sources = list(sources)
        self.per_source = per_source
        self.errors: List[str] = []

    def fetch_all(self) -> List[Article]:
        articles: List[Article] = []
        self.errors = []

        for source in self.sources:
            try:
                articles.extend(self._fetch_source(source))
            except Exception as exc:  # A broken source should not stop the whole briefing.
                self.errors.append(f"{source.get('name', 'Unknown source')}: {exc}")

        return articles

    def _fetch_source(self, source: Mapping[str, str]) -> List[Article]:
        feed = feedparser.parse(source["url"])
        status = getattr(feed, "status", None)
        if status and int(status) >= 400:
            raise RuntimeError(f"feed returned HTTP {status}")

        articles: List[Article] = []
        entries = getattr(feed, "entries", [])
        for entry in entries[: self.per_source]:
            try:
                articles.append(self._to_article(entry, source))
            except (TypeError, ValueError):
                continue
        return articles

    @staticmethod
    def _to_article(entry: Mapping[str, object], source: Mapping[str, str]) -> Article:
        data: Dict[str, object] = dict(entry)
        title = str(data.get("title") or "Untitled article").strip()
        link = str(data.get("link") or "").strip()
        if not link:
            raise ValueError(f"RSS entry '{title}' has no link")

        return Article(
            title=title,
            link=link,
            description=str(data.get("summary") or data.get("description") or "").strip(),
            published=str(data.get("published") or data.get("updated") or "Unknown"),
            source=source.get("name", "Unknown source"),
            category=source.get("category", "technology"),
        )
