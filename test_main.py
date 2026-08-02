import unittest
from unittest.mock import patch, MagicMock
from main import fetch_tech_news_rss, summarize_extractive_free, clean_html

class TestTechBrief(unittest.TestCase):

    def test_clean_html(self):
        """Test HTML cleaning function."""
        html = "<div>Hello <p>World</p></div>"
        self.assertEqual(clean_html(html), "Hello World")

    @patch('requests.get')
    def test_fetch_news_rss_success(self, mock_get):
        """Test successful RSS fetching using Mock."""
        mock_response = MagicMock()
        mock_response.content = b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><item><title>Test Article</title><link>http://test.com</link><description>Test Description</description></item></channel></rss>'
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        articles = fetch_tech_news_rss()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'Test Article')

    def test_summarize_extractive_free(self):
        """Test the free extractive summarizer."""
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        summary = summarize_extractive_free(text, max_sentences=2)
        self.assertIn("Sentence one. Sentence two.", summary)
        self.assertIn("(Free Extractive Summary)", summary)

if __name__ == '__main__':
    unittest.main()
