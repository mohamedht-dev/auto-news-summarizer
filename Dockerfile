FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TECH_BRIEF_DB=/app/data/tech_brief.db

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --no-cache-dir . \
    && mkdir -p /app/data \
    && chown -R app:app /app

USER app
EXPOSE 8000
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["sh", "-c", "if [ \"${TECH_BRIEF_SYNC_ON_START:-0}\" = \"1\" ]; then tech-brief sync --offline --limit \"${TECH_BRIEF_STARTUP_LIMIT:-8}\" || true; fi; exec tech-brief serve --host 0.0.0.0 --port \"${PORT:-8000}\""]
