from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import httpx

from app.models import Paper
from app.services.query_processor import build_arxiv_query


ARXIV_API_URL = "https://export.arxiv.org/api/query"
OPENALEX_API_URL = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SUPPORTED_SOURCES = ["arxiv", "openalex", "semantic_scholar"]
ARXIV_PAGE_SIZE = 10


class PaperSourceError(Exception):
    """Raised when an upstream academic source fails."""


def search_papers(
    query: str,
    max_results: int,
    source: str,
    filters: Optional[Dict[str, Optional[int]]] = None,
    sort_by: str = "relevance",
) -> List[Paper]:
    filters = filters or {}
    source = source.lower()
    if source not in SUPPORTED_SOURCES:
        raise PaperSourceError(f"Unsupported paper source: {source}")

    if source == "arxiv":
        papers = _search_arxiv(query, max_results, filters, sort_by)
    elif source == "openalex":
        papers = _search_openalex(query, max_results, filters, sort_by)
    else:
        papers = _search_semantic_scholar(query, max_results, filters, sort_by)

    return _deduplicate_papers(papers)


def _search_arxiv(
    query: str,
    max_results: int,
    filters: Dict[str, Optional[int]],
    sort_by: str,
) -> List[Paper]:
    sort_mapping = {
        "relevance": "relevance",
        "year": "submittedDate",
        "citation": "relevance",
    }
    headers = {"User-Agent": "paper-recommender-demo/1.0"}
    papers: List[Paper] = []
    search_query = build_arxiv_query(query)
    timeout = httpx.Timeout(connect=10.0, read=45.0, write=30.0, pool=30.0)
    page_size = min(max_results, ARXIV_PAGE_SIZE)

    for start in range(0, max_results, page_size):
        batch_size = min(page_size, max_results - start)
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": batch_size,
            "sortBy": sort_mapping.get(sort_by, "relevance"),
            "sortOrder": "descending",
        }
        response = _request_with_retries(
            ARXIV_API_URL,
            params=params,
            headers=headers,
            source_name="arXiv",
            retries=4,
            timeout=timeout,
        )
        batch = _parse_arxiv_entries(response.text, filters)
        papers.extend(batch)

        # Stop early when arXiv has no more results to return for later pages.
        if len(batch) < batch_size:
            break

    return papers[:max_results]


def _parse_arxiv_entries(xml_text: str, filters: Dict[str, Optional[int]]) -> List[Paper]:
    namespace = {"atom": "http://www.w3.org/2005/Atom"}

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise PaperSourceError("Failed to parse arXiv response.") from exc

    papers: List[Paper] = []
    for entry in root.findall("atom:entry", namespace):
        title = _clean_text(entry.findtext("atom:title", default="", namespaces=namespace))
        abstract = _clean_text(entry.findtext("atom:summary", default="", namespaces=namespace))
        published = entry.findtext("atom:published", default="", namespaces=namespace)
        year = int(published[:4]) if published[:4].isdigit() else None
        if filters.get("year_from") and year and year < int(filters["year_from"]):
            continue
        if filters.get("year_to") and year and year > int(filters["year_to"]):
            continue

        authors = [
            _clean_text(author.findtext("atom:name", default="", namespaces=namespace))
            for author in entry.findall("atom:author", namespace)
        ]
        url = entry.findtext("atom:id", default="", namespaces=namespace) or None
        pdf_url = None
        for link in entry.findall("atom:link", namespace):
            href = link.attrib.get("href")
            title_attr = link.attrib.get("title")
            if title_attr == "pdf" and href:
                pdf_url = href
                break
        if not pdf_url and url and "/abs/" in url:
            pdf_url = url.replace("/abs/", "/pdf/") + ".pdf"

        papers.append(
            Paper(
                id=url,
                title=title,
                authors=[author for author in authors if author],
                abstract=abstract,
                year=year,
                venue="arXiv",
                source="arxiv",
                url=url,
                pdf_url=pdf_url,
                citation_count=None,
                published_at=published or None,
            )
        )

    return papers


