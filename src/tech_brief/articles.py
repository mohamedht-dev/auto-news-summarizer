"""Article cleanup and full-text extraction."""

from ipaddress import ip_address
from typing import Iterable, List, Optional
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from .config import DEFAULT_MAX_CONTENT_CHARS
from .models import Article

USER_AGENT = "ArabicAITechBrief/0.4 (+https://github.com/mohamedht-dev/auto-news-summarizer)"


class ArticleProcessor:
    def __init__(
        self,
        session: Optional[requests.Session] = None,
        max_content_chars: int = DEFAULT_MAX_CONTENT_CHARS,
    ) -> None:
        self.session = session or requests.Session()
        self.max_content_chars = max_content_chars

    def extract_full_content(self, article: Article) -> Article:
        if not self._is_safe_article_url(article.link):
            article.content = article.description
            return article

        try:
            response = self.session.get(
                article.link,
                timeout=15,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "nav", "footer", "aside"]):
                tag.decompose()

            content = self._select_content(soup)
            if content:
                article.content = content[: self.max_content_chars]
        except requests.RequestException:
            article.content = article.description

        return article

    @staticmethod
    def _select_content(soup: BeautifulSoup) -> str:
        selectors = ("article", ".article-content", ".post-content", ".entry-content", "main")
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = " ".join(element.stripped_strings)
                if text:
                    return text

        return " ".join(" ".join(paragraph.stripped_strings) for paragraph in soup.find_all("p"))

    @classmethod
    def deduplicate(cls, articles: Iterable[Article]) -> List[Article]:
        seen = set()
        unique: List[Article] = []

        for article in articles:
            key = cls._canonical_url(article.link) or article.title.strip().casefold()
            if key not in seen:
                seen.add(key)
                unique.append(article)

        return unique

    @staticmethod
    def _canonical_url(url: str) -> str:
        parts = urlsplit(url.strip())
        if not parts.netloc:
            return url.strip().casefold()
        return urlunsplit(
            (parts.scheme.casefold(), parts.netloc.casefold(), parts.path.rstrip("/"), "", "")
        )

    @staticmethod
    def _is_safe_article_url(url: str) -> bool:
        parts = urlsplit(url.strip())
        if parts.scheme.casefold() not in {"http", "https"} or not parts.hostname:
            return False
        try:
            return ip_address(parts.hostname).is_global
        except ValueError:
            return parts.hostname.casefold() != "localhost"
