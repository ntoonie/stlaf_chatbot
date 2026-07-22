"""
test_retrieval.py - Manually inspect HYBRID retrieval quality (BM25
full-text + dense vector, fused via RRF) against pgvector/Supabase,
without needing the FastAPI server, auth, or a real Claude call.
Prints RAW rrf_score (no threshold filtering) so you can pick a real
min_score_threshold for pipeline.py based on actual output.

IMPORTANT: rrf_score is HIGHER = better, opposite direction from the
old distance-based version, and on a completely different numeric
scale (roughly 0.008-0.033 for typical rank positions, not ~0.3-0.9).

Run: python scripts/test_retrieval.py
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
TOP_K = 4

TEST_QUERIES = [
    # --- Known-good baseline ---
    "What are the requirements for maternity leave?",
    "How is 13th month pay computed?",

    # --- Known-bad baseline (the "broad question" bug) - the main
    # thing hybrid search is supposed to help with, since BM25 can
    # match the literal phrase "Labor Code" where dense search alone
    # struggled ---
    "What is the Labor Code?",

    # --- Exact-identifier query - dense search historically smooths
    # over exact numbers; BM25 should be strong here specifically ---
    "What does Article 300 say?",

    # --- Taglish / code-switching ---
    "Ano ang requirements para sa maternity leave?",
    "Pwede po bang mag-resign nang walang 30-day notice?",

    # --- Pure Tagalog - expect BM25 to contribute little/nothing here
    # since content_tsv is 'english'-config over an English corpus;
    # semantic_search should still carry these, same as before ---
    "Ano ang mga kondisyon para sa pagbibigay ng maternity leave?",
    "Ilang araw ang maternity leave sa Pilipinas?",
    "Paano kinakalkula ang ikalabintatlong buwang sahod?",
]


def main() -> None:
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("Connecting to Supabase...")
    client = get_supabase_admin_client()

    count_result = client.table("law_chunks").select("chunk_id", count="exact").execute()
    print(f"Table has {count_result.count} indexed chunks.\n")

    for query in TEST_QUERIES:
        print("=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        query_embedding = model.encode([query], normalize_embeddings=True).tolist()[0]

        response = client.rpc(
            "hybrid_search_law_chunks",
            {
                "query_text": query,
                "query_embedding": query_embedding,
                "match_count": TOP_K,
            },
        ).execute()
        rows = response.data

        if not rows:
            print("  (no results returned at all)")
            print()
            continue

        for i, row in enumerate(rows):
            text_preview = row["text"][:150].replace("\n", " ")
            print(
                f"  [{i + 1}] rrf_score={row['rrf_score']:.5f}  "
                f"{row['title']} (p.{row['start_page']})"
            )
            print(f"      \"{text_preview}...\"")
        print()

    print("=" * 70)
    print("Eyeball the rrf_score values above:")
    print("  - HIGHER = better now (opposite of the old distance metric).")
    print("  - Compare 'What is the Labor Code?' and 'Article 300' results")
    print("    against your dense-only pgvector run - these are the two")
    print("    queries hybrid search should visibly improve.")
    print("  - For the pure Tagalog queries, check whether rankings")
    print("    changed much from dense-only - expected to be similar,")
    print("    since content_tsv can't lexically match Tagalog text.")
    print("  - Pick min_score_threshold in pipeline.py: somewhere between")
    print("    your worst still-relevant score and your best clearly-")
    print("    irrelevant score, same process as every previous threshold.")


if __name__ == "__main__":
    main()