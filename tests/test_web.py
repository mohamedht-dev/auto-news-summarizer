import re

from fastapi.testclient import TestClient

from tech_brief.database import Database
from tech_brief.models import BriefingItem
from tech_brief.web.app import create_app


def seed_article(database):
    return database.save_item(
        BriefingItem(
            original_title="New developer platform",
            headline_ar="منصة جديدة للمطورين",
            summary_ar="ملخص عربي لمنصة تقنية جديدة.",
            summary_en="An English summary for a new technology platform.",
            key_points=["إطلاق المنصة", "أدوات أسرع"],
            why_it_matters="تسرّع بناء المنتجات.",
            companies=["Example"],
            technologies=["Cloud"],
            confidence=0.88,
            source_url="https://example.com/platform",
            source_name="TechCrunch",
            published="2026-08-02T09:00:00+00:00",
            category="technology",
        ),
        summarizer="extractive",
    )


def csrf_from(response):
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match
    return match.group(1)


def test_public_pages_api_feed_and_security_headers(tmp_path):
    database_path = str(tmp_path / "web.db")
    database = Database(database_path)
    database.initialize()
    article_id = seed_article(database)

    with TestClient(create_app(database_path)) as client:
        home = client.get("/")
        archive = client.get("/archive", params={"q": "منصة"})
        article = client.get(f"/articles/{article_id}")
        saved = client.get("/saved")
        api = client.get("/api/articles", params={"q": "developer"})
        stats = client.get("/api/stats")
        feed = client.get("/feed.xml")

        assert home.status_code == 200
        assert "منصة جديدة للمطورين" in home.text
        assert "data-bookmark" in home.text
        assert home.headers["x-frame-options"] == "DENY"
        assert client.get("/static/og.png").status_code == 200
        assert client.get("/static/icon.svg").status_code == 200
        assert archive.status_code == 200
        assert article.status_code == 200
        assert "د قراءة" in article.text
        assert saved.status_code == 200
        assert "data-saved-grid" in saved.text
        assert api.json()["total"] == 1
        assert stats.json()["stats"]["articles"] == 1
        assert stats.json()["top_topics"][0] == {"name": "Example", "count": 1}
        service_worker = client.get("/service-worker.js")
        assert service_worker.status_code == 200
        assert service_worker.headers["service-worker-allowed"] == "/"
        assert "nabd-tech-v2" in service_worker.text
        assert feed.status_code == 200
        assert "application/rss+xml" in feed.headers["content-type"]
        assert "default-src 'self'" in home.headers["content-security-policy"]
        assert client.get("/robots.txt").status_code == 200
        assert client.get("/sitemap.xml").status_code == 200
        assert client.get("/health").json() == {"status": "ok", "articles": 1}
        assert client.get("/missing").status_code == 404


def test_admin_authentication_csrf_and_source_management(tmp_path, monkeypatch):
    monkeypatch.setenv("TECH_BRIEF_ADMIN_PASSWORD", "strong-test-password")
    monkeypatch.setenv("TECH_BRIEF_SESSION_SECRET", "test-secret-with-enough-entropy")
    application = create_app(str(tmp_path / "admin.db"))

    with TestClient(application) as client:
        login_page = client.get("/admin")
        assert login_page.status_code == 401
        csrf_token = csrf_from(login_page)

        bad_csrf = client.post(
            "/admin/login",
            data={"password": "strong-test-password", "csrf_token": "bad"},
        )
        assert bad_csrf.status_code == 403

        login = client.post(
            "/admin/login",
            data={"password": "strong-test-password", "csrf_token": csrf_token},
        )
        assert login.status_code == 200
        assert "لوحة الإدارة" in login.text

        admin_csrf = csrf_from(login)
        added = client.post(
            "/admin/sources",
            data={
                "name": "Example",
                "url": "https://example.com/feed.xml",
                "category": "technology",
                "csrf_token": admin_csrf,
            },
        )
        assert added.status_code == 200
        assert "Example" in added.text

        blocked = client.post(
            "/admin/sources",
            data={
                "name": "Local",
                "url": "http://127.0.0.1/feed.xml",
                "category": "technology",
                "csrf_token": csrf_from(added),
            },
        )
        assert blocked.status_code == 200
        assert "تحقق من اسم المصدر" in blocked.text
