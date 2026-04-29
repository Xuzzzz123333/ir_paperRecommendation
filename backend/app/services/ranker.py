from __future__ import annotations

import re
from functools import lru_cache
from typing import List

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from app.models import Paper


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-]+", (text or "").lower())


def normalize_scores(scores: List[float]) -> List[float]:
    if not scores:
        return []
    array = np.asarray(scores, dtype=float)
    score_min = float(array.min())
    score_max = float(array.max())
    if np.isclose(score_min, score_max):
        if np.isclose(score_max, 0.0):
            return [0.0 for _ in scores]
        return [1.0 for _ in scores]
    normalized = (array - score_min) / (score_max - score_min)
    return normalized.tolist()


def bm25_score(query: str, documents: List[str]) -> List[float]:
    tokenized_docs = [tokenize(document) for document in documents]
    tokenized_query = tokenize(query)
    if not tokenized_query or not any(tokenized_docs):
        return [0.0 for _ in documents]
    engine = BM25Okapi(tokenized_docs)
    scores = engine.get_scores(tokenized_query)
    return normalize_scores(scores.tolist())


@lru_cache(maxsize=4)
def get_embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def dense_score(query: str, documents: List[str], model_name: str) -> List[float]:
    if not documents:
        return []

    model = get_embedding_model(model_name)
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0]
    doc_embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    scores = np.dot(doc_embeddings, query_embedding)
    return normalize_scores(scores.tolist())


def hybrid_rank(
    query: str,
    papers: List[Paper],
    alpha: float,
    model_name: str,
    sort_by: str = "relevance",
) -> List[dict]:
    documents = [
        " ".join(part for part in [paper.title, paper.abstract or ""] if part).strip()
        for paper in papers
    ]
    dense_scores = dense_score(query, documents, model_name)
    bm25_scores = bm25_score(query, documents)

    citation_scores = normalize_scores([float(paper.citation_count or 0) for paper in papers])
    recency_scores = normalize_scores([float(paper.year or 0) for paper in papers])

    ranked_items = []
    for index, paper in enumerate(papers):
        final_score = alpha * dense_scores[index] + (1.0 - alpha) * bm25_scores[index]
        ranked_items.append(
            {
                "paper": paper,
                "final_score": final_score,
                "dense_score": dense_scores[index],
                "bm25_score": bm25_scores[index],
                "citation_tiebreak": citation_scores[index] * 0.08,
                "recency_tiebreak": recency_scores[index] * 0.04,
            }
        )

    if sort_by == "year":
        ranked_items.sort(
            key=lambda item: (
                -(item["final_score"] + item["recency_tiebreak"]),
                -(item["paper"].year or 0),
                -(item["paper"].citation_count or 0),
            )
        )
    elif sort_by == "citation":
        ranked_items.sort(
            key=lambda item: (
                -(item["final_score"] + item["citation_tiebreak"]),
                -(item["paper"].citation_count or 0),
                -(item["paper"].year or 0),
            )
        )
    else:
        ranked_items.sort(
            key=lambda item: (
                -item["final_score"],
                -item["dense_score"],
                -item["bm25_score"],
            )
        )

    return ranked_items
