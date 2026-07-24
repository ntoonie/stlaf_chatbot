"""
test_corpus_coverage.py - Broad, English-only coverage check across
the FULL 24-document corpus, one or two questions per document not
already covered by test_retrieval.py's core regression queries.

REPLACES the original 12-question version, which predated the
reranker (was dense+BM25 only) and had heavy topical overlap with
queries already tested extensively elsewhere (maternity leave,
paternity leave, resignation, 13th month pay). This version focuses
on genuinely untested ground, including documents never queried
before: DO-237-22, RA 7877 (Anti-Sexual Harassment Act, distinct from
the Safe Spaces Act), and RA 9442 (PWD equal-opportunity provisions).

Language scope deliberately English-only - multi-language testing has
its own established pattern in test_retrieval.py and ad-hoc UI
testing; keeping this script focused on topical breadth, not language
variation, avoids conflating two different things being measured.

Run: python scripts/test_corpus_coverage.py
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

# One or two questions per document, targeting genuinely untested
# ground. expected_source values verified against real text via
# project_knowledge_search (not inferred from filenames/RA numbers) -
# several corrected findings noted below.
COVERAGE_QUERIES = [
    {"question": "What does DO 237-22 establish or regulate?",
     "expected_source": "DO23722.pdf = Revised IRR of the Telecommuting Act (RA 11165)",
     "note": "VERIFIED via project knowledge. A bare citation-style query with no topical keywords is expected to underperform regardless of source - same known pattern as 'What is the Labor Code?'. Ask about telecommuting directly instead to see this document retrieve well."},

    {"question": "Who can be held liable for sexual harassment under this law - only the employer, or also co-workers?", "expected_source": "Anti-Sexual Harassment Act of 1995 (RA 7877)",
     "note": "Confirmed good result earlier: BOTH RA 7877 and Safe Spaces Act scored highly (0.94-0.96) - legitimate overlap, not a bug, since both laws address employer liability."},
    {"question": "What is the difference between this law and the Safe Spaces Act?", "expected_source": "Anti-Sexual Harassment Act of 1995 or Safe Spaces Act",
     "note": "Comparative/meta-question - known weak pattern, same family as 'What is the Labor Code?'. No single chunk synthesizes a comparison between two laws."},

    {"question": "Can an employer refuse to hire someone solely because they have a disability?",
     "expected_source": "Labor Code (Article 79-81 + footnote 69, citing RA 7277 Sec. 5)",
     "note": "CORRECTED after verification: RA_9442.pdf itself only covers Chapter 8 (consumer discounts/privileges) - NOT the employment equal-opportunity provision, which lives in the ORIGINAL RA 7277, never ingested into this corpus. The Labor Code footnote citation is arguably the best available answer given what's actually indexed - not a retrieval bug, a corpus completeness gap."},
    {"question": "What workplace accommodations must an employer provide for a disabled employee?",
     "expected_source": "Labor Code (Article 167, 156) - same RA 7277 gap as above",
     "note": "Same corpus gap as the previous question - RA_9442.pdf and RA_10754.pdf both amend RA 7277 but neither contains its core employment provisions."},

    {"question": "Can a company apply for an exemption from the minimum wage order?", "expected_source": "Wage Rationalization Act"},

    {"question": "What is a Safety Officer, and is every company required to have one?", "expected_source": "Occupational Safety and Health Standards Act"},
    {"question": "What are the penalties for an employer that violates OSH standards?", "expected_source": "Occupational Safety and Health Standards Act"},

    {"question": "What is illegal recruitment, and what are its penalties?", "expected_source": "Migrant Workers and Overseas Filipinos Act (RA 8042), also covered by its amendment RA 10022"},

    {"question": "How does someone qualify as a 'solo parent' under this law?", "expected_source": "Solo Parents' Welfare Act"},

    {"question": "Is an employer required to offer telecommuting, or is it optional?", "expected_source": "Telecommuting Act (RA 11165) and/or its Revised IRR (DO23722.pdf)"},

    {"question": "What is the NLRC's jurisdiction - what kinds of labor disputes can it actually hear?", "expected_source": "2011 NLRC Rules of Procedure",
     "note": "VERIFIED: 2011__NLRC.pdf Section 1 has near-perfect matching content (10-item jurisdiction list). BUT near-identical 'Section 1. Jurisdiction of Labor Arbiters' language also exists in RA_10022.pdf's IRR and Labor Code Art. 224 - a genuinely hard 3-way disambiguation, not a careless miss."},
    {"question": "What is the difference between labor-only contracting and legitimate job contracting?", "expected_source": "Rules Implementing Articles 106 to 109 of the Labor Code (DO 174-17)"},

    {"question": "Can a domestic worker be required to work on their designated rest day?", "expected_source": "Domestic Workers Act (Batas Kasambahay)"},

    {"question": "What happens to an SSS member's contributions if their employer never remitted them?", "expected_source": "Social Security Act of 2018"},

    {"question": "Is stalking or persistent unwanted following covered under the Safe Spaces Act?", "expected_source": "Safe Spaces Act",
     "note": "Correct document does appear across all ranks, but at low scores (0.13-0.27) - content addresses harassment generally (catcalling, wolf-whistling) without a clearly isolated 'stalking' provision."},

    {"question": "Are service charges the same as tips, and can an employer treat them that way?", "expected_source": "Service Charge Law",
     "note": "Comparative question - known weak pattern, same as the harassment-law comparison above."},

    {"question": "What is the penalty for employing a child in hazardous work?", "expected_source": "An Act Providing for the Elimination of the Worst Forms of Child Labor (RA 9231)"},

    {"question": "Can an employer set a mandatory retirement age below what SSS allows for benefits?", "expected_source": "Social Security Act of 2018 or Labor Code",
     "note": "Synthesis-style question - no single chunk directly compares employer-set retirement age against SSS-allowed benefit age."},

    {"question": "What government agency handles complaints from Overseas Filipino Workers specifically?", "expected_source": "Department of Migrant Workers Act (RA 11641), also legitimately covered by RA 8042 Section 23",
     "note": "VERIFIED: RA_11641.pdf has clearly relevant content (Sec. 3 definitions, Department powers, OFW family protection) - the earlier miss was a genuine ranking loss against RA 8042's older but more directly-quotable phrasing, not a content gap."},
]



def main() -> None:
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print(f"Loading reranker model: {RERANKER_MODEL_NAME} ...")
    reranker = CrossEncoder(RERANKER_MODEL_NAME)

    print("Connecting to Supabase...")
    client = get_supabase_admin_client()

    count_result = client.table("law_chunks").select("chunk_id", count="exact").execute()
    print(f"Table has {count_result.count} indexed chunks.\n")

    for item in COVERAGE_QUERIES:
        query = item["question"]
        print("=" * 70)
        print(f"QUERY: {query}")
        print(f"EXPECTED SOURCE: {item['expected_source']}")
        note = item.get("note")
        if note:
            print(f"NOTE: {note}")
        print("=" * 70)

        query_embedding = model.encode([query], normalize_embeddings=True).tolist()[0]
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

        pairs = [(query, row["text"]) for row in candidates]
        rerank_scores = reranker.predict(pairs)
        for row, score in zip(candidates, rerank_scores):
            row["rerank_score"] = float(score)
        reranked = sorted(candidates, key=lambda r: r["rerank_score"], reverse=True)

        for i, row in enumerate(reranked[:FINAL_TOP_K]):
            text_preview = row["text"][:120].replace("\n", " ")
            print(f"  [{i + 1}] rerank_score={row['rerank_score']:.4f}  {row['title']} (p.{row['start_page']})")
            print(f"      \"{text_preview}...\"")
        print()

    print("=" * 70)
    print("For each query, check whether EXPECTED SOURCE appears at/near")
    print("rank 1. Note rerank_score too - a correct document at a LOW")
    print("score (e.g. <0.05, per today's calibration) is a weaker result")
    print("than one that scores high, even if the ranking itself is right.")


if __name__ == "__main__":
    main()