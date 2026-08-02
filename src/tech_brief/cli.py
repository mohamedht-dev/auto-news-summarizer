"""Command-line interface."""

import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv

from .articles import ArticleProcessor
from .config import DEFAULT_MODEL, DEFAULT_SOURCES
from .feeds import FeedFetcher
from .pipeline import BriefingPipeline
from .renderers import MarkdownRenderer
from .summarizers import ExtractiveSummarizer, OpenAISummarizer, Summarizer

app = typer.Typer(help="Generate a bilingual daily technology briefing from RSS feeds.")


@app.callback()
def cli() -> None:
    """Generate bilingual technology briefings."""


def _select_summarizer(offline: bool, model: str) -> Summarizer:
    api_key = os.getenv("OPENAI_API_KEY")
    if offline or not api_key:
        if not offline:
            typer.echo("[WARN] OPENAI_API_KEY is not set; using the extractive summarizer.")
        return ExtractiveSummarizer()
    return OpenAISummarizer(api_key=api_key, model=model)


@app.command()
def generate(
    limit: Annotated[
        int, typer.Option(min=1, max=50, help="Maximum number of articles.")
    ] = 5,
    output_dir: Annotated[Path, typer.Option(help="Output directory.")] = Path(
        "daily_briefings"
    ),
    model: Annotated[
        Optional[str],
        typer.Option(help="OpenAI model; defaults to OPENAI_MODEL or gpt-4o-mini."),
    ] = None,
    offline: Annotated[
        bool, typer.Option(help="Never call OpenAI; use extractive summaries.")
    ] = False,
) -> None:
    """Fetch news and write today's briefing as Markdown."""

    load_dotenv()
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    summarizer = _select_summarizer(offline, selected_model)
    pipeline = BriefingPipeline(
        fetcher=FeedFetcher(DEFAULT_SOURCES),
        processor=ArticleProcessor(),
        summarizer=summarizer,
    )

    typer.echo("[INFO] Fetching and processing news feeds...")
    result = pipeline.run(limit)
    for error in result.errors:
        typer.echo(f"[WARN] {error}", err=True)

    if not result.items:
        typer.echo("[ERROR] No briefing items were generated.", err=True)
        raise typer.Exit(code=1)

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"tech_briefing_{date_str}.md"
    file_path.write_text(MarkdownRenderer.render(result.items, date_str), encoding="utf-8")

    typer.echo(f"[OK] Wrote {len(result.items)} summaries from {result.unique} unique articles")
    typer.echo(f"[OUTPUT] {file_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
