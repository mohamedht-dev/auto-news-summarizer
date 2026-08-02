# نبض التقنية | Arabic AI Tech Brief

[![CI](https://github.com/mohamedht-dev/auto-news-summarizer/actions/workflows/ci.yml/badge.svg)](https://github.com/mohamedht-dev/auto-news-summarizer/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/mohamedht-dev/auto-news-summarizer)

منصة ويب عربية مفتوحة المصدر تجمع أخبار التقنية والذكاء الاصطناعي من خلاصات RSS، تستخرج محتوى المقالات، وتحوّله إلى ملخصات عربية وإنجليزية قابلة للبحث والأرشفة. تعمل عبر OpenAI عند توفير المفتاح، وتتحول تلقائيًا إلى تلخيص استخراجي مجاني عند غيابه.

An open-source Arabic-first news intelligence platform. It collects RSS articles, extracts their content, generates bilingual structured summaries, and serves a searchable web archive with an administration dashboard.

## ما الجديد في الإصدار 0.4

- واجهة عربية RTL متجاوبة مع الجوال والوضع الليلي.
- صفحة رئيسية، أرشيف، بحث، تصفية، صفحات أخبار، أخبار مرتبطة، وRSS عام.
- قاعدة SQLite دائمة تمنع تكرار الأخبار وتحفظ سجل كل تشغيل.
- لوحة إدارة محمية بكلمة مرور وCSRF لإضافة مصادر RSS أو تعطيلها أو حذفها.
- تشغيل التوليد من لوحة الإدارة في الخلفية.
- واجهة JSON موثقة تلقائيًا على `/api/docs`.
- عامل مجدول لتحديث الأرشيف باستمرار.
- رؤوس حماية، سياسة محتوى CSP، تقييد النطاقات، Sitemap، Robots، وضغط GZip.
- صورة Docker وملف Compose يشغّلان الموقع والعامل المجدول مع تخزين دائم مشترك.

## تشغيل سريع

```bash
git clone https://github.com/mohamedht-dev/auto-news-summarizer.git
cd auto-news-summarizer
python -m venv .venv
python -m pip install -e .
cp .env.example .env
tech-brief sync --offline --limit 10
tech-brief serve
```

افتح `http://127.0.0.1:8000`. يعمل الأمر السابق مجانًا دون مفتاح OpenAI. لإنتاج ملخصات ذكية ثنائية اللغة، ضع `OPENAI_API_KEY` في ملف `.env` ثم شغّل `tech-brief sync` دون `--offline`.

في Windows PowerShell استخدم `Copy-Item .env.example .env` بدل `cp`.

## الإعدادات

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
TECH_BRIEF_DB=data/tech_brief.db
TECH_BRIEF_ADMIN_PASSWORD=use-a-long-random-password
TECH_BRIEF_SESSION_SECRET=use-a-different-long-random-secret
TECH_BRIEF_COOKIE_SECURE=0
TECH_BRIEF_ALLOWED_HOSTS=localhost,127.0.0.1
```

في بيئة الإنتاج:

- اجعل `TECH_BRIEF_COOKIE_SECURE=1` بعد تشغيل HTTPS.
- استبدل `TECH_BRIEF_ALLOWED_HOSTS` بنطاق الموقع الحقيقي.
- احفظ كلمة الإدارة ومفتاح الجلسة ومفتاح OpenAI في مدير أسرار، ولا تضف ملف `.env` إلى Git.
- ضع مجلد `data/` على قرص دائم حتى لا يضيع الأرشيف عند إعادة النشر.

## الأوامر

```bash
# إنشاء موجز Markdown بالطريقة القديمة
tech-brief generate --limit 5

# مزامنة الأخبار الجديدة إلى قاعدة بيانات الموقع
tech-brief sync --limit 15

# مزامنة مجانية دون OpenAI
tech-brief sync --offline --limit 15

# تشغيل الموقع
tech-brief serve --host 0.0.0.0 --port 8000

# تحديث الأرشيف كل ساعة؛ ينفذ أول مزامنة فورًا
tech-brief worker --interval-minutes 60 --limit 15
```

يمكن تغيير مسار قاعدة البيانات في أوامر المزامنة والعامل عبر `--database`، أو لجميع أجزاء التطبيق عبر `TECH_BRIEF_DB`.

## Docker

أنشئ ملف `.env` بقيم الإنتاج أولًا، ثم:

```bash
docker compose up --build -d
docker compose ps
```

يعمل `web` على المنفذ 8000، ويحدّث `worker` الأخبار كل ساعة. يشتركان في وحدة التخزين `tech-brief-data`.

لإنشاء صورة الموقع فقط:

```bash
docker build -t tech-brief .
docker run --rm -p 8000:8000 --env-file .env -v tech-brief-data:/app/data tech-brief
```

## نشر مجاني مؤقت على Render

يتضمن المشروع ملف `render.yaml` جاهزًا لخدمة Render المجانية. اضغط زر **Deploy to Render** أعلى الصفحة، ثم وافق على إنشاء الخدمة. تُعبّئ الخدمة ثمانية أخبار تلقائيًا عند كل إقلاع وتعيد نشر `main` بعد نجاح فحوصات CI.

الخدمة المجانية تنام بعد الخمول، وقد تستغرق أول زيارة قرابة دقيقة. كما أن SQLite مؤقتة في الخطة المجانية؛ لذلك يُعاد بناء الأرشيف عند إعادة التشغيل. استخدم PostgreSQL أو قرصًا دائمًا عند الانتقال إلى إنتاج حقيقي.

## المسارات والواجهات

| المسار | الغرض |
| --- | --- |
| `/` | أحدث الأخبار والبحث والتصفية |
| `/archive` | الأرشيف الكامل مع الصفحات |
| `/articles/{id}` | الملخص العربي والإنجليزي وتفاصيل الخبر |
| `/admin` | إدارة المصادر وعمليات التحديث |
| `/api/articles` | واجهة JSON قابلة للبحث والتصفح |
| `/api/docs` | توثيق OpenAPI التفاعلي |
| `/feed.xml` | خلاصة RSS للأخبار الملخصة |
| `/sitemap.xml` | خريطة الموقع لمحركات البحث |
| `/health` | فحص جاهزية الخدمة |

## كيف يعمل

```text
RSS sources
    ↓
collect + deduplicate
    ↓
safe article extraction
    ↓
OpenAI structured summary ── or ── free extractive summary
    ↓
SQLite archive
    ↓
FastAPI + Jinja web, JSON API, RSS
```

يستخدم ملخص OpenAI مخرجات منظمة متوافقة مع نموذج Pydantic، بينما يحافظ الوضع المجاني على عمل المنصة في التطوير أو عند غياب المفتاح.

## التطوير والاختبارات

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest --cov=tech_brief --cov-report=term-missing --cov-fail-under=80
```

يفحص CI المشروع على Python 3.9 و3.11 و3.13. كما تُشغّل مهمة `Daily Tech Briefing` يوميًا الساعة 08:00 بتوقيت الرياض وتتيح ملف Markdown من قسم Artifacts.

## بنية المشروع

```text
src/tech_brief/
├── articles.py          # استخراج وتنظيف المقال
├── database.py          # SQLite والمصادر والأرشيف وسجل التشغيل
├── feeds.py             # جلب RSS
├── pipeline.py          # تنسيق مراحل الجمع والتلخيص
├── service.py           # مزامنة الأخبار وحفظها
├── summarizers/         # OpenAI والتلخيص المجاني
├── renderers/           # إخراج Markdown
└── web/
    ├── app.py           # تطبيق FastAPI والمسارات والأمان
    ├── templates/       # صفحات Jinja العربية
    └── static/          # CSS وJavaScript وملف PWA
```

## خارطة الطريق

- [x] منصة ويب عربية وأرشيف قابل للبحث.
- [x] إدارة مصادر RSS من الموقع.
- [x] عامل مزامنة مجدول وتشغيل Docker.
- [ ] إرسال الموجز إلى Telegram والبريد.
- [ ] حسابات مستخدمين وقوائم اهتمامات شخصية.
- [ ] PostgreSQL وطابور مهام للنشر واسع النطاق.
- [ ] استخدام Batch API للأرشيفات الكبيرة وتقليل تكلفة المعالجة.

## الترخيص

مرخص تحت رخصة [MIT](LICENSE).
