"""Checks local complaint history to detect repeated/unresolved contacts.

Repeated contact is only ever one signal among several (category, current
complaint, policy) - it must not by itself decide escalation.
"""
from backend import config
from backend.db import database
from backend.graph.state import ComplaintState


def run(state: ComplaintState) -> dict:
    customer_id = state.get("customer_id")
    category = state.get("category")

    if not customer_id or not category:
        return {"repeated_contact": False, "previous_complaint_count": 0}

    count = database.count_recent_same_category(customer_id, category)
    repeated_contact = count >= config.REPEATED_CONTACT_THRESHOLD

    return {"repeated_contact": repeated_contact, "previous_complaint_count": count}
