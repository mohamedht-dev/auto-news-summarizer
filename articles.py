import requests
from bs4 import BeautifulSoup
from typing import List
from .models import Article

class ArticleProcessor:
    @staticmethod
    def extract_full_content(article: Article) -> Article:
        try:
            response = requests.get(article.link, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Common article body selectors
            selectors = ['article', '.article-content', '.post-content', '.entry-content', 'main']
            content = ""
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            if not content:
                # Fallback to paragraphs
                content = ' '.join([p.get_text() for p in soup.find_all('p')])
            
            article.content = content[:5000] # Limit content size
        except Exception:
            article.content = article.description # Fallback to RSS description
        return article

    @staticmethod
    def deduplicate(articles: List[Article]) -> List[Article]:
        seen_links = set()
        unique_articles = []
        for article in articles:
            if article.link not in seen_links:
                seen_links.add(article.link)
                unique_articles.append(article)
        return unique_articles
