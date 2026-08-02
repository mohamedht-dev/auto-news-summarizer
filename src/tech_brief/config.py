"""Application defaults."""

import os
from typing import Dict, List

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_PER_SOURCE = 10
DEFAULT_MAX_CONTENT_CHARS = 8_000
DEFAULT_DATABASE_PATH = os.getenv("TECH_BRIEF_DB", "data/tech_brief.db")

DEFAULT_SOURCES: List[Dict[str, str]] = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "technology",
    },
    {
        "name": "OpenAI",
        "url": "https://openai.com/news/rss.xml",
        "category": "artificial-intelligence",
    },
]
