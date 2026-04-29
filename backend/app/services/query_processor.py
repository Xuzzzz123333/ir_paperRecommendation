from __future__ import annotations

import re
from typing import Optional


def normalize_query(query: str) -> str:
    return " ".join(query.strip().split())


def validate_year_range(year_from: Optional[int], year_to: Optional[int]) -> None:
    if year_from and year_to and year_from > year_to:
        raise ValueError("year_from cannot be greater than year_to.")


def tokenize_query(query: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-]+", query.lower())


def build_arxiv_query(query: str) -> str:
    terms = tokenize_query(query)
    if not terms:
        return f'all:{normalize_query(query)}'

    return " OR ".join(f"all:{term}" for term in terms)
