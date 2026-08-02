import requests
from bs4 import BeautifulSoup
import feedparser
import os
from datetime import datetime

# Placeholder for a real AI summarization function
def summarize_text_ai(text):
    """Placeholder for an AI-powered text summarization function.
    This function would typically call an external AI service (e.g., OpenAI API)
    or use a local NLP model to generate a concise summary of the input text.
    For now, it returns a truncated version of the text.
    """
    words = text.split()
    if len(words) > 30:
        return ' '.join(words[:30]) + '... (AI Summary Placeholder)'
    return text + '... (AI Summary Placeholder)'

def fetch_tech_news_rss(rss_url="https://techcrunch.com/feed/"):
    """Fetches tech news from an RSS feed."""
    try:
        feed = feedparser.parse(rss_url)
        articles = []
        for entry in feed.entries:
            title = entry.title if hasattr(entry, 'title') else 'No Title'
            link = entry.link if hasattr(entry, 'link') else '#'
            summary = entry.summary if hasattr(entry, 'summary') else 'No Summary'
            articles.append({'title': title, 'link': link, 'summary': summary})
        return articles
    except Exception as e:
        print(f"Error fetching news from RSS: {e}")
        return []

def save_daily_briefing(briefing_content, directory="daily_briefings"):
    """Saves the daily news briefing to a Markdown file."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(directory, f"tech_news_briefing_{today_date}.md")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(briefing_content)
    print(f"Daily briefing saved to {filename}")

def main():
    print("بدء تشغيل جالب وملخص الأخبار التقنية...")
    
    # Fetch news from RSS feed
    news_articles = fetch_tech_news_rss()

    briefing_output = f"# ملخص الأخبار التقنية اليومي - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    briefing_output += "## آخر الأخبار التقنية:\n\n"

    if news_articles:
        for i, article in enumerate(news_articles[:5]): # Process top 5 articles
            # For now, we summarize the article's summary or title
            # In a future step, we'd fetch the full article content and summarize it with AI
            summarized_content = summarize_text_ai(article['summary'] if article['summary'] != 'No Summary' else article['title'])
            briefing_output += f"### {i+1}. [{article['title']}]({article['link']})\n"
            briefing_output += f"> {summarized_content}\n\n"
    else:
        briefing_output += "لم يتم العثور على أخبار تقنية.\n"
    
    print(briefing_output)
    save_daily_briefing(briefing_output)

if __name__ == "__main__":
    main()
