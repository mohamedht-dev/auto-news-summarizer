import unittest
from main import fetch_tech_news_rss, summarize_text_ai

class TestTechBrief(unittest.TestCase):

    def test_fetch_news(self):
        """Test if news fetching returns a list (even if empty)."""
        articles = fetch_tech_news_rss()
        self.assertIsInstance(articles, list)

    def test_summarize_placeholder(self):
        """Test if the summarization placeholder works as expected."""
        text = "This is a very long text that should be summarized by our placeholder function because it exceeds thirty words in length for testing purposes."
        summary = summarize_text_ai(text)
        self.assertIn("(AI Summary Placeholder)", summary)

if __name__ == '__main__':
    unittest.main()
