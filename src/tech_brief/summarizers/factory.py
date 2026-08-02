"""Summary provider selection shared by the CLI and web platform."""

import os

from ..config import DEFAULT_MODEL
from .base import Summarizer
from .extractive import ExtractiveSummarizer
from .openai import OpenAISummarizer


def create_summarizer(offline: bool = False, model: str = DEFAULT_MODEL) -> Summarizer:
    api_key = os.getenv("OPENAI_API_KEY")
    if offline or not api_key:
        return ExtractiveSummarizer()
    return OpenAISummarizer(api_key=api_key, model=model)
