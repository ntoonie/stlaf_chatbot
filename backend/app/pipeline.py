"""
pipeline.py - The full RAG pipeline: session memory, query rewriting,
retrieval, prompt construction, generation, and structured citations.

Generation uses the Claude API when ANTHROPIC_API_KEY is set, and
automatically falls back to a mock generator when it isn't - see
MOCK_MODE below. This lets the rest of the system be built and tested
before a real API key is available.
"""

import re
import time
import sys
import os
from pathlib import Path
# OLLAMA PIPELINE
import requests as http_requests  # separate name to avoid clashing with any existing 'requests' import

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
USE_OLLAMA = os.environ.get("USE_OLLAMA", "false").lower() == "true"

if USE_OLLAMA:
    print("🦙 USE_OLLAMA=true - generation will use local Ollama (llama3.2:3b), not Claude or mock mode.")


def _generate_ollama_response(system_message: str, user_message: str) -> str:
    """Real generation via a locally-running Ollama model - no API key,
    no cost, fully offline. Slower than Claude, but genuinely real
    output instead of mock placeholder text."""
    full_prompt = f"{system_message}\n\n{user_message}"
    response = http_requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()
#END OF OLLAMA PIPELINE

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from rag_utils import (
    format_page_reference,
    format_retrieved_context,
    is_refusal,
    REFUSAL_MESSAGE,
)

from supabase_client import get_supabase_admin_client

from anthropic import Anthropic

# ============================================================
# Claude API configuration, with automatic mock-mode fallback
# ============================================================
CLAUDE_MODEL = "claude-sonnet-5"

_client: Anthropic | None = None
MOCK_MODE = os.environ.get("ANTHROPIC_API_KEY") is None

if MOCK_MODE:
    print("⚠️  No ANTHROPIC_API_KEY found - running in MOCK MODE. "
          "Generation will return placeholder text, not real Claude output.")

# Toggle for the Tagalog/Taglish English-gloss translation step (see
# question_seems_non_english / translate_question_to_english below).
# Built while llama3.2:3b was the only generator and needed the help;
# untested whether Claude needs it too. Since each translation is a
# SECOND full generation call, this doubles Claude API cost on every
# Tagalog/Taglish question specifically - A/B test with this flag
# before assuming it's still worth keeping on once a real Claude key
# is in use.
ENABLE_TRANSLATION = os.environ.get("ENABLE_TRANSLATION", "true").lower() == "true"


def get_claude_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        _client = Anthropic(api_key=api_key)
    return _client


CITATION_PATTERN = re.compile(r"\(Source:\s*[^,]+,\s*pp?\.\s*\d+(-\d+)?\)")

SYSTEM_INSTRUCTIONS = f"""You are a legal information assistant specializing EXCLUSIVELY in Philippine labor law.

STRICT RULES YOU MUST FOLLOW:
1. Answer ONLY using the information provided in the "RETRIEVED CONTEXT" section below. Do NOT use any other knowledge you may have about Philippine labor law, other countries' labor laws, or general legal knowledge.
2. If the RETRIEVED CONTEXT does not contain enough information to answer the question, respond with EXACTLY this sentence and nothing else: "{REFUSAL_MESSAGE}"
3. When you DO answer, you MUST cite the specific source document and page number for every claim, using the format: (Source: [document title], p.[page number]).
4. Do not guess, estimate, or infer information that is not explicitly stated in the RETRIEVED CONTEXT.
5. Keep answers clear and direct, written for a non-lawyer to understand, while remaining accurate to the legal text.
6. The RETRIEVED CONTEXT is written in English even when the QUESTION is in Tagalog or Taglish - this is expected, not a sign the context doesn't apply. If an English translation of the question is provided below the QUESTION, use it only to confirm your understanding of what is being asked. Your ANSWER must still be written in the same language as the original QUESTION, not the translation.
7. Never include the refusal sentence anywhere in your response unless it is the ENTIRE response. If you are able to answer using the RETRIEVED CONTEXT, do not append, reference, restate, or hedge with the refusal sentence afterward - a correct answer must stand on its own, with nothing contradicting it at the end.
"""


class ConversationSession:
    """Holds running history for ONE session, capped to a fixed number
    of recent turns to control prompt token growth."""

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns
        self.turns: list[dict] = []

    def add_turn(self, question: str, answer: str) -> None:
        self.turns.append({"question": question, "answer": answer})
        self.turns = self.turns[-self.max_turns :]

    def has_history(self) -> bool:
        return len(self.turns) > 0

    def format_history_for_prompt(self) -> str:
        if not self.has_history():
            return "(No previous conversation.)"
        lines = []
        for turn in self.turns:
            lines.append(f"User: {turn['question']}")
            lines.append(f"Assistant: {turn['answer']}")
        return "\n".join(lines)


class SessionStore:
    """Maps session_id -> ConversationSession, keeping simultaneous
    conversations isolated from each other.

    KNOWN LIMITATION: in-memory only - sessions are lost on server
    restart and this does not scale across multiple server instances.
    """

    def __init__(self):
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession()
        return self._sessions[session_id]


