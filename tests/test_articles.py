from tech_brief.articles import ArticleProcessor
from tech_brief.models import Article


def make_article(link: str, title: str = "News") -> Article:
    return Article(title=title, link=link, description="RSS fallback", source="Example")


class FakeResponse:
    text = """
    <html><body><nav>Menu</nav><article>
    <h1>Launch</h1><p>The product is now available.</p><script>ignore()</script>
    </article></body></html>
    """

    @staticmethod
    def raise_for_status() -> None:
        return None


class FakeSession:
    called = False

    def get(self, *args, **kwargs):
        self.called = True
        return FakeResponse()


def test_deduplicate_ignores_tracking_query_and_trailing_slash():
    articles = [
        make_article("https://example.com/story/?utm_source=rss"),
        make_article("https://example.com/story"),
    ]

    assert ArticleProcessor.deduplicate(articles) == [articles[0]]


def test_extract_full_content_removes_navigation_and_scripts():
    processor = ArticleProcessor(session=FakeSession())

    article = processor.extract_full_content(make_article("https://example.com/story"))

    assert article.content == "Launch The product is now available."


def test_extract_full_content_does_not_request_private_ip_addresses():
    session = FakeSession()
    article = make_article("http://127.0.0.1/admin")

    result = ArticleProcessor(session=session).extract_full_content(article)

    assert result.content == "RSS fallback"
    assert session.called is False
