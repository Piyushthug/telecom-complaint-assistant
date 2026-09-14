"""Loads markdown knowledge-base documents from disk."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from backend import config


@dataclass
class Document:
    source: str
    content: str


def load_documents(directory: Path = config.KNOWLEDGE_BASE_DIR) -> List[Document]:
    documents = []
    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        documents.append(Document(source=path.name, content=content))
    return documents
