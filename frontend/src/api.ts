export type SourceName = "arxiv" | "openalex" | "semantic_scholar";
export type SortOption = "relevance" | "year" | "citation";

export interface StructuredSummary {
  research_problem: string;
  core_method: string;
  main_contribution: string;
  experimental_evidence: string;
  limitations: string;
  why_recommended: string;
}

export interface Paper {
  id?: string | null;
  title: string;
  authors: string[];
  abstract?: string | null;
  year?: number | null;
  venue?: string | null;
  source: string;
  url?: string | null;
  pdf_url?: string | null;
  citation_count?: number | null;
  published_at?: string | null;
}

export interface RecommendedPaper extends Paper {
  rank: number;
  final_score: number;
  dense_score: number;
  bm25_score: number;
  recommendation_reason: string;
  structured_summary: StructuredSummary;
}

export interface RecommendRequest {
  query: string;
  max_results: number;
  source: SourceName;
  alpha: number;
  year_from?: number;
  year_to?: number;
  sort_by: SortOption;
  model_name?: string;
}

export interface RecommendResponse {
  query: string;
  source: string;
  count: number;
  alpha: number;
  papers: RecommendedPaper[];
  message: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  message: string;
}

export interface SourcesResponse {
  sources: SourceName[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = "Request failed.";
    try {
      const data = await response.json();
      detail = data.detail ?? data.message ?? detail;
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function healthCheck() {
  return requestJson<HealthResponse>("/api/health");
}

export function fetchSources() {
  return requestJson<SourcesResponse>("/api/sources");
}

export function recommendPapers(payload: RecommendRequest) {
  return requestJson<RecommendResponse>("/api/papers/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function clearCache() {
  return requestJson<{ status: string; message: string }>("/api/cache", {
    method: "DELETE",
  });
}
