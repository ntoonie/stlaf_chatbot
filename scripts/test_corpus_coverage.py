"""
test_corpus_coverage.py - Unlike test_retrieval.py (a fast regression
check on the same handful of known queries), this hits ONE question
per document that has never been tested in this project before, to
check broad corpus coverage for the first time.

Specifically checks the paternity_leave_act.pdf ingestion gap flagged
as unconfirmed in the original project notes - if that query doesn't
surface Paternity Leave Act content at/near rank 1, the original
suspicion was right and it needs re-ingestion.

Run: python scripts/test_corpus_coverage.py
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

# One question per document not yet covered by any prior test in this
# project. expected_source is what SHOULD show up at/near rank 1 - not
# a strict pass/fail, just something to eyeball against the printed
# result.
COVERAGE_QUERIES = [
    {
        "question": "How many days of paternity leave is a father entitled to?",
        "expected_source": "Paternity Leave Act",
    },
    {
        # Same question in Taglish, since the paternity leave file has
        # never been queried at all before now, in any language.
        "question": "Ilang araw ang paternity leave na pwedeng makuha ng ama?",
        "expected_source": "Paternity Leave Act",
    },
    {
        "question": "What are the requirements to qualify as a telecommuting employee?",
        "expected_source": "Telecommuting Act",
    },
    {
        "question": "Ano ang mga benepisyo ng isang solo parent sa trabaho?",
        "expected_source": "Solo Parents Welfare Act",
    },
    {
        "question": "What actions are considered workplace sexual harassment?",
        "expected_source": "Safe Spaces Act or Anti-Sexual Harassment Act",
    },
    {
        "question": "Magkano ang minimum wage ng isang kasambahay?",
        "expected_source": "Domestic Workers Act (Batas Kasambahay)",
    },
    {
        "question": "How should collected service charges be distributed to employees?",
        "expected_source": "Service Charge Law",
    },
    {
        "question": "Is it legal for a job posting to set a maximum age requirement?",
        "expected_source": "Anti-Age Discrimination in Employment Act",
    },
    {
        "question": "What protections are guaranteed to overseas Filipino workers?",
        "expected_source": "Migrant Workers Act",
    },
    {
        "question": "What additional benefits are night shift workers entitled to?",
        "expected_source": "Night Workers Act",
    },
    {
        "question": "What safety measures must an employer provide under OSH law?",
        "expected_source": "Occupational Safety and Health Standards Act",
    },
    {
        "question": "What is the minimum age for lawful employment?",
        "expected_source": "Anti-Child Labor Law",
    },
]


def main() -> None:
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("Connecting to Supabase...")
    client = get_supabase_admin_client()

    count_result = client.table("law_chunks").select("chunk_id", count="exact").execute()
    print(f"Table has {count_result.count} indexed chunks.\n")

    # Quick, separate check specifically for the flagged paternity
    # leave gap: does ANY chunk from that source_filename exist at all?
    print("=" * 70)
    print("DIRECT CHECK: does paternity_leave_act.pdf exist in the table AT ALL?")
    print("=" * 70)
    paternity_check = (
        client.table("law_chunks")
        .select("chunk_id, title", count="exact")
        .eq("source_filename", "paternity_leave_act.pdf")
        .limit(1)
        .execute()
    )
    if paternity_check.count and paternity_check.count > 0:
        print(f"FOUND: {paternity_check.count} chunk(s) with source_filename="
              f"'paternity_leave_act.pdf'. The original ingestion gap appears FIXED.")
    else:
        print("NOT FOUND: zero chunks with source_filename='paternity_leave_act.pdf'.")
        print("The original ingestion gap is CONFIRMED - this file needs to be")
        print("checked in data/raw/metadata.json and re-run through the full")
        print("extract -> chunk -> embed -> build_vector_db pipeline.")
    print()

    for item in COVERAGE_QUERIES:
        query = item["question"]
        print("=" * 70)
        print(f"QUERY: {query}")
        print(f"EXPECTED SOURCE: {item['expected_source']}")
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
    print("For each query, check whether the EXPECTED SOURCE actually appears")
    print("at or near rank 1. If a document never shows up across ANY of its")
    print("queries here, that's a new candidate ingestion gap worth checking")
    print("the same way as the paternity leave case above.")


if __name__ == "__main__":
    main()