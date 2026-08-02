from typing import List
from ..models import BriefingItem

class MarkdownRenderer:
    @staticmethod
    def render(items: List[BriefingItem], date: str) -> str:
        md = f"# 🚀 موجز الذكاء الاصطناعي والتقنية | {date}\n\n"
        md += "> ملخص يومي لأهم التطورات التقنية باللغتين العربية والإنجليزية.\n\n"
        
        for item in items:
            md += f"## {item.headline_ar}\n\n"
            md += f"**العربية:** {item.summary_ar}\n\n"
            md += f"**English:** {item.summary_en}\n\n"
            md += "### 🔑 النقاط الأساسية:\n"
            for pt in item.key_points:
                md += f"- {pt}\n"
            md += f"\n**💡 لماذا يهم؟** {item.why_it_matters}\n\n"
            md += f"**🔗 المصدر:** [إقرأ المزيد]({item.source_url})\n\n"
            md += "---\n\n"
        
        md += "\n*تم التوليد تلقائياً بواسطة Arabic AI Tech Intelligence Brief*\n"
        return md