def _search_openalex(
    query: str,
    max_results: int,
    filters: Dict[str, Optional[int]],
    sort_by: str,
) -> List[Paper]:
    params = {
        "search": query,
        "per-page": max_results,
        "sort": {
            "relevance": "relevance_score:desc",
            "year": "publication_year:desc",
            "citation": "cited_by_count:desc",
        }.get(sort_by, "relevance_score:desc"),
    }
    filter_items = []
    if filters.get("year_from"):
        filter_items.append(f"from_publication_date:{int(filters['year_from'])}-01-01")
    if filters.get("year_to"):
        filter_items.append(f"to_publication_date:{int(filters['year_to'])}-12-31")
    if filter_items:
        params["filter"] = ",".join(filter_items)

    response = _request_with_retries(OPENALEX_API_URL, params=params, source_name="OpenAlex")

    data = response.json()
    works = data.get("results", [])
    papers: List[Paper] = []
    for work in works:
        authors = [
            author.get("author", {}).get("display_name", "")
            for author in work.get("authorships", [])
        ]
        abstract = _reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
        open_access = work.get("open_access", {}) or {}
        primary_location = work.get("primary_location", {}) or {}
        primary_source = primary_location.get("source") or {}
        papers.append(
            Paper(
                id=work.get("id"),
                title=_clean_text(work.get("display_name", "")),
                authors=[author for author in authors if author],
                abstract=abstract,
                year=work.get("publication_year"),
                venue=primary_source.get("display_name"),
                source="openalex",
                url=primary_location.get("landing_page_url") or work.get("id"),
                pdf_url=open_access.get("oa_url"),
                citation_count=work.get("cited_by_count"),
                published_at=None,
            )
        )

    return papers


def _search_semantic_scholar(
    query: str,
    max_results: int,
    filters: Dict[str, Optional[int]],
    sort_by: str,
) -> List[Paper]:
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,abstract,year,url,venue,citationCount,openAccessPdf",
    }

    response = _request_with_retries(
        SEMANTIC_SCHOLAR_API_URL,
        params=params,
        source_name="Semantic Scholar",
    )

    data = response.json()
    items = data.get("data", [])
    papers: List[Paper] = []
    for item in items:
        year = item.get("year")
        if filters.get("year_from") and year and year < int(filters["year_from"]):
            continue
        if filters.get("year_to") and year and year > int(filters["year_to"]):
            continue
        authors = [author.get("name", "") for author in item.get("authors", [])]
        pdf_info = item.get("openAccessPdf") or {}
        papers.append(
            Paper(
                id=item.get("paperId"),
                title=_clean_text(item.get("title", "")),
                authors=[author for author in authors if author],
                abstract=_clean_text(item.get("abstract", "")),
                year=year,
                venue=item.get("venue"),
                source="semantic_scholar",
                url=item.get("url"),
                pdf_url=pdf_info.get("url"),
                citation_count=item.get("citationCount"),
                published_at=None,
            )
        )

    if sort_by == "year":
        papers.sort(key=lambda paper: (paper.year or 0, paper.citation_count or 0), reverse=True)
    elif sort_by == "citation":
        papers.sort(key=lambda paper: (paper.citation_count or 0, paper.year or 0), reverse=True)

    return papers


def _deduplicate_papers(papers: List[Paper]) -> List[Paper]:
    seen = set()
    deduplicated = []
    for paper in papers:
        key = (_clean_text(paper.title).lower(), tuple(paper.authors[:3]), paper.year)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(paper)
    return deduplicated


def _clean_text(text: Optional[str]) -> str:
    return " ".join((text or "").split())


def _reconstruct_openalex_abstract(inverted_index: Optional[dict]) -> Optional[str]:
    if not inverted_index:
        return None
    token_positions = []
    for token, positions in inverted_index.items():
        for position in positions:
            token_positions.append((position, token))
    token_positions.sort(key=lambda item: item[0])
    return " ".join(token for _, token in token_positions)


def _request_with_retries(
    url: str,
    params: dict,
    source_name: str,
    headers: Optional[dict] = None,
    retries: int = 3,
    timeout: Optional[httpx.Timeout] = None,
) -> httpx.Response:
    last_error: Optional[Exception] = None
    timeout = timeout or httpx.Timeout(connect=10.0, read=20.0, write=20.0, pool=20.0)

    for attempt in range(retries):
        try:
            response = httpx.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            break
        except httpx.HTTPError as exc:
            last_error = exc
            status_code = getattr(exc.response, "status_code", None) if getattr(exc, "response", None) is not None else None
            if status_code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            break

    if isinstance(last_error, httpx.TimeoutException):
        raise PaperSourceError(
            f"{source_name} request timed out after {timeout.read} seconds. "
            "Please retry, reduce max_results, or switch to openalex temporarily."
        ) from last_error

    raise PaperSourceError(f"{source_name} request failed: {last_error}") from last_error
