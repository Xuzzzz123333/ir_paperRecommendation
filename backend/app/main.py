from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    CacheClearResponse,
    HealthResponse,
    PaperAnalyzeRequest,
    PaperRecommendationRequest,
    PaperRecommendationResponse,
    PaperSearchRequest,
    PaperSearchResponse,
    RecommendedPaper,
    SourcesResponse,
)
from app.services.cache import clear_cache, get_cached_search, init_cache, set_cached_search
from app.services.paper_sources import PaperSourceError, SUPPORTED_SOURCES, search_papers
from app.services.query_processor import normalize_query, validate_year_range
from app.services.ranker import hybrid_rank
from app.services.summarizer import build_structured_summary


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_cache()
    yield


app = FastAPI(
    title="Paper Recommender Demo API",
    version="1.0.0",
    description="Automatic academic paper search, recommendation, and structured abstract analysis.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_or_fetch_candidates(request: PaperSearchRequest):
    cached = get_cached_search(
        query=request.query,
        source=request.source,
        max_results=request.max_results,
        year_from=request.year_from,
        year_to=request.year_to,
        sort_by=request.sort_by,
    )
    if cached is not None:
        return cached

    papers = search_papers(
        query=request.query,
        max_results=request.max_results,
        source=request.source,
        filters={"year_from": request.year_from, "year_to": request.year_to},
        sort_by=request.sort_by,
    )
    set_cached_search(
        query=request.query,
        source=request.source,
        max_results=request.max_results,
        year_from=request.year_from,
        year_to=request.year_to,
        sort_by=request.sort_by,
        papers=papers,
    )
    return papers


def _paper_source_status_code(error: PaperSourceError) -> int:
    if "timed out" in str(error).lower():
        return 504
    return 502


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="paper-recommender-demo-backend",
        message="Backend service is running.",
    )


@app.get("/api/sources", response_model=SourcesResponse)
def get_sources() -> SourcesResponse:
    return SourcesResponse(sources=SUPPORTED_SOURCES)


@app.post("/api/papers/search", response_model=PaperSearchResponse)
def paper_search(request: PaperSearchRequest) -> PaperSearchResponse:
    request.query = normalize_query(request.query)
    try:
        validate_year_range(request.year_from, request.year_to)
        papers = _load_or_fetch_candidates(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PaperSourceError as exc:
        raise HTTPException(status_code=_paper_source_status_code(exc), detail=str(exc)) from exc

    message = "No papers were found for this query." if not papers else "Candidate papers fetched successfully."
    return PaperSearchResponse(
        query=request.query,
        source=request.source,
        count=len(papers),
        papers=papers,
        message=message,
    )


@app.post("/api/papers/recommend", response_model=PaperRecommendationResponse)
def paper_recommend(request: PaperRecommendationRequest) -> PaperRecommendationResponse:
    normalized_query = normalize_query(request.query)
    search_request = PaperSearchRequest(
        query=normalized_query,
        max_results=request.max_results,
        year_from=request.year_from,
        year_to=request.year_to,
        source=request.source,
        sort_by=request.sort_by,
    )
    try:
        validate_year_range(request.year_from, request.year_to)
        candidates = _load_or_fetch_candidates(search_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PaperSourceError as exc:
        raise HTTPException(status_code=_paper_source_status_code(exc), detail=str(exc)) from exc

    if not candidates:
        return PaperRecommendationResponse(
            query=normalized_query,
            source=request.source,
            count=0,
            alpha=request.alpha,
            papers=[],
            message="No candidate papers were found.",
        )

    ranked_items = hybrid_rank(
        query=normalized_query,
        papers=candidates,
        alpha=request.alpha,
        model_name=request.model_name,
        sort_by=request.sort_by,
    )

    recommended = []
    for rank, item in enumerate(ranked_items, start=1):
        paper = item["paper"]
        structured = build_structured_summary(normalized_query, paper)
        recommended.append(
            RecommendedPaper(
                **paper.model_dump(),
                rank=rank,
                final_score=round(float(item["final_score"]), 4),
                dense_score=round(float(item["dense_score"]), 4),
                bm25_score=round(float(item["bm25_score"]), 4),
                recommendation_reason=structured.why_recommended,
                structured_summary=structured,
            )
        )

    return PaperRecommendationResponse(
        query=normalized_query,
        source=request.source,
        count=len(recommended),
        alpha=request.alpha,
        papers=recommended,
        message="Recommendation ranking completed.",
    )


@app.post("/api/papers/analyze")
def analyze_paper(request: PaperAnalyzeRequest):
    summary = build_structured_summary(normalize_query(request.query), request.paper)
    return summary


@app.delete("/api/cache", response_model=CacheClearResponse)
def delete_cache() -> CacheClearResponse:
    clear_cache()
    return CacheClearResponse(status="ok", message="Local metadata cache cleared.")
