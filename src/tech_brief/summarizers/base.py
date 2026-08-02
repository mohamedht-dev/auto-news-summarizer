"""Summarizer contract."""

from typing import Protocol

from ..models import Article, BriefingItem


class Summarizer(Protocol):
    def summarize(self, article: Article) -> BriefingItem:
        """Convert an article into a briefing item."""
