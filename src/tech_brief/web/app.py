"""FastAPI application for the Arabic AI technology news platform."""

import math
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path
from typing import Annotated, Dict, Optional
from urllib.parse import urlsplit
from xml.etree import ElementTree

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ..articles import ArticleProcessor
from ..config import DEFAULT_DATABASE_PATH, DEFAULT_MODEL
from ..database import Database
from ..service import NewsService

WEB_ROOT = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(WEB_ROOT / "templates"))
CATEGORY_LABELS = {
    "technology": "تقنية",
    "artificial-intelligence": "ذكاء اصطناعي",
    "cybersecurity": "أمن سيبراني",
    "startups": "شركات ناشئة",
    "business": "أعمال",
    "science": "علوم",
}
_generation_lock = threading.Lock()


def category_label(value: str) -> str:
    return CATEGORY_LABELS.get(value, value.replace("-", " ").title())


TEMPLATES.env.globals.update(
    category_label=category_label,
    current_year=datetime.now().year,
)


def create_app(database_path: Optional[str] = None) -> FastAPI:
    database = Database(database_path or os.getenv("TECH_BRIEF_DB", DEFAULT_DATABASE_PATH))
    database.initialize()

    application = FastAPI(
        title="نبض التقنية",
        description="منصة عربية ذكية لمتابعة أهم أخبار التقنية والذكاء الاصطناعي.",
        version="0.5.1",
        docs_url="/api/docs",
        redoc_url=None,
    )
    application.state.database = database
    application.state.news_service = NewsService(database)
    allowed_hosts = [
        host.strip()
        for host in os.getenv("TECH_BRIEF_ALLOWED_HOSTS", "*").split(",")
        if host.strip()
    ]
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts or ["*"])
    application.add_middleware(GZipMiddleware, minimum_size=800)
    application.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("TECH_BRIEF_SESSION_SECRET") or secrets.token_urlsafe(32),
        same_site="lax",
        https_only=os.getenv("TECH_BRIEF_COOKIE_SECURE", "0") == "1",
        max_age=60 * 60 * 8,
    )
    application.mount("/static", StaticFiles(directory=str(WEB_ROOT / "static")), name="static")

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'; img-src 'self' data: https:; "
            "style-src 'self'; script-src 'self'; connect-src 'self'"
        )
        if os.getenv("TECH_BRIEF_COOKIE_SECURE", "0") == "1":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @application.get("/", response_class=HTMLResponse)
    async def home(
        request: Request,
        q: str = "",
        category: str = "",
        source: Optional[int] = None,
        page: int = 1,
    ):
        page = max(page, 1)
        per_page = 9
        articles, total = database.list_articles(q, category, source, page, per_page)
        return TEMPLATES.TemplateResponse(
            request,
            "home.html",
            _context(
                request,
                database,
                articles=articles,
                featured=articles[0] if articles and page == 1 else None,
                q=q,
                selected_category=category,
                selected_source=source,
                page=page,
                page_count=max(math.ceil(total / per_page), 1),
                total=total,
                topics=database.top_topics(),
                title="نبض التقنية — موجز التقنية والذكاء الاصطناعي",
            ),
        )

    @application.get("/saved", response_class=HTMLResponse)
    async def saved_articles(request: Request):
        articles, _ = database.list_articles(per_page=100)
        return TEMPLATES.TemplateResponse(
            request,
            "saved.html",
            _context(
                request,
                database,
                articles=articles,
                title="المحفوظات — نبض التقنية",
                description="قائمة الأخبار التي حفظتها للقراءة لاحقًا على هذا الجهاز.",
            ),
        )

    @application.get("/archive", response_class=HTMLResponse)
    async def archive(
        request: Request,
        q: str = "",
        category: str = "",
        source: Optional[int] = None,
        page: int = 1,
    ):
        page = max(page, 1)
        per_page = 12
        articles, total = database.list_articles(q, category, source, page, per_page)
        return TEMPLATES.TemplateResponse(
            request,
            "archive.html",
            _context(
                request,
                database,
                articles=articles,
                q=q,
                selected_category=category,
                selected_source=source,
                page=page,
                page_count=max(math.ceil(total / per_page), 1),
                total=total,
                title="أرشيف الأخبار — نبض التقنية",
            ),
        )

    @application.get("/articles/{article_id}", response_class=HTMLResponse)
    async def article_detail(request: Request, article_id: int):
        article = database.get_article(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="الخبر غير موجود")
        related, _ = database.list_articles(category=str(article["category"]), per_page=4)
        related = [item for item in related if item["id"] != article_id][:3]
        return TEMPLATES.TemplateResponse(
            request,
            "article.html",
            _context(
                request,
                database,
                article=article,
                related=related,
                title=f"{article['headline_ar']} — نبض التقنية",
                description=article["summary_ar"],
            ),
        )

    @application.get("/admin", response_class=HTMLResponse)
    async def admin(request: Request):
        if not _is_admin(request):
            return TEMPLATES.TemplateResponse(
                request,
                "login.html",
                _context(
                    request,
                    database,
                    title="دخول الإدارة — نبض التقنية",
                    admin_configured=bool(os.getenv("TECH_BRIEF_ADMIN_PASSWORD")),
                ),
                status_code=401,
            )
        return TEMPLATES.TemplateResponse(
            request,
            "admin.html",
            _context(
                request,
                database,
                runs=database.list_runs(),
                title="لوحة الإدارة — نبض التقنية",
                generation_busy=_generation_lock.locked(),
                openai_configured=bool(os.getenv("OPENAI_API_KEY")),
            ),
        )

    @application.post("/admin/login")
    async def admin_login(
        request: Request,
        password: Annotated[str, Form()],
        csrf_token: Annotated[str, Form()],
    ):
        _verify_csrf(request, csrf_token)
        configured = os.getenv("TECH_BRIEF_ADMIN_PASSWORD")
        if not configured:
            _flash(request, "عيّن TECH_BRIEF_ADMIN_PASSWORD أولًا.", "error")
        elif secrets.compare_digest(password, configured):
            request.session["is_admin"] = True
            request.session["csrf_token"] = secrets.token_urlsafe(24)
            _flash(request, "مرحبًا بك في لوحة الإدارة.", "success")
        else:
            _flash(request, "كلمة المرور غير صحيحة.", "error")
        return RedirectResponse("/admin", status_code=303)

    @application.post("/admin/logout")
    async def admin_logout(request: Request, csrf_token: Annotated[str, Form()]):
        _require_admin(request)
        _verify_csrf(request, csrf_token)
        request.session.clear()
        return RedirectResponse("/", status_code=303)

    @application.post("/admin/sources")
    async def add_source(
        request: Request,
        name: Annotated[str, Form()],
        url: Annotated[str, Form()],
        category: Annotated[str, Form()],
        csrf_token: Annotated[str, Form()],
    ):
        _require_admin(request)
        _verify_csrf(request, csrf_token)
        if not name.strip() or not _safe_public_url(url):
            _flash(request, "تحقق من اسم المصدر ورابط RSS العام.", "error")
        else:
            try:
                database.add_source(name, url, category)
                _flash(request, "تمت إضافة المصدر بنجاح.", "success")
            except Exception as exc:
                message = "المصدر موجود مسبقًا." if "UNIQUE" in str(exc) else "تعذرت إضافة المصدر."
                _flash(request, message, "error")
        return RedirectResponse("/admin#sources", status_code=303)

    @application.post("/admin/sources/{source_id}/toggle")
    async def toggle_source(
        request: Request,
        source_id: int,
        csrf_token: Annotated[str, Form()],
    ):
        _require_admin(request)
        _verify_csrf(request, csrf_token)
        database.toggle_source(source_id)
        _flash(request, "تم تحديث حالة المصدر.", "success")
        return RedirectResponse("/admin#sources", status_code=303)

    @application.post("/admin/sources/{source_id}/delete")
    async def delete_source(
        request: Request,
        source_id: int,
        csrf_token: Annotated[str, Form()],
    ):
        _require_admin(request)
        _verify_csrf(request, csrf_token)
        database.delete_source(source_id)
        _flash(request, "تم حذف المصدر مع الاحتفاظ بأخباره المؤرشفة.", "success")
        return RedirectResponse("/admin#sources", status_code=303)

    @application.post("/admin/generate")
    async def generate_now(
        request: Request,
        background_tasks: BackgroundTasks,
        limit: Annotated[int, Form()] = 10,
        model: Annotated[str, Form()] = DEFAULT_MODEL,
        offline: Annotated[Optional[str], Form()] = None,
        csrf_token: Annotated[str, Form()] = "",
    ):
        _require_admin(request)
        _verify_csrf(request, csrf_token)
        limit = min(max(limit, 1), 50)
        if not _generation_lock.acquire(blocking=False):
            _flash(request, "هناك عملية توليد جارية بالفعل.", "error")
        else:
            background_tasks.add_task(
                _run_generation,
                application.state.news_service,
                limit,
                offline == "1",
                model.strip() or DEFAULT_MODEL,
            )
            _flash(request, "بدأ توليد الموجز في الخلفية. حدّث الصفحة بعد قليل.", "success")
        return RedirectResponse("/admin#runs", status_code=303)

    @application.get("/api/articles")
    async def api_articles(
        q: str = "",
        category: str = "",
        source: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ):
        per_page = min(max(per_page, 1), 50)
        articles, total = database.list_articles(q, category, source, max(page, 1), per_page)
        return JSONResponse(
            {"items": articles, "total": total, "page": max(page, 1), "per_page": per_page}
        )

    @application.get("/api/stats")
    async def api_stats():
        return {"stats": database.stats(), "top_topics": database.top_topics()}

    @application.get("/service-worker.js", include_in_schema=False)
    async def service_worker():
        response = FileResponse(
            WEB_ROOT / "static" / "service-worker.js",
            media_type="application/javascript",
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Service-Worker-Allowed"] = "/"
        return response

    @application.get("/feed.xml")
    async def rss_feed(request: Request):
        articles, _ = database.list_articles(per_page=30)
        channel = ElementTree.Element("channel")
        ElementTree.SubElement(channel, "title").text = "نبض التقنية"
        ElementTree.SubElement(channel, "link").text = str(request.base_url)
        ElementTree.SubElement(channel, "description").text = (
            "موجز عربي لأهم أخبار التقنية والذكاء الاصطناعي"
        )
        ElementTree.SubElement(channel, "language").text = "ar"
        for article in articles:
            item = ElementTree.SubElement(channel, "item")
            ElementTree.SubElement(item, "title").text = str(article["headline_ar"])
            ElementTree.SubElement(item, "link").text = str(
                request.url_for("article_detail", article_id=article["id"])
            )
            ElementTree.SubElement(item, "guid").text = str(article["link"])
            ElementTree.SubElement(item, "description").text = str(article["summary_ar"])
            ElementTree.SubElement(item, "pubDate").text = str(article["published"])
        rss = ElementTree.Element("rss", {"version": "2.0"})
        rss.append(channel)
        return Response(
            ElementTree.tostring(rss, encoding="unicode"),
            media_type="application/rss+xml",
        )

    @application.get("/health")
    async def health():
        return {"status": "ok", "articles": database.stats()["articles"]}

    @application.get("/robots.txt", response_class=PlainTextResponse)
    async def robots(request: Request):
        base_url = str(request.base_url).rstrip("/")
        return f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {base_url}/sitemap.xml\n"

    @application.get("/sitemap.xml")
    async def sitemap(request: Request):
        articles, _ = database.list_articles(per_page=50)
        namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
        urlset = ElementTree.Element("urlset", {"xmlns": namespace})
        for location in (request.url_for("home"), request.url_for("archive")):
            url = ElementTree.SubElement(urlset, "url")
            ElementTree.SubElement(url, "loc").text = str(location)
        for article in articles:
            url = ElementTree.SubElement(urlset, "url")
            ElementTree.SubElement(url, "loc").text = str(
                request.url_for("article_detail", article_id=article["id"])
            )
        return Response(
            ElementTree.tostring(urlset, encoding="unicode"),
            media_type="application/xml",
        )

    @application.exception_handler(404)
    async def not_found(request: Request, exc):
        return TEMPLATES.TemplateResponse(
            request,
            "404.html",
            _context(request, database, title="الصفحة غير موجودة — نبض التقنية"),
            status_code=404,
        )

    return application


def _context(request: Request, database: Database, **values) -> Dict[str, object]:
    csrf_token = request.session.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_urlsafe(24)
        request.session["csrf_token"] = csrf_token
    base = {
        "request": request,
        "stats": database.stats(),
        "sources": database.list_sources(),
        "categories": database.categories(),
        "csrf_token": csrf_token,
        "is_admin": _is_admin(request),
        "flash": request.session.pop("flash", None),
        "title": "نبض التقنية",
        "description": "منصة عربية ذكية لمتابعة أخبار التقنية والذكاء الاصطناعي.",
        "canonical_url": str(request.url.replace(query="")),
    }
    base.update(values)
    return base


def _is_admin(request: Request) -> bool:
    return request.session.get("is_admin") is True


def _require_admin(request: Request) -> None:
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="تسجيل الدخول مطلوب")


def _verify_csrf(request: Request, submitted: str) -> None:
    expected = request.session.get("csrf_token", "")
    if not expected or not secrets.compare_digest(str(submitted), str(expected)):
        raise HTTPException(status_code=403, detail="رمز الحماية غير صالح")


def _flash(request: Request, message: str, kind: str) -> None:
    request.session["flash"] = {"message": message, "kind": kind}


def _safe_public_url(url: str) -> bool:
    parts = urlsplit(url.strip())
    return bool(
        parts.scheme.casefold() in {"http", "https"}
        and parts.hostname
        and ArticleProcessor._is_safe_article_url(url)
    )


def _run_generation(service: NewsService, limit: int, offline: bool, model: str) -> None:
    try:
        service.sync(limit=limit, offline=offline, model=model)
    finally:
        _generation_lock.release()


app = create_app()
