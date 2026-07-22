"""
test_generation.py - Runs the FULL pipeline (retrieval + Claude
generation) directly, bypassing FastAPI, Supabase auth, and the
frontend entirely. Answers the real remaining question: does Claude
respond correctly, in the right language, WITH citations - not just
"did retrieval find the right chunk" (that's test_retrieval.py's job).

Requires ANTHROPIC_API_KEY to be set in your .env for a REAL test.
Without it, pipeline.py's MOCK_MODE kicks in and you'll just get
placeholder text - still useful to confirm the pipeline runs end to
end, but it will NOT tell you anything about Tagalog quality.

Run: python scripts/test_generation.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Confirmed via `find ~/law_chatbot_internship -name pipeline.py`:
# it lives at backend/app/pipeline.py, not backend/pipeline.py.
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from sentence_transformers import SentenceTransformer
from pipeline import run_full_pipeline, ConversationSession, MOCK_MODE, USE_OLLAMA

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

TEST_CASES = [
    {
        "label": "English",
        "question": "What are the requirements for maternity leave?",
    },
    {
        "label": "Taglish",
        "question": "Pwede po bang mag-resign nang walang 30-day notice?",
    },
    {
        "label": "Pure Tagalog",
        "question": "Ilang araw ang maternity leave sa Pilipinas?",
    },
    {
        "label": "Pure Tagalog (explicit language instruction test)",
        "question": "Sagutin mo sa Tagalog: ilang araw ang maternity leave sa Pilipinas?",
    },
]


def main() -> None:
    if MOCK_MODE:
        print("⚠️  MOCK_MODE is active - no ANTHROPIC_API_KEY found in .env.")
        print("    This run will only confirm the pipeline WIRES together correctly.")
        print("    It will NOT tell you anything about real Tagalog answer quality.\n")
    elif USE_OLLAMA:
        print("🦙 USE_OLLAMA=true - this will test llama3.2:3b, NOT Claude.")
        print("    Set USE_OLLAMA=false (or unset it) to test the actual prod generator.\n")
    else:
        print("✅ Testing against the real Claude API.\n")

    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    session = ConversationSession()

    for case in TEST_CASES:
        print("=" * 70)
        print(f"[{case['label']}] {case['question']}")
        print("=" * 70)

        result = run_full_pipeline(
            case["question"], session, embedding_model,
        )

        print(f"found_context: {result['found_context']}")
        print(f"citation_count: {result['citation_count']}")
        print(f"latency_seconds: {result['latency_seconds']:.2f}")
        print(f"\nANSWER:\n{result['answer']}\n")

        if result["citations"]:
            print("CITATIONS:")
            for c in result["citations"]:
                print(f"  - {c['title']} ({c['page_reference']})")
        print()

    print("=" * 70)
    print("What to check by hand:")
    print("  - Did Tagalog questions get answered IN Tagalog, or did Claude")
    print("    default to English because the retrieved context is English?")
    print("  - Are citations still present and correctly formatted on")
    print("    Tagalog answers, not just English ones?")
    print("  - Does the explicit 'Sagutin mo sa Tagalog' case behave")
    print("    differently from the implicit one? If yes, that's your")
    print("    evidence for whether SYSTEM_INSTRUCTIONS in pipeline.py")
    print("    needs an explicit language-matching rule added.")


if __name__ == "__main__":
    main()