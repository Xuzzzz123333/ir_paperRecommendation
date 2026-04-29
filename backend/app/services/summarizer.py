from __future__ import annotations

import re
from typing import Iterable, List

from app.models import Paper, StructuredSummary
from app.services.query_processor import tokenize_query


DEFAULT_SENTENCE = "Not clearly stated in the abstract."

PROBLEM_KEYWORDS = ["problem", "challenge", "task", "aim", "objective", "question", "address", "focus"]
METHOD_KEYWORDS = ["propose", "present", "introduce", "method", "approach", "framework", "model", "architecture"]
CONTRIBUTION_KEYWORDS = ["contribution", "contributions", "show", "demonstrate", "achieve", "outperform", "improve"]
EVIDENCE_KEYWORDS = ["experiment", "evaluation", "results", "benchmark", "dataset", "analysis", "evidence"]
LIMITATION_KEYWORDS = ["however", "but", "limitation", "future work", "although", "yet", "challenge"]


def split_sentences(text: str) -> List[str]:
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [part.strip() for part in parts if part.strip()]


def _keyword_overlap(sentence: str, keywords: Iterable[str]) -> int:
    lowered = sentence.lower()
    return sum(1 for keyword in keywords if keyword in lowered)


def _select_sentence(sentences: List[str], keywords: Iterable[str]) -> str:
    if not sentences:
        return DEFAULT_SENTENCE

    scored = []
    for sentence in sentences:
        score = _keyword_overlap(sentence, keywords)
        if sentence.lower().startswith(("we ", "this paper", "our ")):
            score += 0.5
        score += min(len(sentence) / 200.0, 0.5)
        scored.append((score, sentence))

    best_score, best_sentence = max(scored, key=lambda item: item[0])
    if best_score <= 0.6:
        return sentences[0]
    return best_sentence


def extract_research_problem(text: str) -> str:
    return _select_sentence(split_sentences(text), PROBLEM_KEYWORDS)


def extract_method(text: str) -> str:
    return _select_sentence(split_sentences(text), METHOD_KEYWORDS)


def extract_contribution(text: str) -> str:
    return _select_sentence(split_sentences(text), CONTRIBUTION_KEYWORDS)


def extract_evidence(text: str) -> str:
    return _select_sentence(split_sentences(text), EVIDENCE_KEYWORDS)


def extract_limitation(text: str) -> str:
    sentences = split_sentences(text)
    candidate = _select_sentence(sentences, LIMITATION_KEYWORDS)
    if candidate == sentences[0] if sentences else False:
        return "The abstract does not explicitly discuss limitations; this is a likely gap for deeper reading."
    return candidate


def build_recommendation_reason(query: str, paper: Paper) -> str:
    query_terms = set(tokenize_query(query))
    text = f"{paper.title} {paper.abstract or ''}".lower()
    matched = [term for term in query_terms if term in text]
    if matched:
        return (
            f"This paper is recommended because it directly overlaps with the query terms "
            f"{', '.join(matched[:5])} and its abstract indicates strong topical relevance."
        )
    return "This paper is recommended because the title and abstract are semantically close to the query."


def build_structured_summary(query: str, paper: Paper) -> StructuredSummary:
    abstract = paper.abstract or ""
    return StructuredSummary(
        research_problem=extract_research_problem(abstract),
        core_method=extract_method(abstract),
        main_contribution=extract_contribution(abstract),
        experimental_evidence=extract_evidence(abstract),
        limitations=extract_limitation(abstract),
        why_recommended=build_recommendation_reason(query, paper),
    )
