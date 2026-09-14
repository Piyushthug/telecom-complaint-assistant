"""Shared state passed between all agents in the LangGraph workflow."""
from typing import Any, Dict, List, TypedDict


class ComplaintState(TypedDict, total=False):
    complaint: str
    customer_id: str

    sentiment: str
    sentiment_confidence: float

    category: str
    category_confidence: float

    summary: str

    retrieved_documents: List[Dict[str, Any]]

    repeated_contact: bool
    previous_complaint_count: int

    suggested_response: str

    validation_status: str
    validation_reason: str

    retry_count: int
    escalated: bool
