from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from app.models import Paper


DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "paper_cache.sqlite"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_cache() -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_cache (
                cache_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                query TEXT NOT NULL,
                year_from INTEGER,
                year_to INTEGER,
                max_results INTEGER NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def make_cache_key(
    query: str,
    source: str,
    max_results: int,
    year_from: Optional[int],
    year_to: Optional[int],
    sort_by: str,
) -> str:
    normalized = " ".join(query.strip().lower().split())
    return f"{source}|{normalized}|{max_results}|{year_from or ''}|{year_to or ''}|{sort_by}"


def get_cached_search(
    query: str,
    source: str,
    max_results: int,
    year_from: Optional[int],
    year_to: Optional[int],
    sort_by: str,
) -> Optional[List[Paper]]:
    init_cache()
    cache_key = make_cache_key(query, source, max_results, year_from, year_to, sort_by)
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT payload FROM search_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    if not row:
        return None

    payload = json.loads(row[0])
    return [Paper(**item) for item in payload]


def set_cached_search(
    query: str,
    source: str,
    max_results: int,
    year_from: Optional[int],
    year_to: Optional[int],
    sort_by: str,
    papers: List[Paper],
) -> None:
    init_cache()
    cache_key = make_cache_key(query, source, max_results, year_from, year_to, sort_by)
    payload = json.dumps([paper.model_dump() for paper in papers], ensure_ascii=False)
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO search_cache (cache_key, source, query, year_from, year_to, max_results, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload = excluded.payload,
                updated_at = CURRENT_TIMESTAMP
            """,
            (cache_key, source, query, year_from, year_to, max_results, payload),
        )
        conn.commit()


def clear_cache() -> None:
    init_cache()
    with _get_connection() as conn:
        conn.execute("DELETE FROM search_cache")
        conn.commit()
