import feedparser
from typing import List
from .models import Article

class FeedFetcher:
    def __init__(self, sources: List[dict]):
        self.sources = sources

    def fetch_all(self) -> List[Article]:
        all_articles = []
        for source in self.sources:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:10]:
                all_articles.append(Article(
                    title=entry.title,
                    link=entry.link,
                    description=entry.get('summary', entry.get('description', '')),
                    published=entry.get('published', entry.get('updated', 'Unknown')),
                    source=source['name'],
                    category=source.get('category', 'technology')
                ))
        return all_articles