def retrieve_relevant_chunks(
    question: str,
    embedding_model,
    top_k: int = 4,
    min_score_threshold: float = 0.01,
) -> dict:
    """Embed the question, run HYBRID search (BM25-equivalent full-text
    search + dense vector search, combined via Reciprocal Rank Fusion)
    through the hybrid_search_law_chunks RPC function, and filter by
    score threshold. Returns found=False if nothing passes the bar -
    this is the FIRST line of defense against hallucination.

    IMPORTANT DIRECTION FLIP from the old distance-based version: RRF
    scores are HIGHER = better (not lower = better, like distance was),
    and live on a completely different numeric scale - roughly
    0.008-0.033 for typical rank positions with the default rrf_k=50,
    NOT the ~0.3-0.9 range distance used. min_score_threshold=0.01 is a
    genuine floor derived from real hybrid_search_law_chunks output
    (observed range ~0.0185-0.0392 for relevant results), not a guess -
    it's set low deliberately since RRF score can't reliably separate
    right from wrong on its own (see the failed 'Article 300' full-
    sentence test) - that job belongs to the reranker, not this
    threshold."""
    query_embedding = embedding_model.encode([question], normalize_embeddings=True).tolist()[0]

    client = get_supabase_admin_client()
    response = client.rpc(
        "hybrid_search_law_chunks",
        {
            "query_text": question,
            "query_embedding": query_embedding,
            "match_count": top_k,
        },
    ).execute()

    rows = response.data
    if not rows:
        return {"found": False, "chunks": [], "best_score": None}

    scores = [row["rrf_score"] for row in rows]
    best_score = max(scores)

    if best_score < min_score_threshold:
        return {"found": False, "chunks": [], "best_score": best_score}

    passing_chunks = [row for row in rows if row["rrf_score"] >= min_score_threshold]
    return {"found": True, "chunks": passing_chunks, "best_score": best_score}


def build_full_prompt(question: str, retrieval_result: dict, english_gloss: str | None = None) -> str:
    """Assembles the user-turn content: labeled retrieved context +
    question, plus an optional English gloss of the question (for
    Tagalog/Taglish input) to help generation, without replacing the
    original question the answer must still be written in."""
    context_text = format_retrieved_context(retrieval_result.get("chunks", []))
    gloss_block = (
        f"\n(English translation of the question, for your understanding only: {english_gloss})"
        if english_gloss
        else ""
    )
    return f"""RETRIEVED CONTEXT:
{context_text}

QUESTION: {question}{gloss_block}

ANSWER:"""


def generate_response(system_message: str, user_message: str, max_new_tokens: int = 400) -> str:
    """Calls Ollama, Claude, or returns mock text - checked in that
    priority order. USE_OLLAMA takes precedence even if a Claude key
    is also present, so you can force free local testing on demand."""
    if USE_OLLAMA:
        return _generate_ollama_response(system_message, user_message)
    if MOCK_MODE:
        return _generate_mock_response(user_message)

    client = get_claude_client()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_new_tokens,
        system=system_message,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text.strip()


def _generate_mock_response(user_message: str) -> str:
    """Placeholder generator - no API call, no GPU, no cost. Lets the
    rest of the pipeline be tested before a real Claude API key exists."""
    if "RETRIEVED CONTEXT:" not in user_message:
        if "LATEST QUESTION:" in user_message:
            return user_message.split("LATEST QUESTION:")[1].split("\n")[0].strip()
        return user_message.strip()

    return (
        "[MOCK RESPONSE - no Claude API key configured] "
        "This is placeholder text standing in for a real generated answer. "
        "The retrieval pipeline ran successfully and found relevant context "
        "for this question (Source: Mock Document, p.1)."
    )


AMBIGUOUS_REFERENCE_WORDS = {"it", "that", "this", "them", "those", "these", "he", "she", "they"}


def question_seems_self_contained(question: str) -> bool:
    """Cheap heuristic: if the question doesn't start with a pronoun-like
    reference word and is reasonably long, it's very likely already
    self-contained - skip the unreliable-on-small-models rewriting step
    entirely rather than risk contamination."""
    first_word = question.strip().split()[0].lower() if question.strip() else ""
    return first_word not in AMBIGUOUS_REFERENCE_WORDS and len(question.split()) >= 4


def rewrite_query_with_history(question: str, session: ConversationSession) -> str:
    if not session.has_history():
        return question
    if question_seems_self_contained(question):
        return question  # skip rewriting entirely - avoid unnecessary contamination risk

    rewrite_system_message = (
        "You rewrite a user's latest question into a fully self-contained "
        "question, using the conversation history for context. If the "
        "question is already self-contained, return it UNCHANGED. "
        "Output ONLY the rewritten question, with no explanation, prefix, or quotes."
    )
    rewrite_user_message = f"""CONVERSATION HISTORY:
{session.format_history_for_prompt()}

LATEST QUESTION: {question}

REWRITTEN SELF-CONTAINED QUESTION:"""

    rewritten = generate_response(rewrite_system_message, rewrite_user_message, max_new_tokens=80)
    return rewritten.strip()


