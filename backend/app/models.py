from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


SourceName = Literal["arxiv", "openalex", "semantic_scholar"]
SortOption = Literal["relevance", "year", "citation"]


class HealthResponse(BaseModel):
    status: str
    service: str
    message: str


class Paper(BaseModel):
    id: Optional[str] = None
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    source: str
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: Optional[int] = None
    published_at: Optional[str] = None


class PaperSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Research topic or natural language query.")
    max_results: int = Field(default=20, ge=1, le=50)
    year_from: Optional[int] = Field(default=None, ge=1900, le=2100)
    year_to: Optional[int] = Field(default=None, ge=1900, le=2100)
    source: SourceName = "arxiv"
    sort_by: SortOption = "relevance"


class PaperSearchResponse(BaseModel):
    query: str
    source: str
    count: int
    papers: List[Paper]
    message: str = ""


class PaperRecommendationRequest(BaseModel):
    query: str = Field(..., min_length=2)
    max_results: int = Field(default=20, ge=1, le=50)
    source: SourceName = "arxiv"
    alpha: float = Field(default=0.65, ge=0.0, le=1.0)
    year_from: Optional[int] = Field(default=None, ge=1900, le=2100)
    year_to: Optional[int] = Field(default=None, ge=1900, le=2100)
    sort_by: SortOption = "relevance"
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


class StructuredSummary(BaseModel):
    research_problem: str
    core_method: str
    main_contribution: str
    experimental_evidence: str
    limitations: str
    why_recommended: str


class RecommendedPaper(Paper):
    rank: int
    final_score: float
    dense_score: float
    bm25_score: float
    recommendation_reason: str
    structured_summary: StructuredSummary


class PaperRecommendationResponse(BaseModel):
    query: str
    source: str
    count: int
    alpha: float
    papers: List[RecommendedPaper]
    message: str = ""


class PaperAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=2)
    paper: Paper


class SourcesResponse(BaseModel):
    sources: List[SourceName]


class CacheClearResponse(BaseModel):
    status: str
    message: str
