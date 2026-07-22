"""
build_vector_db.py - Upserts chunks + embeddings + metadata into the
Supabase pgvector table `law_chunks`. Idempotent - safe to re-run.

REPLACES the ChromaDB version. Same input files (chunks.json,
embeddings.npy), same batching approach - only the destination
changed, from a local ChromaDB collection to Supabase/pgvector.

Prerequisite: run 001_create_law_chunks_pgvector.sql in the Supabase
SQL Editor once, before running this script.

Run: python scripts/build_vector_db.py
"""

import json
import sys
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

load_dotenv()  # same call main.py makes - needed here too since this
                # script runs standalone, not through main.py's startup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Same path convention pipeline.py already uses to reach rag_utils -
# supabase_client.py lives at backend/app/, per your confirmed layout.
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))
from supabase_client import get_supabase_admin_client

CHUNKS_PATH = DATA_PROCESSED_DIR / "chunks.json"
EMBEDDINGS_PATH = DATA_PROCESSED_DIR / "embeddings.npy"
TABLE_NAME = "law_chunks"
BATCH_SIZE = 100  # same batch size as the ChromaDB version


def main() -> None:
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    embeddings = np.load(EMBEDDINGS_PATH)

    assert len(chunks) == embeddings.shape[0], (
        f"Mismatch: {len(chunks)} chunks but {embeddings.shape[0]} embeddings."
    )
    print(f"Loaded {len(chunks)} chunks and {embeddings.shape[0]} embeddings - matched.")
    print(f"Embedding dimension: {embeddings.shape[1]} (should be 1024 for BGE-M3)")

    client = get_supabase_admin_client()

    total = len(chunks)
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_chunks = chunks[start:end]
        batch_embeddings = embeddings[start:end]

        rows = []
        for chunk, embedding in zip(batch_chunks, batch_embeddings):
            rows.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "source_filename": chunk["source_filename"],
                    "title": chunk["title"],
                    "law_number": chunk["law_number"],
                    "category": chunk["category"],
                    "start_page": chunk["start_page"],
                    "end_page": chunk["end_page"],
                    "char_count": chunk["char_count"],
                    # supabase-py serializes this Python list to JSON;
                    # Postgres/pgvector casts a JSON numeric array
                    # directly into the vector type on insert.
                    "embedding": embedding.tolist(),
                }
            )

        # upsert on chunk_id (the primary key) - matches the
        # idempotent "safe to re-run" behavior of the original
        # ChromaDB script.
        client.table(TABLE_NAME).upsert(rows, on_conflict="chunk_id").execute()
        print(f"  Upserted chunks {start}-{end - 1} of {total}")

    count_result = (
        client.table(TABLE_NAME)
        .select("chunk_id", count="exact")
        .execute()
    )
    print(f"\nTable '{TABLE_NAME}' now contains {count_result.count} items.")


if __name__ == "__main__":
    main()