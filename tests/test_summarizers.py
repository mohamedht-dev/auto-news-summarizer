from types import SimpleNamespace

from tech_brief.models import Article, GeneratedSummary
from tech_brief.summarizers import ExtractiveSummarizer, OpenAISummarizer

ARTICLE = Article(
    title="A new tool ships",
    link="https://example.com/tool",
    description="The tool launched today. It helps developers automate tests.",
    source="Example News",
    published="2026-08-02",
)


def test_extractive_summarizer_produces_valid_item():
    item = ExtractiveSummarizer().summarize(ARTICLE)

    assert item.source_url == ARTICLE.link
    assert item.summary_en.startswith("The tool launched")
    assert item.key_points
    assert item.confidence == 0.45


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


def test_openai_summarizer_uses_structured_response_and_trusted_source_url():
    parsed = GeneratedSummary(
        headline_ar="إطلاق أداة جديدة",
        summary_ar="أُطلقت أداة جديدة لأتمتة الاختبارات.",
        summary_en="A new testing automation tool launched.",
        key_points=["تساعد المطورين"],
        why_it_matters="تقلل وقت الاختبار.",
        companies=[],
        technologies=[],
        confidence=0.9,
    )
    responses = FakeResponses(parsed)
    client = SimpleNamespace(responses=responses)

    item = OpenAISummarizer(client=client, model="test-model").summarize(ARTICLE)

    assert item.source_url == ARTICLE.link
    assert item.source_name == ARTICLE.source
    assert responses.calls[0]["text_format"] is GeneratedSummary
    assert responses.calls[0]["model"] == "test-model"
