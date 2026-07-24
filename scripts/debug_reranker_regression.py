"""
debug_reranker_regression.py - Isolates WHY the reranker regression
happens on "Pwede po bang mag-resign nang walang 30-day notice?" by
holding the two COMPETING CHUNKS fixed and varying only the query
phrasing.

Article 300 (the correct answer) says "one (1) month in advance" -
never "30 days" anywhere. The wrong-winning maternity leave chunk
literally contains "thirty (30) days". If rephrasing the query to say
"one month" instead of "30-day" flips the ranking back to correct,
that's direct evidence of surface lexical overlap driving the
reranker's score, not genuine topical understanding - same diagnostic
principle as debug_paternity_maternity.py, applied to the reranker
instead of dense/BM25.

Run: python scripts/debug_reranker_regression.py
"""

from sentence_transformers import CrossEncoder

RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"

# The two REAL competing chunks from the actual regression, verbatim.
CORRECT_CHUNK = (
    "ART. 300. [285] Termination by Employee. \u2013 (a) An employee may terminate without just "
    "cause the employee-employer relationship by serving a written notice on the employer at least "
    "one (1) month in advance. The employer upon whom no such notice was served may hold the "
    "employee liable for damages.\n\n"
    "(b) An employee may put an end to the relationship without serving any notice on the "
    "employer for any of the following just causes:"
)

WRONG_WINNER_CHUNK = (
    "(b) An additional maternity leave of thirty (30) days, without pay, can be availed of, at "
    "the option of the female worker: Provided, That the employer shall be given due notice, in "
    "writing, at least forty-five (45) days before the end of her maternity leave: Provided, "
    "further, That no prior notice shall be necessary in the event of a medical emergency but "
    "subsequent notice shall be given to the head of the agency."
)

# Query variants - same underlying question, different surface wording.
# The key contrast: variants mentioning "30-day" match WRONG_WINNER's
# literal wording; variants mentioning "one month" match CORRECT's.
QUERY_VARIANTS = [
    ("Original Taglish (the actual failing query)", "Pwede po bang mag-resign nang walang 30-day notice?"),
    ("English translation, still says '30-day'", "Can I resign without giving a 30-day notice?"),
    ("Rephrased to match Article 300's own wording", "Can I resign without giving one month's notice?"),
    ("Generic, no specific number mentioned", "What is required for an employee to resign?"),
    ("Uses 'terminate employment', Article 300's own verb", "Can an employee terminate employment without one month's notice?"),
]


def main() -> None:
    print(f"Loading reranker model: {RERANKER_MODEL_NAME} ...")
    reranker = CrossEncoder(RERANKER_MODEL_NAME)
    print()

    print("#" * 70)
    print("Scoring both REAL competing chunks against each query variant")
    print("#" * 70)

    for label, query in QUERY_VARIANTS:
        correct_score = reranker.predict([(query, CORRECT_CHUNK)])[0]
        wrong_score = reranker.predict([(query, WRONG_WINNER_CHUNK)])[0]

        winner = "CORRECT (Article 300)" if correct_score > wrong_score else "WRONG (maternity leave)"

        print()
        print("=" * 70)
        print(f"{label}")
        print(f"QUERY: {query!r}")
        print("=" * 70)
        print(f"  Article 300 (correct) score:        {correct_score:.4f}")
        print(f"  Maternity leave (wrong) score:       {wrong_score:.4f}")
        print(f"  WINNER: {winner}")

    print()
    print("#" * 70)
    print("READ THIS:")
    print("  If 'one month' variants correctly favor Article 300 while")
    print("  '30-day' variants favor the wrong chunk, that's direct evidence")
    print("  the reranker is responding to LITERAL NUMBER/PHRASE OVERLAP")
    print("  ('30 days' appears in both query and wrong chunk) rather than")
    print("  genuine topical understanding that both describe a NOTICE")
    print("  PERIOD FOR RESIGNATION vs a NOTICE PERIOD FOR MATERNITY LEAVE.")
    print("#" * 70)


if __name__ == "__main__":
    main()