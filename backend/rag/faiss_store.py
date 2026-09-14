"""Local FAISS vector store: build, save, load, search."""
import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np

from backend import config
from backend.rag.chunker import Chunk

INDEX_FILE = "index.faiss"
METADATA_FILE = "metadata.json"


def build_index(chunks: List[Chunk], embeddings: np.ndarray) -> faiss.Index:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine similarity via normalized vectors
    index.add(embeddings)
    return index


def save_index(index: faiss.Index, chunks: List[Chunk], directory: Path = config.FAISS_INDEX_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(directory / INDEX_FILE))

    metadata = [
        {"text": c.text, "source": c.source, "chunk_index": c.chunk_index}
        for c in chunks
    ]
    (directory / METADATA_FILE).write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def load_index(directory: Path = config.FAISS_INDEX_DIR) -> Tuple[faiss.Index, list]:
    index_path = directory / INDEX_FILE
    metadata_path = directory / METADATA_FILE
    if not index_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found in {directory}. Run scripts/build_faiss_index.py first."
        )
    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return index, metadata


def search(
    index: faiss.Index,
    metadata: list,
    query_embedding: np.ndarray,
    top_k: int = config.TOP_K,
) -> List[dict]:
    query_vector = np.expand_dims(query_embedding, axis=0)
    scores, indices = index.search(query_vector, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        entry = metadata[idx]
        results.append(
            {
                "document": entry["source"],
                "chunk_text": entry["text"],
                "similarity_score": float(score),
                "metadata": {"chunk_index": entry["chunk_index"]},
            }
        )
    return results
