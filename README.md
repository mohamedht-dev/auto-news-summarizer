# 🚀 Arabic AI Tech Intelligence Brief

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source](https://img.shields.io/badge/Open%20Source-Heart-red.svg)](https://github.com/mohamedht-dev/auto-news-summarizer)

أداة برمجية مفتوحة المصدر تقوم بتوليد موجز يومي ذكي لأهم أخبار التقنية والذكاء الاصطناعي باللغتين العربية والإنجليزية، مع أتمتة كاملة للتشغيل.

An open-source Python tool that generates bilingual daily technology briefings from RSS feeds using AI, featuring full automation and professional CLI.

## ✨ المميزات (Features)
- **ذكاء اصطناعي متطور:** يستخدم `gpt-4o-mini` مع Structured Outputs لضمان دقة الملخصات.
- **تحليل المحتوى الكامل:** لا يكتفي بالعناوين، بل يقرأ المقالات كاملة لاستخراج الفائدة.
- **أتمتة كاملة:** يعمل تلقائياً كل صباح عبر GitHub Actions.
- **دعم اللغتين:** ملخصات متزامنة بالعربية والإنجليزية.
- **هيكل برمج احترافي:** حزمة Python قابلة للتثبيت وسهلة التوسيع.

## 🛠️ التثبيت (Installation)
```bash
git clone https://github.com/mohamedht-dev/auto-news-summarizer.git
cd auto-news-summarizer
pip install -e .
```

## 🚀 الاستخدام (Usage)
تأكد من ضبط مفتاح OpenAI في متغيرات البيئة:
```bash
export OPENAI_API_KEY='your-key-here'
tech-brief generate --limit 5
```

## 📅 خارطة الطريق (Roadmap)
- [x] تحويل المشروع إلى حزمة Python معيارية.
- [x] دعم استخراج المحتوى الكامل للمقالات.
- [x] استخدام مخرجات منظمة (Structured Outputs).
- [ ] إضافة واجهة ويب بسيطة (FastAPI).
- [ ] دعم قنوات إرسال إضافية (Telegram/Email).

## 📄 الترخيص (License)
هذا المشروع مرخص تحت رخصة **MIT**.

---
*Made with ❤️ for the Tech Community.*
