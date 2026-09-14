"""Local embedding model wrapper (sentence-transformers)."""
from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from backend import config


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(config.EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(embeddings, dtype="float32")


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def embedding_dimension() -> int:
    return _get_model().get_sentence_embedding_dimension()
