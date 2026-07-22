"""
debug_single_query.py - Runs ONE query through each pipeline stage
SEPARATELY, printing everything unabridged: the raw retrieved chunks
and scores, the exact assembled prompt sent to the LLM (not truncated),
and the raw generated output. Built to answer one specific question:
does llama3.2:3b actually receive the correct context and just fail
to use it, or does something upstream silently exclude/truncate it
before generation ever gets a chance?

Run: python scripts/debug_single_query.py
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from sentence_transformers import SentenceTransformer
from pipeline import (
    retrieve_relevant_chunks,
    build_full_prompt,
    generate_response,
    is_refusal,
    question_seems_non_english,
    translate_question_to_english,
    SYSTEM_INSTRUCTIONS,
    MOCK_MODE,
    USE_OLLAMA,
    ENABLE_TRANSLATION,
    OLLAMA_MODEL,
)

QUESTION = "Can I resign without giving a 1 month notice?"

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"


def main() -> None:
    if MOCK_MODE:
        print("WARNING: MOCK_MODE is active - generation step will be placeholder text.")
    elif USE_OLLAMA:
        print(f"Using Ollama: {OLLAMA_MODEL}")
    else:
        print("Using real Claude API.")
    print()

    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} ...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print()

    # ============================================================
    # STAGE 1: Retrieval - see the RAW chunks and scores, unabridged
    # ============================================================
    print("=" * 70)
    print("STAGE 1: RETRIEVAL")
    print("=" * 70)
    print(f"QUESTION: {QUESTION}\n")

    retrieval_result = retrieve_relevant_chunks(QUESTION, embedding_model)

    print(f"found: {retrieval_result['found']}")
    print(f"best_score: {retrieval_result.get('best_score')}")
    print(f"number of chunks returned: {len(retrieval_result.get('chunks', []))}\n")

    for i, chunk in enumerate(retrieval_result.get("chunks", [])):
        print(f"--- Chunk {i + 1} ---")
        print(f"  title: {chunk['title']}")
        print(f"  page: {chunk.get('start_page')}-{chunk.get('end_page')}")
        print(f"  rrf_score: {chunk.get('rrf_score')}")
        print(f"  FULL TEXT (unabridged):")
        print(f"  {chunk['text']}")
        print()

    if not retrieval_result["found"]:
        print("Retrieval itself returned found=False - the refusal is happening")
        print("HERE, before generation is even called. Nothing to check further.")
        return

    # ============================================================
    # STAGE 1.5: Translation - the NEW step, mirrors what
    # run_full_pipeline actually does. Earlier versions of this
    # script called build_full_prompt() directly and skipped this
    # entirely, which meant it was silently testing the OLD pipeline
    # even after pipeline.py was updated - fixed now.
    # ============================================================
    print("=" * 70)
    print("STAGE 1.5: TRANSLATION")
    print("=" * 70)
    print(f"ENABLE_TRANSLATION: {ENABLE_TRANSLATION}")

    is_non_english = question_seems_non_english(QUESTION)
    print(f"question_seems_non_english(QUESTION): {is_non_english}")

    english_gloss = None
    if ENABLE_TRANSLATION and is_non_english:
        print("Calling translate_question_to_english()...")
        english_gloss = translate_question_to_english(QUESTION)
        print(f"english_gloss: {english_gloss!r}")
    else:
        print("Translation SKIPPED (either disabled via ENABLE_TRANSLATION,")
        print("or question_seems_non_english() returned False).")
    print()

    # ============================================================
    # STAGE 2: Prompt construction - see EXACTLY what gets sent
    # ============================================================
    print("=" * 70)
    print("STAGE 2: ASSEMBLED PROMPT (exactly what the LLM receives)")
    print("=" * 70)

    full_prompt = build_full_prompt(QUESTION, retrieval_result, english_gloss)
    full_text_sent = f"{SYSTEM_INSTRUCTIONS}\n\n{full_prompt}"

    print(full_text_sent)
    print()

    char_count = len(full_text_sent)
    rough_token_estimate = char_count // 4  # rough heuristic: ~4 chars/token
    print(f"Character count: {char_count}")
    print(f"Rough token estimate: ~{rough_token_estimate}")
    print("IMPORTANT: pipeline.py's _generate_ollama_response does NOT set")
    print("an explicit 'num_ctx' option in its request to Ollama's API.")
    print("Ollama's DEFAULT context window for many models is 2048 tokens")
    print("unless overridden - if the estimate above is anywhere close to")
    print("or above 2048, Ollama may be SILENTLY TRUNCATING this prompt")
    print("before the model ever sees all of it. This is worth ruling out")
    print("as the actual cause, separately from 'the model is just weak.'")
    print()

    # ============================================================
    # STAGE 3: Generation - see the RAW output and the refusal check
    # ============================================================
    print("=" * 70)
    print("STAGE 3: GENERATION")
    print("=" * 70)

    raw_answer = generate_response(SYSTEM_INSTRUCTIONS, full_prompt, max_new_tokens=600)

    print("RAW ANSWER (exactly what the model returned):")
    print(raw_answer)
    print()
    print(f"is_refusal(raw_answer): {is_refusal(raw_answer)}")
    print(f"(is_refusal requires an EXACT match to the refusal string - if")
    print(f" the model blended a partial answer with refusal-like text,")
    print(f" this would print False even though the answer is still bad -")
    print(f" worth reading the raw answer above regardless of this result.)")


if __name__ == "__main__":
    main()