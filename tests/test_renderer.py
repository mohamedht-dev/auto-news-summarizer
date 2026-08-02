from tech_brief.models import BriefingItem
from tech_brief.renderers import MarkdownRenderer


def test_markdown_renderer_includes_bilingual_content_and_source():
    item = BriefingItem(
        headline_ar="خبر تقني",
        summary_ar="ملخص عربي.",
        summary_en="English summary.",
        key_points=["النقطة الأولى"],
        why_it_matters="لأنه مفيد.",
        companies=[],
        technologies=[],
        confidence=0.8,
        source_url="https://example.com/story",
        source_name="Example",
    )

    markdown = MarkdownRenderer.render([item], "2026-08-02")

    assert "# 🚀 موجز الذكاء الاصطناعي والتقنية | 2026-08-02" in markdown
    assert "**العربية:** ملخص عربي." in markdown
    assert "**English:** English summary." in markdown
    assert "[اقرأ المزيد](https://example.com/story)" in markdown
