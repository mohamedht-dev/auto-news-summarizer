"""Command-line interface."""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv

from .articles import ArticleProcessor
from .config import DEFAULT_DATABASE_PATH, DEFAULT_MODEL, DEFAULT_SOURCES
from .database import Database
from .feeds import FeedFetcher
from .pipeline import BriefingPipeline
from .renderers import MarkdownRenderer
from .service import NewsService
from .summarizers import Summarizer, create_summarizer

app = typer.Typer(help="Generate a bilingual daily technology briefing from RSS feeds.")


@app.callback()
def cli() -> None:
    """Generate bilingual technology briefings."""


def _select_summarizer(offline: bool, model: str) -> Summarizer:
    api_key = os.getenv("OPENAI_API_KEY")
    if offline or not api_key:
        if not offline:
            typer.echo("[WARN] OPENAI_API_KEY is not set; using the extractive summarizer.")
    return create_summarizer(offline=offline, model=model)


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


@app.command()
def sync(
    limit: Annotated[
        int, typer.Option(min=1, max=100, help="Maximum number of new articles.")
    ] = 10,
    database: Annotated[Path, typer.Option(help="SQLite database path.")] = Path(
        DEFAULT_DATABASE_PATH
    ),
    model: Annotated[
        Optional[str],
        typer.Option(help="OpenAI model; defaults to OPENAI_MODEL or gpt-4o-mini."),
    ] = None,
    offline: Annotated[
        bool, typer.Option(help="Never call OpenAI; use extractive summaries.")
    ] = False,
) -> None:
    """Fetch new articles and persist them for the web platform."""

    load_dotenv()
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    service = NewsService(Database(str(database)))
    result = service.sync(limit=limit, offline=offline, model=selected_model)
    typer.echo(
        f"[OK] Saved {result.saved} new articles; skipped {result.skipped} existing articles"
    )
    for error in result.errors:
        typer.echo(f"[WARN] {error}", err=True)


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Host interface.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535, help="HTTP port.")] = 8000,
    reload: Annotated[bool, typer.Option(help="Reload on source changes.")] = False,
) -> None:
    """Run the Arabic technology news web platform."""

    import uvicorn

    load_dotenv()
    uvicorn.run("tech_brief.web.app:app", host=host, port=port, reload=reload)


@app.command()
def worker(
    interval_minutes: Annotated[
        int, typer.Option(min=5, max=1440, help="Minutes between synchronization runs.")
    ] = 60,
    limit: Annotated[
        int, typer.Option(min=1, max=100, help="Maximum new articles per run.")
    ] = 15,
    database: Annotated[Path, typer.Option(help="SQLite database path.")] = Path(
        DEFAULT_DATABASE_PATH
    ),
    model: Annotated[
        Optional[str], typer.Option(help="OpenAI model used for summaries.")
    ] = None,
    offline: Annotated[
        bool, typer.Option(help="Never call OpenAI; use extractive summaries.")
    ] = False,
) -> None:
    """Continuously synchronize the web archive on a fixed interval."""

    load_dotenv()
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    service = NewsService(Database(str(database)))
    typer.echo(f"[INFO] Worker started; synchronizing every {interval_minutes} minutes")

    try:
        while True:
            try:
                result = service.sync(limit=limit, offline=offline, model=selected_model)
                typer.echo(
                    f"[OK] Saved {result.saved}; skipped {result.skipped}; "
                    f"errors {len(result.errors)}"
                )
            except Exception as exc:  # A later scheduled run can recover automatically.
                typer.echo(f"[ERROR] Synchronization failed: {exc}", err=True)
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        typer.echo("[INFO] Worker stopped")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
