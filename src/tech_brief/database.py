"""Small SQLite persistence layer for sources, articles, and generation runs."""

import json
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .config import DEFAULT_DATABASE_PATH, DEFAULT_SOURCES
from .models import BriefingItem

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'technology',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_fetched_at TEXT,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_title TEXT NOT NULL,
    headline_ar TEXT NOT NULL,
    summary_ar TEXT NOT NULL,
    summary_en TEXT NOT NULL,
    key_points TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    companies TEXT NOT NULL,
    technologies TEXT NOT NULL,
    confidence REAL NOT NULL,
    link TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    source_id INTEGER,
    category TEXT NOT NULL DEFAULT 'technology',
    published TEXT NOT NULL,
    summarizer TEXT NOT NULL DEFAULT 'openai',
    created_at TEXT NOT NULL,
    FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    fetched INTEGER NOT NULL DEFAULT 0,
    unique_count INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    saved INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    errors TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS locks (
    name TEXT PRIMARY KEY,
    acquired_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str = DEFAULT_DATABASE_PATH) -> None:
        self.path = str(path)

    @contextmanager
    def connect(self):
        db_path = Path(self.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 15000")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            connection.execute("PRAGMA journal_mode = WAL")
            existing = connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            if existing == 0:
                for source in DEFAULT_SOURCES:
                    connection.execute(
                        """INSERT INTO sources (name, url, category, enabled, created_at)
                        VALUES (?, ?, ?, 1, ?)""",
                        (source["name"], source["url"], source["category"], utc_now()),
                    )

    def list_sources(self, enabled_only: bool = False) -> List[Dict[str, object]]:
        where = "WHERE s.enabled = 1" if enabled_only else ""
        with self.connect() as connection:
            rows = connection.execute(
                f"""SELECT s.*, COUNT(a.id) AS article_count
                FROM sources s LEFT JOIN articles a ON a.source_id = s.id
                {where} GROUP BY s.id ORDER BY s.enabled DESC, s.name COLLATE NOCASE"""
            ).fetchall()
        return [dict(row) for row in rows]

    def add_source(self, name: str, url: str, category: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO sources (name, url, category, enabled, created_at)
                VALUES (?, ?, ?, 1, ?)""",
                (name.strip(), url.strip(), category.strip() or "technology", utc_now()),
            )
            return int(cursor.lastrowid)

    def toggle_source(self, source_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE sources SET enabled = CASE enabled WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
                (source_id,),
            )

    def delete_source(self, source_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM sources WHERE id = ?", (source_id,))

    def update_source_result(self, source_id: int, error: Optional[str] = None) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE sources SET last_fetched_at = ?, last_error = ? WHERE id = ?",
                (utc_now(), error, source_id),
            )

    def known_links(self) -> Set[str]:
        with self.connect() as connection:
            rows = connection.execute("SELECT link FROM articles").fetchall()
        return {row["link"] for row in rows}

    def save_item(self, item: BriefingItem, summarizer: str) -> int:
        with self.connect() as connection:
            source = connection.execute(
                "SELECT id FROM sources WHERE name = ? ORDER BY id LIMIT 1",
                (item.source_name,),
            ).fetchone()
            cursor = connection.execute(
                """INSERT INTO articles (
                    original_title, headline_ar, summary_ar, summary_en, key_points,
                    why_it_matters, companies, technologies, confidence, link,
                    source_name, source_id, category, published, summarizer, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    headline_ar = excluded.headline_ar,
                    summary_ar = excluded.summary_ar,
                    summary_en = excluded.summary_en,
                    key_points = excluded.key_points,
                    why_it_matters = excluded.why_it_matters,
                    companies = excluded.companies,
                    technologies = excluded.technologies,
                    confidence = excluded.confidence,
                    summarizer = excluded.summarizer""",
                (
                    item.original_title or item.headline_ar,
                    item.headline_ar,
                    item.summary_ar,
                    item.summary_en,
                    json.dumps(item.key_points, ensure_ascii=False),
                    item.why_it_matters,
                    json.dumps(item.companies, ensure_ascii=False),
                    json.dumps(item.technologies, ensure_ascii=False),
                    item.confidence,
                    item.source_url,
                    item.source_name,
                    source["id"] if source else None,
                    item.category,
                    item.published,
                    summarizer,
                    utc_now(),
                ),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            row = connection.execute(
                "SELECT id FROM articles WHERE link = ?", (item.source_url,)
            ).fetchone()
            return int(row["id"])

    def list_articles(
        self,
        query: str = "",
        category: str = "",
        source_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 9,
    ) -> Tuple[List[Dict[str, object]], int]:
        clauses: List[str] = []
        params: List[object] = []
        if query.strip():
            value = f"%{query.strip()}%"
            clauses.append(
                "(a.headline_ar LIKE ? OR a.original_title LIKE ? OR "
                "a.summary_ar LIKE ? OR a.summary_en LIKE ?)"
            )
            params.extend([value, value, value, value])
        if category:
            clauses.append("a.category = ?")
            params.append(category)
        if source_id:
            clauses.append("a.source_id = ?")
            params.append(source_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        offset = max(page - 1, 0) * per_page

        with self.connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) FROM articles a {where}", params
            ).fetchone()[0]
            rows = connection.execute(
                f"""SELECT a.* FROM articles a {where}
                ORDER BY a.id DESC LIMIT ? OFFSET ?""",
                [*params, per_page, offset],
            ).fetchall()
        return [self._article_dict(row) for row in rows], int(total)

    def get_article(self, article_id: int) -> Optional[Dict[str, object]]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM articles WHERE id = ?", (article_id,)
            ).fetchone()
        return self._article_dict(row) if row else None

    def categories(self) -> List[str]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT category FROM articles ORDER BY category"
            ).fetchall()
        return [row["category"] for row in rows]

    def top_topics(self, limit: int = 8) -> List[Dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT companies, technologies, source_name
                FROM articles ORDER BY id DESC LIMIT 200"""
            ).fetchall()
        topics: Counter = Counter()
        sources: Counter = Counter()
        for row in rows:
            if row["source_name"].strip():
                sources[row["source_name"].strip()] += 1
            for value in self._json_list(row["companies"]):
                if value.strip():
                    topics[value.strip()] += 1
            for value in self._json_list(row["technologies"]):
                if value.strip():
                    topics[value.strip()] += 1
        if not topics:
            topics = sources
        return [
            {"name": name, "count": count}
            for name, count in topics.most_common(max(limit, 0))
        ]

    def stats(self) -> Dict[str, int]:
        with self.connect() as connection:
            article_count = connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            source_count = connection.execute(
                "SELECT COUNT(*) FROM sources WHERE enabled = 1"
            ).fetchone()[0]
            category_count = connection.execute(
                "SELECT COUNT(DISTINCT category) FROM articles"
            ).fetchone()[0]
        return {
            "articles": int(article_count),
            "sources": int(source_count),
            "categories": int(category_count),
        }

    def start_run(self) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO runs (started_at, status) VALUES (?, 'running')", (utc_now(),)
            )
            return int(cursor.lastrowid)

    def acquire_lock(self, name: str, stale_after_seconds: int = 7200) -> bool:
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=stale_after_seconds)).isoformat(
            timespec="seconds"
        )
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM locks WHERE name = ? AND acquired_at < ?", (name, cutoff)
            )
            cursor = connection.execute(
                "INSERT OR IGNORE INTO locks (name, acquired_at) VALUES (?, ?)",
                (name, utc_now()),
            )
            return cursor.rowcount == 1

    def release_lock(self, name: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM locks WHERE name = ?", (name,))

    def finish_run(
        self,
        run_id: int,
        status: str,
        fetched: int,
        unique_count: int,
        skipped: int,
        saved: int,
        errors: Iterable[str],
    ) -> None:
        error_list = list(errors)
        with self.connect() as connection:
            connection.execute(
                """UPDATE runs SET finished_at = ?, status = ?, fetched = ?,
                unique_count = ?, skipped = ?, saved = ?, error_count = ?, errors = ?
                WHERE id = ?""",
                (
                    utc_now(),
                    status,
                    fetched,
                    unique_count,
                    skipped,
                    saved,
                    len(error_list),
                    json.dumps(error_list, ensure_ascii=False),
                    run_id,
                ),
            )

    def list_runs(self, limit: int = 10) -> List[Dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["errors"] = self._json_list(item["errors"])
            result.append(item)
        return result

    @classmethod
    def _article_dict(cls, row: sqlite3.Row) -> Dict[str, object]:
        item = dict(row)
        for key in ("key_points", "companies", "technologies"):
            item[key] = cls._json_list(item[key])
        reading_words = " ".join(
            [
                str(item.get("summary_ar", "")),
                str(item.get("summary_en", "")),
                *[str(point) for point in item["key_points"]],
            ]
        ).split()
        item["reading_minutes"] = max(1, (len(reading_words) + 179) // 180)
        return item

    @staticmethod
    def _json_list(value: str) -> List[str]:
        try:
            decoded = json.loads(value or "[]")
            return decoded if isinstance(decoded, list) else []
        except (TypeError, json.JSONDecodeError):
            return []
