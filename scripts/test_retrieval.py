"""
test_retrieval.py - Fetches a candidate pool via hybrid search (BM25 +
dense + RRF), then reranks it with a cross-encoder, printing BOTH
orderings side by side so you can see exactly what reranking changed -
not just trust that it helped.

REPLACES the pre-reranker version. Prints raw rerank_score (no
threshold filtering) so you can calibrate min_rerank_score in
pipeline.py from real output - I could not verify bge-reranker-v2-m3's
score range myself (blocked network in my build environment), so this
number is genuinely unconfirmed until you look at real values here.

Run: python scripts/test_retrieval.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from sentence_transformers import SentenceTransformer, CrossEncoder
from supabase_client import get_supabase_admin_client

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
CANDIDATE_POOL_SIZE = 20
FINAL_TOP_K = 4

TEST_QUERIES = [
    # --- Known-good baseline ---
    "What are the requirements for maternity leave?",
    "How is 13th month pay computed?",

    # --- Known-bad baseline (the "broad question" bug) ---
    "What is the Labor Code?",

    # --- Exact-identifier query ---
    "What does Article 300 say?",

    # --- Taglish / code-switching ---
    "Ano ang requirements para sa maternity leave?",
    "Pwede po bang mag-resign nang walang 30-day notice?",

    # --- Pure Tagalog ---
    "Ilang araw ang maternity leave sa Pilipinas?",

    # --- THE case that motivated building the reranker at all -
    # dense+BM25 both put Expanded Maternity Leave Law above the
    # correct Paternity Leave Act here (see
    # debug_paternity_maternity.py). This is the one query in this
    # list where reranking actually needs to prove itself.
    "Ilang araw ang paternity leave na pwedeng makuha ng ama?",
]


def main() -> None:
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print(f"Loading reranker model: {RERANKER_MODEL_NAME} ...")
    reranker = CrossEncoder(RERANKER_MODEL_NAME)

    print("Connecting to Supabase...")
    client = get_supabase_admin_client()

    count_result = client.table("law_chunks").select("chunk_id", count="exact").execute()
    print(f"Table has {count_result.count} indexed chunks.\n")

    for query in TEST_QUERIES:
        print("=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        query_embedding = embed_model.encode([query], normalize_embeddings=True).tolist()[0]
        response = client.rpc(
            "hybrid_search_law_chunks",
            {
                "query_text": query,
                "query_embedding": query_embedding,
                "match_count": CANDIDATE_POOL_SIZE,
            },
        ).execute()
        candidates = response.data

        if not candidates:
            print("  (no results returned at all)\n")
            continue

        print(f"--- BEFORE reranking (RRF order, top {FINAL_TOP_K} of {len(candidates)} candidates) ---")
        for i, row in enumerate(candidates[:FINAL_TOP_K]):
            print(f"  [{i + 1}] rrf_score={row['rrf_score']:.5f}  {row['title']} (p.{row['start_page']})")

        pairs = [(query, row["text"]) for row in candidates]
        rerank_scores = reranker.predict(pairs)
        for row, score in zip(candidates, rerank_scores):
            row["rerank_score"] = float(score)
        reranked = sorted(candidates, key=lambda r: r["rerank_score"], reverse=True)

        print(f"--- AFTER reranking (top {FINAL_TOP_K}) ---")
        for i, row in enumerate(reranked[:FINAL_TOP_K]):
            text_preview = row["text"][:100].replace("\n", " ")
            print(f"  [{i + 1}] rerank_score={row['rerank_score']:.4f}  (rrf was {row['rrf_score']:.5f})  {row['title']} (p.{row['start_page']})")
            print(f"      \"{text_preview}...\"")

        before_top = candidates[0]["chunk_id"]
        after_top = reranked[0]["chunk_id"]
        if before_top != after_top:
            print(f"  >>> RERANKING CHANGED RANK 1 (was: {candidates[0]['title']} -> now: {reranked[0]['title']})")
        print()

    print("=" * 70)
    print("Eyeball the rerank_score values above:")
    print("  - HIGHER = better (same convention as RRF, unlike raw distance).")
    print("  - For the paternity/maternity query specifically: did reranking")
    print("    fix it? Compare AFTER's rank 1 against BEFORE's.")
    print("  - Find the gap between your worst genuinely-relevant score and")
    print("    your best clearly-irrelevant score - that's min_rerank_score.")
    print("  - This number is COMPLETELY UNCONFIRMED until you do this -")
    print("    it was never tested against a live model before now.")


if __name__ == "__main__":
    main()