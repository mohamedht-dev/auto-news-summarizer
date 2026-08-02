import requests
from bs4 import BeautifulSoup
import feedparser
import os
from datetime import datetime
import re

def clean_html(raw_html):
    """Removes HTML tags from a string and cleans up whitespace."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r'\s+', ' ', text).strip()

def summarize_extractive_free(text, max_sentences=3):
    """A free, non-AI extractive summarizer that picks the first few sentences."""
    if not text:
        return "No content available to summarize."
    sentences = re.split(r'(?<=[.!?])\s+', text)
    summary = " ".join(sentences[:max_sentences])
    return summary + " (Free Extractive Summary)"

def summarize_with_openai(text):
    """Summarizes text using OpenAI's API if an API key is provided."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        # Note: Using requests directly to avoid dependency on the openai library if not needed
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that summarizes tech news in a concise way. Provide the summary in both English and Arabic."},
                {"role": "user", "content": f"Summarize this article: {text[:4000]}"}
            ],
            "max_tokens": 500
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

def fetch_tech_news_rss(rss_url="https://techcrunch.com/feed/"):
    """Fetches tech news from an RSS feed with timeout and error handling."""
    try:
        response = requests.get(rss_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        articles = []
        for entry in feed.entries:
            title = entry.title if hasattr(entry, 'title') else 'No Title'
            link = entry.link if hasattr(entry, 'link') else '#'
            # Clean HTML from the summary/description
            raw_summary = entry.summary if hasattr(entry, 'summary') else (entry.description if hasattr(entry, 'description') else '')
            clean_summary = clean_html(raw_summary)
            articles.append({'title': title, 'link': link, 'content': clean_summary})
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
    print("Starting Arabic AI Tech Brief...")
    
    news_articles = fetch_tech_news_rss()

    briefing_output = f"# Tech News Daily Briefing - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    briefing_output += "## Latest Tech News Summaries:\n\n"

    if news_articles:
        for i, article in enumerate(news_articles[:5]): # Process top 5 articles
            print(f"Processing article {i+1}: {article['title']}")
            
            # Try AI summarization first, fall back to extractive if it fails or no key
            summary = summarize_with_openai(article['content'])
            if not summary:
                summary = summarize_extractive_free(article['content'])
            
            briefing_output += f"### {i+1}. [{article['title']}]({article['link']})\n"
            briefing_output += f"{summary}\n\n"
            briefing_output += "---\n\n"
    else:
        briefing_output += "No tech news found today.\n"
    
    save_daily_briefing(briefing_output)
    print("Briefing generated successfully.")

if __name__ == "__main__":
    main()
