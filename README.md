# 🚀 Arabic AI Tech Intelligence Brief

[![CI](https://github.com/mohamedht-dev/auto-news-summarizer/actions/workflows/ci.yml/badge.svg)](https://github.com/mohamedht-dev/auto-news-summarizer/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

أداة مفتوحة المصدر تجمع أخبار التقنية والذكاء الاصطناعي من خلاصات RSS، وتستخرج محتوى المقالات، ثم تنشئ موجزًا يوميًا بالعربية والإنجليزية. تعمل عبر OpenAI عند توفير المفتاح، وتستمر بوضع تلخيص استخراجي مجاني عند غيابه.

An open-source Python CLI that collects technology news from RSS feeds, extracts article text, and writes a bilingual daily Markdown briefing. It uses OpenAI Structured Outputs when configured and falls back to a free extractive mode when no API key is available.

## المميزات | Features

- حزمة Python معيارية قابلة للتثبيت مع أمر `tech-brief`.
- تلخيص منظم عبر OpenAI وPydantic، مع نموذج قابل للتغيير بواسطة `OPENAI_MODEL`.
- وضع `--offline` لا يحتاج مفتاحًا أو تكلفة API.
- تحمل أعطال المصادر أو المقالات الفردية دون خسارة الموجز بالكامل.
- إزالة تكرار الروابط حتى عند اختلاف معاملات التتبع.
- اختبارات آلية على Python 3.9 و3.11 و3.13.
- تشغيل يومي في 08:00 بتوقيت الرياض عبر GitHub Actions.

## التثبيت | Installation

```bash
git clone https://github.com/mohamedht-dev/auto-news-summarizer.git
cd auto-news-summarizer
python -m venv .venv
python -m pip install -e .
```

للمساهمة وتشغيل الاختبارات:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## الاستخدام | Usage

تشغيل مجاني دون OpenAI:

```bash
tech-brief generate --offline --limit 5
```

تشغيل التلخيص الثنائي اللغة عبر OpenAI:

```bash
cp .env.example .env
# ضع OPENAI_API_KEY داخل ملف .env
tech-brief generate --limit 5
```

يمكنك تغيير النموذج من البيئة أو الخيار المباشر:

```bash
OPENAI_MODEL=gpt-4o-mini tech-brief generate --limit 10
tech-brief generate --model gpt-4o-mini --output-dir daily_briefings
```

في Windows PowerShell استخدم `$env:OPENAI_MODEL = "gpt-4o-mini"` قبل تشغيل الأمر.

## الأتمتة على GitHub

1. افتح `Settings → Secrets and variables → Actions` في المستودع.
2. أضف سرًا باسم `OPENAI_API_KEY` للحصول على الملخصات العربية والإنجليزية بالذكاء الاصطناعي.
3. شغّل `Daily Tech Briefing` يدويًا من تبويب Actions للاختبار.
4. نزّل ملف `tech-briefing` من قسم Artifacts بعد انتهاء التشغيل.

إذا لم تضف المفتاح، فلن يفشل التشغيل؛ سيُنشئ موجزًا استخراجيًا مجانيًا. المهمة بصلاحية قراءة فقط ولا تدفع تغييرات تلقائيًا إلى المستودع.

## بنية المشروع

```text
src/tech_brief/
├── articles.py       # استخراج وتنظيف نص المقال
├── feeds.py          # جلب خلاصات RSS
├── pipeline.py       # تنسيق مراحل التنفيذ ومعالجة الأخطاء
├── summarizers/      # OpenAI والتلخيص الاستخراجي
└── renderers/        # إخراج Markdown
```

## خارطة الطريق | Roadmap

- [x] حزمة Python معيارية وCLI.
- [x] تلخيص منظم ووضع مجاني احتياطي.
- [x] اختبارات وCI وتشغيل يومي.
- [ ] مصادر RSS قابلة للتخصيص من ملف إعدادات.
- [ ] واجهة ويب خفيفة.
- [ ] إرسال الموجز عبر Telegram والبريد.

## الترخيص | License

مرخص تحت رخصة [MIT](LICENSE).
