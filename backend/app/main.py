from fastapi import Depends
from auth import verify_jwt
from supabase_client import get_or_create_chat_session, persist_message, persist_usage_log

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: dict = Depends(verify_jwt)):
    if "collection" not in app_state:
        raise HTTPException(status_code=503, detail="Still starting up, try again shortly.")

    verified_user_id = user["sub"]

    session = app_state["session_store"].get_or_create(verified_user_id)
    result = run_full_pipeline(
        request.question, session,
        app_state["collection"], app_state["embedding_model"],
    )

    # Persist to Supabase for durable history/analytics - separate from
    # the in-memory SessionStore, which only exists for fast conversation
    # context resolution during query rewriting.
    try:
        chat_session_id = get_or_create_chat_session(verified_user_id)
        persist_message(chat_session_id, "user", request.question)
        persist_message(chat_session_id, "assistant", result["answer"], result.get("citations"))
        persist_usage_log(verified_user_id, result["latency_seconds"], result["found_context"])
    except Exception as e:
        # Persistence failure should NEVER break the actual chat response -
        # log it, but still return the answer to the user.
        print(f"WARNING: Failed to persist chat history to Supabase: {e}")

    return result