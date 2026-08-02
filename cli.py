import typer
import os
from datetime import datetime
from .feeds import FeedFetcher
from .articles import ArticleProcessor
from .summarizers.openai import OpenAISummarizer
from .renderers.markdown import MarkdownRenderer

app = typer.Typer()

@app.command()
def generate(
    limit: int = 5,
    output_dir: str = "daily_briefings"
):
    """جلب الأخبار وتوليد الموجز اليومي."""
    sources = [
        {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
        {"name": "OpenAI", "url": "https://openai.com/news/rss.xml"}
    ]
    
    typer.echo("🔍 جاري جلب الأخبار...")
    fetcher = FeedFetcher(sources)
    articles = fetcher.fetch_all()
    
    typer.echo("🧹 تنظيف البيانات وإزالة التكرار...")
    processor = ArticleProcessor()
    articles = processor.deduplicate(articles)
    
    # Take only the limit
    articles = articles[:limit]
    
    typer.echo(f"📝 استخراج المحتوى وتلخيص {len(articles)} مقالات...")
    summarizer = OpenAISummarizer()
    briefing_items = []
    
    for art in articles:
        typer.echo(f"  - معالجة: {art.title}")
        art = processor.extract_full_content(art)
        try:
            item = summarizer.summarize(art)
            briefing_items.append(item)
        except Exception as e:
            typer.echo(f"  ❌ فشل تلخيص {art.title}: {e}")
            
    if not briefing_items:
        typer.echo("⚠️ لم يتم توليد أي ملخصات.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    md_content = MarkdownRenderer.render(briefing_items, date_str)
    
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"tech_briefing_{date_str}.md")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    typer.echo(f"✅ تم بنجاح! التقرير جاهز في: {file_path}")

def main():
    app()

if __name__ == "__main__":
    main()
