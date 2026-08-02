
import requests
from bs4 import BeautifulSoup

def fetch_tech_news(url="https://techcrunch.com/"):
    """Fetches tech news headlines from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = []
        # This selector might need adjustment based on the actual website structure
        for item in soup.find_all('h2', class_='post-block__title'):
            link = item.find('a')
            if link and link.text.strip():
                headlines.append(link.text.strip())
        return headlines
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

def summarize_text(text):
    """A placeholder for a text summarization function."""
    # In a real application, this would use an AI model (e.g., OpenAI API, Hugging Face model)
    # For this demo, we'll just take the first few words or a simplified version.
    words = text.split()
    if len(words) > 15:
        return ' '.join(words[:15]) + '... (ملخص)'
    return text + '... (ملخص)'

def main():
    print("بدء تشغيل ملخص الأخبار التقنية...")
    news_headlines = fetch_tech_news()

    if news_headlines:
        print("\nآخر الأخبار التقنية:")
        for i, headline in enumerate(news_headlines[:5]): # Summarize top 5 headlines
            summary = summarize_text(headline)
            print(f"{i+1}. {summary}")
    else:
        print("لم يتم العثور على أخبار تقنية.")

if __name__ == "__main__":
    main()
