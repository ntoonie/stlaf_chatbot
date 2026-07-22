"""
debug_paternity_maternity.py - Isolates WHICH half of hybrid search
(dense/BGE-M3 or BM25/full-text) is responsible for Expanded Maternity
Leave Law outranking Paternity Leave Act on:
  "Ilang araw ang paternity leave na pwedeng makuha ng ama?"
despite the equivalent English question working correctly.

Uses hybrid_search_law_chunks's own full_text_weight/semantic_weight
parameters to isolate each method - no new SQL needed.

Run: python scripts/debug_paternity_maternity.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from sentence_transformers import SentenceTransformer
from supabase_client import get_supabase_admin_client

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

QUESTION = "Ilang araw ang paternity leave na pwedeng makuha ng ama?"

# Isolation runs: same question, different weight combinations
WEIGHT_VARIANTS = [
    ("HYBRID (both weights=1, default - reproduces the bug)", 1, 1),
    ("DENSE ONLY (full_text_weight=0)", 0, 1),
    ("BM25 ONLY (semantic_weight=0)", 1, 0),
]

# Phrasing variants - same underlying question, varying how much
# "ama"/male-specific signal is present, to find the tipping point
PHRASING_VARIANTS = [
    "Ilang araw ang paternity leave na pwedeng makuha ng ama?",
    "Ilang araw ang paternity leave?",
    "Ama, ilang araw ang leave mo bilang bagong tatay?",
    "paternity leave ama",
]


def run_query(client, model, question, full_text_weight, semantic_weight, match_count=4):
    query_embedding = model.encode([question], normalize_embeddings=True).tolist()[0]
    response = client.rpc(
        "hybrid_search_law_chunks",
        {
            "query_text": question,
            "query_embedding": query_embedding,
            "match_count": match_count,
            "full_text_weight": full_text_weight,
            "semantic_weight": semantic_weight,
        },
    ).execute()
    return response.data


def main() -> None:
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("Connecting to Supabase...")
    client = get_supabase_admin_client()
    print()

    # ============================================================
    # PART 1: Isolate which method is responsible
    # ============================================================
    print("#" * 70)
    print("PART 1: ISOLATING DENSE vs BM25")
    print(f"QUESTION: {QUESTION}")
    print("#" * 70)

    for label, ftw, sw in WEIGHT_VARIANTS:
        print()
        print("=" * 70)
        print(label)
        print("=" * 70)
        rows = run_query(client, model, QUESTION, ftw, sw)
        for i, row in enumerate(rows):
            print(f"  [{i + 1}] rrf_score={row['rrf_score']:.5f}  {row['title']} (p.{row['start_page']})")

    # ============================================================
    # PART 2: Find the phrasing tipping point
    # ============================================================
    print()
    print("#" * 70)
    print("PART 2: PHRASING VARIANTS (default hybrid weights)")
    print("#" * 70)

    for question in PHRASING_VARIANTS:
        print()
        print("=" * 70)
        print(f"QUERY: {question}")
        print("=" * 70)
        rows = run_query(client, model, question, 1, 1)
        for i, row in enumerate(rows):
            print(f"  [{i + 1}] rrf_score={row['rrf_score']:.5f}  {row['title']} (p.{row['start_page']})")

    print()
    print("#" * 70)
    print("READ THIS:")
    print("  - Part 1 tells you WHICH method (dense, BM25, or both) ranks")
    print("    maternity leave above paternity leave for this exact query.")
    print("  - Part 2 tells you whether ANY amount of rephrasing fixes it,")
    print("    or whether the confusion is deeper than phrasing alone.")
    print("#" * 70)


if __name__ == "__main__":
    main()