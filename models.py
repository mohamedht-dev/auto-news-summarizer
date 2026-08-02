from typing import List, Optional
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str
    link: str
    description: str
    content: Optional[str] = None
    published: str
    source: str
    category: Optional[str] = "technology"

class BriefingItem(BaseModel):
    headline_ar: str = Field(description="عنوان الخبر باللغة العربية")
    summary_ar: str = Field(description="ملخص الخبر باللغة العربية")
    summary_en: str = Field(description="Summary of the news in English")
    key_points: List[str] = Field(description="نقاط أساسية مستخلصة من الخبر")
    why_it_matters: str = Field(description="لماذا يهم هذا الخبر المجتمع التقني؟")
    companies: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str

class DailyBriefing(BaseModel):
    date: str
    items: List[BriefingItem]
    meta: dict
