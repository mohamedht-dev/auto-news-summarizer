"""Markdown output."""

from typing import Iterable

from ..models import BriefingItem


class MarkdownRenderer:
    @staticmethod
    def render(items: Iterable[BriefingItem], date: str) -> str:
        lines = [
            f"# 🚀 موجز الذكاء الاصطناعي والتقنية | {date}",
            "",
            "> ملخص يومي لأهم التطورات التقنية باللغتين العربية والإنجليزية.",
            "",
        ]

        for item in items:
            lines.extend(
                [
                    f"## {item.headline_ar}",
                    "",
                    f"**العربية:** {item.summary_ar}",
                    "",
                    f"**English:** {item.summary_en}",
                    "",
                    "### 🔑 النقاط الأساسية",
                    "",
                ]
            )
            lines.extend(f"- {point}" for point in item.key_points)
            lines.extend(
                [
                    "",
                    f"**💡 لماذا يهم؟** {item.why_it_matters}",
                    "",
                    f"**📰 المصدر:** {item.source_name or 'غير محدد'}",
                    "",
                    f"**🔗 الرابط:** [اقرأ المزيد]({item.source_url})",
                    "",
                    "---",
                    "",
                ]
            )

        lines.extend(
            [
                "*تم التوليد تلقائيًا بواسطة Arabic AI Tech Intelligence Brief.*",
                "",
            ]
        )
        return "\n".join(lines)
