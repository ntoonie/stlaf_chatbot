import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # reads .env for ANTHROPIC_API_KEY, SUPABASE_JWT_SECRET, etc.

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent.parent / "scripts"))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from schemas import ChatRequest, ChatResponse
from pipeline import run_full_pipeline, SessionStore
from auth import verify_jwt
from supabase_client import get_or_create_chat_session, persist_message, persist_usage_log

import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = BASE_DIR.parent.parent
CHROMA_DB_DIR = str(PROJECT_ROOT / "chroma_db")
COLLECTION_NAME = "ph_labor_law"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

app_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading ChromaDB collection...")
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    # get_or_create_collection so the app can start even with ZERO
    # documents indexed yet - correct for the current empty-corpus stage.
    app_state["collection"] = client.get_or_create_collection(name=COLLECTION_NAME)

    print("Loading embedding model...")
    app_state["embedding_model"] = SentenceTransformer(EMBEDDING_MODEL_NAME)

    app_state["session_store"] = SessionStore()
    print(f"Startup complete. Collection has {app_state['collection'].count()} indexed chunks.")

    yield
    app_state.clear()


app = FastAPI(title="Philippine Labor Law Chatbot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your actual frontend origin before production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "ready": "collection" in app_state,
        "indexed_chunks": app_state["collection"].count() if "collection" in app_state else 0,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: dict = Depends(verify_jwt)):
    if "collection" not in app_state:
        raise HTTPException(status_code=503, detail="Still starting up, try again shortly.")

    verified_user_id = user["sub"]
    session = app_state["session_store"].get_or_create(request.session_id)

    result = run_full_pipeline(
        request.question, session,
        app_state["collection"], app_state["embedding_model"],
    )

    try:
        chat_session_id = get_or_create_chat_session(verified_user_id)
        persist_message(chat_session_id, "user", request.question)
        persist_message(chat_session_id, "assistant", result["answer"], result.get("citations"))
        persist_usage_log(verified_user_id, result["latency_seconds"], result["found_context"])
    except Exception as e:
        print(f"WARNING: Failed to persist chat history to Supabase: {e}")

    return result