"""High-level retrieval API used by the LangGraph workflow."""
from functools import lru_cache
from typing import List

from backend import config
from backend.rag import embeddings, faiss_store


@lru_cache(maxsize=1)
def _load() -> tuple:
    return faiss_store.load_index()


def retrieve(query: str, top_k: int = config.TOP_K) -> List[dict]:
    index, metadata = _load()
    query_embedding = embeddings.embed_query(query)
    return faiss_store.search(index, metadata, query_embedding, top_k=top_k)
