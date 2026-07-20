"""
build_vector_db.py - Upserts chunks + embeddings + metadata into a
persistent ChromaDB collection. Idempotent - safe to re-run.
Run: python scripts/build_vector_db.py
"""

import json
from pathlib import Path
import numpy as np
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"

CHUNKS_PATH = DATA_PROCESSED_DIR / "chunks.json"
EMBEDDINGS_PATH = DATA_PROCESSED_DIR / "embeddings.npy"
COLLECTION_NAME = "ph_labor_law"


def main() -> None:
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    embeddings = np.load(EMBEDDINGS_PATH)

    assert len(chunks) == embeddings.shape[0], (
        f"Mismatch: {len(chunks)} chunks but {embeddings.shape[0]} embeddings."
    )
    print(f"Loaded {len(chunks)} chunks and {embeddings.shape[0]} embeddings - matched.")

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Philippine Labor Law RAG chatbot corpus"},
    )

    batch_size = 100
    total = len(chunks)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_chunks = chunks[start:end]
        batch_embeddings = embeddings[start:end]

        ids = [c["chunk_id"] for c in batch_chunks]
        documents = [c["text"] for c in batch_chunks]
        embeddings_list = batch_embeddings.tolist()
        metadatas = [
            {
                "source_filename": c["source_filename"],
                "title": c["title"],
                "law_number": c["law_number"],
                "category": c["category"],
                "start_page": c["start_page"],
                "end_page": c["end_page"],
            }
            for c in batch_chunks
        ]
        collection.upsert(ids=ids, documents=documents, embeddings=embeddings_list, metadatas=metadatas)
        print(f"  Upserted chunks {start}-{end - 1} of {total}")

    print(f"\nCollection '{collection.name}' now contains {collection.count()} items.")


if __name__ == "__main__":
    main()