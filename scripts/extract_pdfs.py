"""
extract_pdfs.py - Extracts page-level text from every PDF listed in
data/raw/metadata.json, preserving page numbers for later citation.
Run: python scripts/extract_pdfs.py
"""

import json
import os
from pathlib import Path
from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
METADATA_PATH = DATA_RAW_DIR / "metadata.json"


def load_metadata() -> list[dict]:
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_pdf_pages(pdf_path: Path) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    pages_data = []
    for i, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ""
        pages_data.append({"page": i + 1, "text": raw_text, "char_count": len(raw_text)})
    return pages_data


def flag_suspicious_pages(pages_data: list[dict], filename: str, min_chars: int = 20) -> list[int]:
    """Flags pages with suspiciously little text - likely scanned
    images with no real text layer (caught DO 174's original broken
    PDF this exact way back in Colab)."""
    suspicious = [p["page"] for p in pages_data if p["char_count"] < min_chars]
    if suspicious:
        print(f"  WARNING: {filename} has {len(suspicious)} suspicious page(s): {suspicious}")
    return suspicious


def process_all_documents() -> None:
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metadata = load_metadata()

    for record in metadata:
        filename = record["filename"]
        pdf_path = DATA_RAW_DIR / filename
        print(f"\nProcessing: {filename}")

        if not pdf_path.exists():
            print(f"  SKIPPED: file not found at {pdf_path}")
            continue

        pages_data = extract_pdf_pages(pdf_path)
        flag_suspicious_pages(pages_data, filename)

        total_chars = sum(p["char_count"] for p in pages_data)
        print(f"  Extracted {len(pages_data)} page(s), {total_chars} total characters.")

        output_filename = filename.replace(".pdf", "_pages.json")
        output_path = DATA_PROCESSED_DIR / output_filename
        output_data = {
            "source_filename": filename,
            "title": record["title"],
            "law_number": record["law_number"],
            "category": record["category"],
            "pages": pages_data,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {output_path.name}")

    print(f"\n{'=' * 50}")
    processed_count = len(list(DATA_PROCESSED_DIR.glob("*_pages.json")))
    print(f"Total documents processed: {processed_count}/{len(metadata)}")


if __name__ == "__main__":
    process_all_documents()