# Common Filipino function words unlikely to appear in genuine English
# text - a cheap, no-LLM-call gate so English-only questions skip
# translation entirely, rather than paying for an extra generation
# call on every single request. Not exhaustive, not a real language
# detector - just needs to catch the common case cheaply.
TAGALOG_MARKER_WORDS = {
    "ang", "ng", "mga", "na", "sa", "ba", "po", "opo", "hindi", "oo",
    "ako", "ikaw", "siya", "kami", "tayo", "kayo", "sila", "ito", "iyan",
    "paano", "saan", "kailan", "bakit", "sino", "ilan", "walang", "may",
    "meron", "nang", "lang", "din", "rin", "naman", "kasi", "yung",
}


def question_seems_non_english(question: str) -> bool:
    """Cheap heuristic: if any common Tagalog function word appears,
    the question is very likely Tagalog or Taglish. Deliberately loose
    (matches on Taglish too, not just pure Tagalog) - the cost of a
    false positive here is one extra translation call; the cost of a
    false negative is the exact generation-refusal failure mode this
    whole feature exists to fix."""
    words = set(re.findall(r"[a-zA-Z]+", question.lower()))
    return bool(words & TAGALOG_MARKER_WORDS)


def translate_question_to_english(question: str) -> str:
    """Get an English gloss of a Tagalog/Taglish question, to help
    generation - NOT used for retrieval, since BGE-M3 already handles
    Tagalog/Taglish retrieval well natively (confirmed via
    test_retrieval.py). This targets the generation-stage failure
    debug_single_query.py isolated: correct context retrieved, but the
    model still refused, most likely from struggling to map a Tagalog
    question onto English legal text unassisted.

    Falls back to the original question if translation comes back
    empty - never let a translation failure silently break the whole
    pipeline."""
    translate_system_message = (
        "You are a translator. Translate the user's question into "
        "clear, natural English. Output ONLY the English translation, "
        "with no explanation, prefix, quotes, or commentary."
    )
    translate_user_message = f"QUESTION: {question}\n\nENGLISH TRANSLATION:"

    translated = generate_response(
        translate_system_message, translate_user_message, max_new_tokens=100
    )
    translated = translated.strip()
    return translated if translated else question


def build_structured_citations(retrieval_result: dict, snippet_length: int = 150) -> list[dict]:
    """Builds citations from ACTUAL retrieval results, never by parsing
    the LLM's own generated text."""
    citations = []
    for chunk in retrieval_result.get("chunks", []):
        page_ref = format_page_reference(chunk["start_page"], chunk["end_page"])
        snippet = chunk["text"][:snippet_length].replace("\n", " ").strip()
        if len(chunk["text"]) > snippet_length:
            snippet += "..."
        citations.append(
            {
                "title": chunk["title"],
                "law_number": chunk["law_number"],
                "page_reference": page_ref,
                "category": chunk["category"],
                "snippet": snippet,
                "relevance_score": chunk["rrf_score"],
            }
        )
    return citations


def run_full_pipeline(
    question: str,
    session: ConversationSession,
    embedding_model,
    top_k: int = 4,
    min_score_threshold: float = 0.01,
) -> dict:
    """The complete pipeline: memory -> retrieval -> prompting ->
    generation -> citations."""
    start_time = time.perf_counter()

    resolved_question = rewrite_query_with_history(question, session)

    retrieval_result = retrieve_relevant_chunks(
        resolved_question, embedding_model, top_k, min_score_threshold
    )

    if not retrieval_result["found"]:
        session.add_turn(question, REFUSAL_MESSAGE)
        return {
            "answer": REFUSAL_MESSAGE,
            "citations": [],
            "citation_count": 0,
            "found_context": False,
            "latency_seconds": time.perf_counter() - start_time,
        }

    # Retrieval already succeeded using the ORIGINAL (possibly Tagalog)
    # question - BGE-M3 handles Tagalog/Taglish retrieval well natively,
    # so translation is deliberately NOT used here. It's only applied
    # now, for generation, targeting the specific failure
    # debug_single_query.py isolated: correct context retrieved, model
    # still refused.
    english_gloss = None
    if ENABLE_TRANSLATION and question_seems_non_english(resolved_question):
        english_gloss = translate_question_to_english(resolved_question)

    full_prompt = build_full_prompt(resolved_question, retrieval_result, english_gloss)
    raw_answer = generate_response(SYSTEM_INSTRUCTIONS, full_prompt, max_new_tokens=600)

    llm_refused = is_refusal(raw_answer)
    citations = build_structured_citations(retrieval_result) if not llm_refused else []

    session.add_turn(question, raw_answer)

    return {
        "answer": raw_answer,
        "citations": citations,
        "citation_count": len(citations),
        "found_context": True,
        "latency_seconds": time.perf_counter() - start_time,
    }