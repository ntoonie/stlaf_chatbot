"""
rag_utils.py - Pure, testable helper functions with no GPU, LLM, or
database dependency. Safe to unit test directly.
"""

import re

REFUSAL_MESSAGE = (
    "I could not find information about this in the Philippine labor "
    "law documents I have access to."
)

CITATION_PATTERN = re.compile(r"\(Source:\s*[^,]+,\s*pp?\.\s*\d+(-\d+)?\)")


def format_page_reference(start_page: int, end_page: int) -> str:
    """Format a page range as 'p.X' (single page) or 'pp.X-Y' (multi-page)."""
    if start_page == end_page:
        return f"p.{start_page}"
    return f"pp.{start_page}-{end_page}"


def fix_hyphenated_linebreaks(text: str) -> str:
    """Rejoin words split across a hyphenated line break during PDF extraction."""
    return re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)


def format_retrieved_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into labeled context blocks for the LLM prompt."""
    if not chunks:
        return "(No relevant context was retrieved.)"
    blocks = []
    for chunk in chunks:
        page_ref = format_page_reference(chunk["start_page"], chunk["end_page"])
        block = f"[Source: {chunk['title']}, {page_ref}]\n\"{chunk['text']}\""
        blocks.append(block)
    return "\n\n".join(blocks)


def contains_citation(answer_text: str) -> bool:
    """Check whether generated text contains a citation-shaped pattern."""
    return bool(CITATION_PATTERN.search(answer_text))


def is_refusal(answer_text: str) -> bool:
    """Check whether generated text IS the exact refusal message."""
    return answer_text.strip() == REFUSAL_MESSAGE


def passes_distance_threshold(distances: list[float], threshold: float) -> bool:
    """Given a list of distances, check whether the BEST (lowest) one
    passes the confidence threshold."""
    if not distances:
        return False
    return min(distances) <= threshold