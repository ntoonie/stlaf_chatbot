"""
check_missing_documents.py - Direct existence check for documents that
never appeared across dedicated test_corpus_coverage.py queries aimed
specifically at them: Magna Carta for Disabled Persons (RA 9442 /
10754), 2011 NLRC Rules of Procedure, and RA 11641 (Department of
Migrant Workers Act). Same diagnostic pattern as the earlier confirmed
paternity_leave_act.pdf gap - settle "not indexed" vs "indexed but
losing every ranking" before guessing which one it is.

Run: python scripts/check_missing_documents.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from supabase_client import get_supabase_admin_client

# Filenames as they'd appear in source_filename - adjust if your
# actual filenames differ (check against data/raw/metadata.json).
SUSPECT_FILES = [
    "RA 9442.pdf",
    "RA 10754.pdf",
    "2011 - NLRC.pdf",
    "RA 11641.pdf",
]


def main() -> None:
    print("Connecting to Supabase...")
    client = get_supabase_admin_client()

    total_count = client.table("law_chunks").select("chunk_id", count="exact").execute().count
    print(f"Table has {total_count} indexed chunks total.\n")

    for filename in SUSPECT_FILES:
        result = (
            client.table("law_chunks")
            .select("chunk_id, title, start_page", count="exact")
            .eq("source_filename", filename)
            .limit(3)
            .execute()
        )
        print("=" * 70)
        print(f"FILE: {filename}")
        print("=" * 70)
        if result.count and result.count > 0:
            print(f"FOUND: {result.count} chunk(s) indexed.")
            print("Sample titles/pages:")
            for row in result.data:
                print(f"  - {row['title']} (p.{row['start_page']})")
        else:
            print("NOT FOUND: zero chunks with this source_filename.")
            print("Check data/raw/metadata.json - either this file was never")
            print("listed there, or the filename doesn't match exactly.")
        print()

    print("=" * 70)
    print("If a file shows FOUND but still never wins in test_corpus_coverage.py,")
    print("that's a genuine RANKING problem (content exists, isn't surfacing).")
    print("If it shows NOT FOUND, that's an INGESTION gap - check metadata.json,")
    print("then re-run extract_pdfs.py -> chunk_documents.py -> generate_embeddings.py")
    print("-> build_vector_db.py, same as the paternity_leave_act.pdf fix earlier.")


if __name__ == "__main__":
    main()