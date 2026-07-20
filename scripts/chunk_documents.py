"""
chunk_documents.py - Splits extracted page text into legal-structure-
aware chunks (Article/Section boundaries), with a size-based fallback
for oversized pieces. Run: python scripts/chunk_documents.py
"""

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MAX_CHUNK_CHARS = 800
CHUNK_OVERLAP_CHARS = 100

LEGAL_HEADING_PATTERN = re.compile(
    r"^\s*((?:ART(?:ICLE)?|SEC(?:TION)?)\.?\s*\d+[A-Za-z\-]*\.)",
    re.MULTILINE | re.IGNORECASE,
)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_filename: str
    title: str
    law_number: str
    category: str
    start_page: int
    end_page: int
    char_count: int


def remove_boilerplate_lines(pages: list[dict], min_frequency_ratio: float = 0.5) -> list[dict]:
    total_pages = len(pages)
    line_counts: dict[str, int] = {}
    for page in pages:
        lines_on_page = {line.strip() for line in page["text"].split("\n") if line.strip()}
        for line in lines_on_page:
            line_counts[line] = line_counts.get(line, 0) + 1
    threshold = max(3, int(total_pages * min_frequency_ratio))
    boilerplate = {line for line, count in line_counts.items() if count >= threshold}

    cleaned = []
    for page in pages:
        kept = [l for l in page["text"].split("\n") if l.strip() not in boilerplate]
        cleaned.append({**page, "text": "\n".join(kept)})
    return cleaned


def fix_hyphenated_linebreaks(text: str) -> str:
    return re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)


def build_full_text_with_page_map(pages: list[dict]) -> tuple[str, list[tuple[int, int, int]]]:
    parts, page_map = [], []
    cursor = 0
    for page in pages:
        cleaned = fix_hyphenated_linebreaks(page["text"])
        start = cursor
        parts.append(cleaned)
        cursor += len(cleaned)
        page_map.append((start, cursor, page["page"]))
        parts.append("\n")
        cursor += 1
    return "".join(parts), page_map


def find_page_for_offset(offset: int, page_map: list[tuple[int, int, int]]) -> int:
    for start, end, page_num in page_map:
        if start <= offset < end:
            return page_num
    return page_map[-1][2] if page_map else 1


def split_by_legal_structure(full_text: str) -> list[tuple[int, str]]:
    matches = list(LEGAL_HEADING_PATTERN.finditer(full_text))
    if len(matches) < 2:
        return [(0, full_text)]
    pieces = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        text = full_text[start:end].strip()
        if text:
            pieces.append((start, text))
    return pieces


def enforce_max_chunk_size(pieces: list[tuple[int, str]], max_chars: int, overlap: int) -> list[tuple[int, str]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars, chunk_overlap=overlap, separators=["\n\n", "\n", ". ", " ", ""],
    )
    final = []
    for start_offset, text in pieces:
        if len(text) <= max_chars:
            final.append((start_offset, text))
            continue
        sub_pieces = splitter.split_text(text)
        cursor = 0
        for sub in sub_pieces:
            pos = text.find(sub, max(0, cursor - overlap))
            abs_offset = start_offset + (pos if pos != -1 else 0)
            final.append((abs_offset, sub))
            cursor = pos + len(sub) if pos != -1 else cursor
    return final


def process_document_into_chunks(pages_json_path: Path) -> list[Chunk]:
    with open(pages_json_path, "r", encoding="utf-8") as f:
        doc_data = json.load(f)

    cleaned_pages = remove_boilerplate_lines(doc_data["pages"])
    full_text, page_map = build_full_text_with_page_map(cleaned_pages)
    structural_pieces = split_by_legal_structure(full_text)
    final_pieces = enforce_max_chunk_size(structural_pieces, MAX_CHUNK_CHARS, CHUNK_OVERLAP_CHARS)

    chunks = []
    for i, (offset, text) in enumerate(final_pieces):
        start_page = find_page_for_offset(offset, page_map)
        end_page = find_page_for_offset(min(offset + len(text), len(full_text) - 1), page_map)
        chunks.append(Chunk(
            chunk_id=f"{doc_data['source_filename']}_{i:04d}",
            text=text,
            source_filename=doc_data["source_filename"],
            title=doc_data["title"],
            law_number=doc_data["law_number"],
            category=doc_data["category"],
            start_page=start_page,
            end_page=end_page,
            char_count=len(text),
        ))
    return chunks


def process_all_documents() -> None:
    all_chunks: list[Chunk] = []
    pages_files = sorted(DATA_PROCESSED_DIR.glob("*_pages.json"))

    for pages_path in pages_files:
        print(f"Chunking: {pages_path.name}")
        doc_chunks = process_document_into_chunks(pages_path)
        print(f"    -> {len(doc_chunks)} chunk(s) produced.")
        all_chunks.extend(doc_chunks)

    output_path = DATA_PROCESSED_DIR / "chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in all_chunks], f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_chunks)} total chunks to {output_path.name}")


if __name__ == "__main__":
    process_all_documents()