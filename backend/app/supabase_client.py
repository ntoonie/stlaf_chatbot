import os
from supabase import create_client, Client

_client: Client | None = None


def get_supabase_admin_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in .env")
        _client = create_client(url, key)
    return _client


def get_or_create_chat_session(profile_id: str) -> str:
    """Returns an existing open chat_session id for this user, or
    creates a new one. Keeps it simple: one active session per user
    per backend process lifetime (matches the in-memory SessionStore's
    scope) rather than building session-expiry logic yet."""
    client = get_supabase_admin_client()

    existing = (
        client.table("chat_sessions")
        .select("id")
        .eq("profile_id", profile_id)
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if existing.data:
        return existing.data[0]["id"]

    created = client.table("chat_sessions").insert({"profile_id": profile_id}).execute()
    return created.data[0]["id"]


def persist_message(chat_session_id: str, role: str, content: str, citations: list | None = None) -> None:
    """Writes one message turn (user or assistant) to the messages table."""
    client = get_supabase_admin_client()
    client.table("messages").insert({
        "chat_session_id": chat_session_id,
        "role": role,
        "content": content,
        "citations": citations,
    }).execute()


def persist_usage_log(profile_id: str, latency_seconds: float, found_context: bool) -> None:
    """Writes one usage record - foundation for future billing/analytics (SAD Section 22)."""
    client = get_supabase_admin_client()
    client.table("usage_logs").insert({
        "profile_id": profile_id,
        "latency_seconds": latency_seconds,
        "found_context": found_context,
    }).execute()