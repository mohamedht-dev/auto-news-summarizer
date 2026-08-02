import os
from typing import Optional
from openai import OpenAI
from ..models import Article, BriefingItem

class OpenAISummarizer:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def summarize(self, article: Article) -> BriefingItem:
        text_to_process = article.content or article.description
        
        prompt = f"""
        Analyze the following technology news article and provide a structured summary in Arabic and English.
        Article Title: {article.title}
        Source: {article.source}
        Content: {text_to_process}
        """
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional technology journalist specializing in AI and tech trends."},
                {"role": "user", "content": prompt}
            ],
            response_format=BriefingItem,
        )
        
        briefing_item = completion.choices[0].message.parsed
        briefing_item.source_url = article.link
        return briefing_item
