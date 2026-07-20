"""
generate_embeddings.py - Converts chunks.json into embedding vectors
using sentence-transformers/all-MiniLM-L6-v2 (free, local, CPU-friendly).
Run: python scripts/generate_embeddings.py
"""

import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHUNKS_PATH = DATA_PROCESSED_DIR / "chunks.json"
EMBEDDINGS_PATH = DATA_PROCESSED_DIR / "embeddings.npy"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main() -> None:
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks.")

    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} (first run downloads ~90MB)...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"Model loaded. Output dimension: {model.get_sentence_embedding_dimension()}")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"\nSaved embeddings with shape {embeddings.shape} to {EMBEDDINGS_PATH.name}")


if __name__ == "__main__":
    main()