"""No-cost summarizer used when an OpenAI key is unavailable."""

import re
from typing import List

from bs4 import BeautifulSoup

from ..models import Article, BriefingItem

SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟])\s+")


class ExtractiveSummarizer:
    """Build a concise briefing from the article's own sentences."""

    def __init__(self, max_sentences: int = 3, max_chars: int = 700) -> None:
        self.max_sentences = max_sentences
        self.max_chars = max_chars

    def summarize(self, article: Article) -> BriefingItem:
        text = self._plain_text(article.content or article.description or article.title)
        sentences = [part.strip() for part in SENTENCE_SPLIT.split(text) if part.strip()]
        selected = sentences[: self.max_sentences] or [article.title]
        summary = " ".join(selected)[: self.max_chars].strip()

        return BriefingItem(
            headline_ar=article.title,
            summary_ar=summary,
            summary_en=summary,
            key_points=self._key_points(selected),
            why_it_matters=(
                "ملخص استخراجي تلقائي؛ استخدم مفتاح OpenAI للحصول على تحليل ثنائي اللغة."
            ),
            companies=[],
            technologies=[],
            confidence=0.45,
            source_url=article.link,
            source_name=article.source,
            published=article.published,
        )

    @staticmethod
    def _plain_text(value: str) -> str:
        return " ".join(BeautifulSoup(value, "html.parser").stripped_strings)

    @staticmethod
    def _key_points(sentences: List[str]) -> List[str]:
        points = [sentence[:220].strip() for sentence in sentences[:3] if sentence.strip()]
        return points or ["No summary text was available in the RSS entry."]
