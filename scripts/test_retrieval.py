"""Sanity-check script for the RAG pipeline (run after build_faiss_index.py).

Run with:
    python scripts/test_retrieval.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag import retriever

QUERIES = [
    ("My internet is completely down.", "Internet Outage Complaint Policy.md"),
    ("My internet is working but very slow.", "Slow Internet Troubleshooting SOP.md"),
    ("I was charged twice this month.", "Billing Complaint Policy.md"),
    ("Can I get my money back?", "Customer Refund Policy.md"),
    ("I contacted support three times and nothing happened.", "Customer Complaint Escalation Policy.md"),
]


def main() -> None:
    for query, expected_source in QUERIES:
        results = retriever.retrieve(query, top_k=3)
        top_sources = [r["document"] for r in results]
        hit = expected_source in top_sources
        status = "PASS" if hit else "FAIL"
        print(f"[{status}] query={query!r}")
        print(f"        expected~{expected_source} top_sources={top_sources}")


if __name__ == "__main__":
    main()
