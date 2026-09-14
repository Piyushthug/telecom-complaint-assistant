"""One-off script: load knowledge base -> chunk -> embed -> build & save FAISS index.

Run with:
    python scripts/build_faiss_index.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag import document_loader, chunker, embeddings, faiss_store


def main() -> None:
    documents = document_loader.load_documents()
    print(f"Loaded {len(documents)} documents from knowledge_base/")

    chunks = chunker.chunk_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    texts = [c.text for c in chunks]
    vectors = embeddings.embed_texts(texts)
    print(f"Generated embeddings with dimension {vectors.shape[1]}")

    index = faiss_store.build_index(chunks, vectors)
    faiss_store.save_index(index, chunks)
    print("FAISS index saved to backend/rag/index/")


if __name__ == "__main__":
    main()
