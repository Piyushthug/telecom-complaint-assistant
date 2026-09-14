"""Splits documents into overlapping text chunks for embedding."""
from dataclasses import dataclass
from typing import List

from backend import config
from backend.rag.document_loader import Document


@dataclass
class Chunk:
    text: str
    source: str
    chunk_index: int


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
        else:
            # Paragraph itself is too long; hard-split it.
            for start in range(0, len(paragraph), chunk_size - chunk_overlap):
                chunks.append(paragraph[start:start + chunk_size])
            current = ""

    if current:
        chunks.append(current)

    # Add overlap between consecutive chunks so context isn't lost at boundaries.
    overlapped: List[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0 or chunk_overlap <= 0:
            overlapped.append(chunk)
            continue
        prefix = chunks[i - 1][-chunk_overlap:]
        overlapped.append(f"{prefix}\n{chunk}")

    return overlapped


def chunk_documents(
    documents: List[Document],
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> List[Chunk]:
    all_chunks: List[Chunk] = []
    for document in documents:
        pieces = _split_text(document.content, chunk_size, chunk_overlap)
        for index, piece in enumerate(pieces):
            all_chunks.append(Chunk(text=piece, source=document.source, chunk_index=index))
    return all_chunks
