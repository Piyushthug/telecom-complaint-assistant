"""Service layer for complaint operations — all business logic, no direct SQL from agents."""
from typing import Optional

from backend.db import database


def get_customer_complaints(customer_id: str) -> dict:
    """Retrieve all complaints for a customer with their statuses.

    This is the ONLY way agents can access complaint history — through this API.
    """
    history = database.get_customer_history(customer_id)

    if not history:
        return {
            "customer_id": customer_id,
            "complaint_count": 0,
            "complaints": [],
        }

    return {
        "customer_id": customer_id,
        "complaint_count": len(history),
        "complaints": [
            {
                "complaint_id": h["complaint_id"],
                "category": h["category"],
                "status": h["status"],
                "created_at": h["created_at"],
                "resolution_time_hours": h["resolution_time_hours"],
            }
            for h in history
        ],
    }


def get_complaint_details(complaint_id: str) -> Optional[dict]:
    """Retrieve details for a specific complaint."""
    # Could query a complaints table if it exists
    # For now, search in history
    # In a real system, this would join multiple tables
    return None  # Placeholder


def get_recent_complaint(customer_id: str) -> Optional[dict]:
    """Get the most recent complaint for a customer."""
    history = database.get_customer_history(customer_id)
    if history:
        return {
            "complaint_id": history[0]["complaint_id"],
            "category": history[0]["category"],
            "status": history[0]["status"],
            "created_at": history[0]["created_at"],
        }
    return None
