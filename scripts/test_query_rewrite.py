"""
test_query_rewrite.py - Two-part test for the query-rewrite system,
unconfirmed since before this whole session started.

PART 1: question_seems_self_contained() - pure Python, no LLM call,
runs instantly. Tests realistic follow-up phrasing patterns.

PART 2: rewrite_query_with_history() - the full LLM-driven rewrite,
tested in realistic multi-turn conversations (built with the real
ConversationSession class, not a mock). Requires USE_OLLAMA=true (or
a real Claude key later) since this stage makes an actual generation
call.

Run: python scripts/test_query_rewrite.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from pipeline import (
    question_seems_self_contained,
    rewrite_query_with_history,
    ConversationSession,
    MOCK_MODE,
    USE_OLLAMA,
)

# ============================================================
# PART 1: Pure heuristic - no LLM, no history needed
# ============================================================
HEURISTIC_TEST_CASES = [
    ("What's the requirement?", "NEEDS_REWRITE", "short follow-up, no pronoun - caught by word-count"),
    ("How about for paternity leave?", "SELF_CONTAINED", "implicitly needs context, but no leading pronoun + 5 words - a real gap"),
    ("Is it different for probationary employees?", "SELF_CONTAINED", "pronoun is MID-sentence, not first word - heuristic misses this"),
    ("That too?", "NEEDS_REWRITE", "pronoun IS the first word - correctly caught"),
    ("What is the minimum wage in the Philippines?", "SELF_CONTAINED", "genuinely self-contained, new topic - correct"),
]


def run_part_1():
    print("#" * 70)
    print("PART 1: question_seems_self_contained() - pure heuristic")
    print("#" * 70)
    for question, expected_label, note in HEURISTIC_TEST_CASES:
        result = question_seems_self_contained(question)
        actual_label = "SELF_CONTAINED" if result else "NEEDS_REWRITE"
        status = "MATCHES EXPECTATION" if actual_label == expected_label else "DIFFERS"
        print(f"[{status}] {question!r}")
        print(f"    -> classified as: {actual_label}  |  {note}")
    print()


# ============================================================
# PART 2: Full rewrite in realistic multi-turn conversations
# ============================================================
CONVERSATION_SCENARIOS = [
    {
        "label": "Your exact example - short follow-up",
        "history": [("Tell me about maternity leave.", "Maternity leave in the Philippines is governed by the Expanded Maternity Leave Law (RA 11210), which grants 105 days of paid leave.")],
        "follow_up": "What's the requirement?",
    },
    {
        "label": "The false-positive case - mid-sentence pronoun",
        "history": [("What are the requirements for resignation?", "An employee must serve a written notice at least one month in advance, per Article 300 of the Labor Code.")],
        "follow_up": "Is it different for probationary employees?",
    },
    {
        "label": "No leading pronoun, but still context-dependent",
        "history": [("What are the requirements for maternity leave?", "A female worker must have paid at least 3 monthly SSS contributions.")],
        "follow_up": "How about for paternity leave?",
    },
]


def run_part_2():
    print("#" * 70)
    print("PART 2: Full rewrite in realistic multi-turn conversations")
    if MOCK_MODE:
        print("WARNING: MOCK_MODE active - rewrite calls will return placeholder")
        print("         text, not a real rewritten question. Set USE_OLLAMA=true")
        print("         or wait for a real Claude key for a meaningful test.")
    elif USE_OLLAMA:
        print("Using Ollama for the rewrite call.")
    else:
        print("Using real Claude API for the rewrite call.")
    print("#" * 70)

    for scenario in CONVERSATION_SCENARIOS:
        print()
        print("=" * 70)
        print(f"SCENARIO: {scenario['label']}")
        print("=" * 70)

        session = ConversationSession()
        for question, answer in scenario["history"]:
            session.add_turn(question, answer)
            print(f"  [history] Q: {question}")
            print(f"  [history] A: {answer}")

        follow_up = scenario["follow_up"]
        was_flagged_self_contained = question_seems_self_contained(follow_up)

        print(f"\n  FOLLOW-UP: {follow_up}")
        print(f"  question_seems_self_contained(): {was_flagged_self_contained}")

        resolved = rewrite_query_with_history(follow_up, session)

        if resolved == follow_up:
            print(f"  RESULT: unchanged -> {resolved!r}")
        else:
            print(f"  RESULT: rewritten -> {resolved!r}")

        print("  CHECK: would this resolved question, on its own, retrieve the")
        print("         right chunk without needing the conversation history?")


if __name__ == "__main__":
    run_part_1()
    run_part_2()