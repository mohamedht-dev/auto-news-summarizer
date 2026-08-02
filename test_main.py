import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from datetime import datetime
from main import clean_html, summarize_extractive_free, summarize_with_openai, fetch_tech_news_rss, save_daily_briefing, main
import requests

class TestTechBrief(unittest.TestCase):

    def test_clean_html(self):
        """Test HTML cleaning function."""
        html = "<div>Hello <p>World</p></div><br>  Line<br>Break"
        self.assertEqual(clean_html(html), "Hello World Line Break")
        self.assertEqual(clean_html(None), "")
        self.assertEqual(clean_html(""), "")

    def test_summarize_extractive_free(self):
        """Test the free extractive summarizer."""
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        summary = summarize_extractive_free(text, max_sentences=2)
        self.assertIn("Sentence one. Sentence two.", summary)
        self.assertIn("(Free Extractive Summary / ملخص استخراجي مجاني)", summary)
        self.assertEqual(summarize_extractive_free(""), "No content available to summarize.")

    @patch("requests.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "gpt-4o-mini"})
    def test_summarize_with_openai_success(self, mock_post):
        """Test successful OpenAI summarization."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "AI Summary. / ملخص الذكاء الاصطناعي."}
            }]
        }
        mock_post.return_value = mock_response

        summary = summarize_with_openai("Test text")
        self.assertEqual(summary, "AI Summary. / ملخص الذكاء الاصطناعي.")
        mock_post.assert_called_once()

    @patch("main.requests.post") # Mock requests.post in the main module
    @patch("main.summarize_extractive_free") # Mock the fallback function
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key", "OPENAI_MODEL": "gpt-4o-mini"})
    def test_summarize_with_openai_failure_fallback(self, mock_free_summarize, mock_post):
        """Test OpenAI summarization failure with fallback to free mode."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error") # Use RequestException
        mock_free_summarize.return_value = "(Free Extractive Summary / ملخص استخراجي مجاني)"

        summary = summarize_with_openai("Test text")
        self.assertEqual(summary, "(Free Extractive Summary / ملخص استخراجي مجاني)")
        mock_post.assert_called_once()
        mock_free_summarize.assert_called_once_with("Test text")

    @patch("main.summarize_extractive_free") # Mock the fallback function
    @patch.dict(os.environ, {}, clear=True)
    def test_summarize_with_openai_no_key(self, mock_free_summarize):
        """Test OpenAI summarization when no API key is set."""
        mock_free_summarize.return_value = "(Free Extractive Summary / ملخص استخراجي مجاني)"
        summary = summarize_with_openai("Test text")
        self.assertEqual(summary, "(Free Extractive Summary / ملخص استخراجي مجاني)")
        mock_free_summarize.assert_called_once_with("Test text")

    @patch("requests.get")
    def test_fetch_tech_news_rss_success(self, mock_get):
        """Test successful RSS fetching."""
        mock_response = MagicMock()
        mock_response.content = b"""
        <rss version="2.0">
            <channel>
                <item>
                    <title>Article 1</title>
                    <link>http://example.com/1</link>
                    <description>Summary 1</description>
                </item>
                <item>
                    <title>Article 2</title>
                    <link>http://example.com/2</link>
                    <description>Summary 2</description>
                </item>
            </channel>
        </rss>
        """
        mock_get.return_value = mock_response
        articles = fetch_tech_news_rss()
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["title"], "Article 1")
        self.assertEqual(articles[0]["content"], "Summary 1")

    @patch("main.os.makedirs") # Patch os.makedirs in the main module
    @patch("main.os.path.exists", return_value=False) # Ensure makedirs is called
    @patch("builtins.open", new_callable=mock_open)
    def test_save_daily_briefing(self, mock_file_open, mock_path_exists, mock_makedirs):
        """Test saving the daily briefing to a Markdown file."""
        content = "# Test Briefing"
        save_daily_briefing(content)
        mock_makedirs.assert_called_once_with("daily_briefings", exist_ok=True)
        mock_file_open.assert_called_once()
        mock_file_open().write.assert_called_once_with(content)

    @patch("main.fetch_tech_news_rss")
    @patch("main.summarize_with_openai")
    @patch("main.save_daily_briefing")
    def test_main_flow(self, mock_save, mock_ai_summarize, mock_fetch_news):
        """Test the main execution flow."""
        mock_fetch_news.return_value = [
            {"title": "Test Article 1", "link": "http://link1.com", "content": "Content 1"},
            {"title": "Test Article 2", "link": "http://link2.com", "content": "Content 2"}
        ]
        mock_ai_summarize.side_effect = ["AI Summary 1", "Free Summary 2"] # Simulate one success, one fallback

        main()

        mock_fetch_news.assert_called_once()
        self.assertEqual(mock_ai_summarize.call_count, 2)
        mock_save.assert_called_once()
        saved_content = mock_save.call_args[0][0]
        self.assertIn("AI Summary 1", saved_content)
        self.assertIn("Free Summary 2", saved_content)
        self.assertIn("Test Article 1", saved_content)
        self.assertIn("Test Article 2", saved_content)

    @patch("main.fetch_tech_news_rss", return_value=[])
    @patch("main.save_daily_briefing")
    def test_main_no_news(self, mock_save, mock_fetch_news):
        """Test main flow when no news is found."""
        main()
        mock_fetch_news.assert_called_once()
        mock_save.assert_called_once()
        saved_content = mock_save.call_args[0][0]
        self.assertIn("No tech news found today.", saved_content)

if __name__ == "__main__":
    unittest.main()
