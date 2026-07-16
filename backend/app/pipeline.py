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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from rag_utils import (
    format_page_reference,
    format_retrieved_context,
    is_refusal,
    REFUSAL_MESSAGE,
)

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
    collection,
    embedding_model,
    top_k: int = 4,
    distance_threshold: float = 0.85,
) -> dict:
    """Embed the question, query ChromaDB, and filter by distance
    threshold. Returns found=False if nothing passes the bar - this is
    the FIRST line of defense against hallucination."""
    query_embedding = embedding_model.encode([question], normalize_embeddings=True).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    if not results["ids"][0]:
        return {"found": False, "chunks": [], "best_distance": None}

    distances = results["distances"][0]
    best_distance = min(distances)

    if best_distance > distance_threshold:
        return {"found": False, "chunks": [], "best_distance": best_distance}

    passing_chunks = []
    for i in range(len(results["ids"][0])):
        if distances[i] <= distance_threshold:
            passing_chunks.append(
                {
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "distance": distances[i],
                    **results["metadatas"][0][i],
                }
            )
    return {"found": True, "chunks": passing_chunks, "best_distance": best_distance}


def build_full_prompt(question: str, retrieval_result: dict) -> str:
    """Assembles the user-turn content: labeled retrieved context + question."""
    context_text = format_retrieved_context(retrieval_result.get("chunks", []))
    return f"""RETRIEVED CONTEXT:
{context_text}

QUESTION: {question}

ANSWER:"""


def generate_response(system_message: str, user_message: str, max_new_tokens: int = 400) -> str:
    """Calls the Claude API for generation, or returns mock placeholder
    text if MOCK_MODE is active (no API key configured yet)."""
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


def rewrite_query_with_history(question: str, session: ConversationSession) -> str:
    """Resolves ambiguous follow-up questions into fully self-contained
    questions BEFORE retrieval."""
    if not session.has_history():
        return question

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
                "distance": chunk["distance"],
            }
        )
    return citations


def run_full_pipeline(
    question: str,
    session: ConversationSession,
    collection,
    embedding_model,
    top_k: int = 4,
    distance_threshold: float = 0.85,
) -> dict:
    """The complete pipeline: memory -> retrieval -> prompting ->
    generation -> citations."""
    start_time = time.perf_counter()

    resolved_question = rewrite_query_with_history(question, session)

    retrieval_result = retrieve_relevant_chunks(
        resolved_question, collection, embedding_model, top_k, distance_threshold
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

    full_prompt = build_full_prompt(resolved_question, retrieval_result)
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