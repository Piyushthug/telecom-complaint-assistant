"""Generates a customer-facing response grounded in retrieved policy content.

If the customer is asking for complaint status/lookup, the agent fetches real
data from the complaint API and includes it in the response.
"""
import json
import requests
from urllib.parse import urljoin

from backend.graph.state import ComplaintState
from backend.llm import llm_client

# Internal API base URL (backend talking to itself)
API_BASE_URL = "http://127.0.0.1:8000"


def _should_lookup_complaint(complaint_text: str) -> bool:
    """Detect if the customer is asking for complaint status/ID/history."""
    keywords = [
        "status of my",
        "complaint id",
        "complaint number",
        "complain id",
        "complain number",
        "previous complaint",
        "earlier complaint",
        "last complaint",
        "complaint status",
        "update on",
        "what happened to",
        "where is my",
    ]
    text_lower = complaint_text.lower()
    return any(keyword in text_lower for keyword in keywords)


def _fetch_complaint_history(customer_id: str) -> dict:
    """Call the complaints API to get real complaint data."""
    try:
        url = urljoin(API_BASE_URL, f"/complaints/{customer_id}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        # If API call fails, just log and continue with generic response
        pass
    return None


def _format_complaint_history(history: dict) -> str:
    """Format complaint history into a readable summary for the response."""
    if not history or history.get("complaint_count", 0) == 0:
        return ""

    lines = [f"\nYour complaint history ({history['complaint_count']} total):"]
    for complaint in history.get("complaints", [])[:5]:  # Show last 5
        status = complaint.get("status", "UNKNOWN").upper()
        complaint_id = complaint.get("complaint_id", "N/A")
        category = complaint.get("category", "GENERAL")
        created = complaint.get("created_at", "N/A")
        lines.append(f"  • {complaint_id} ({category}): {status} - {created}")

    return "\n".join(lines)


PROMPT_TEMPLATE = """You are a telecom customer support assistant drafting a reply to a customer complaint.

Customer complaint:
\"\"\"{complaint}\"\"\"

Category: {category}
Sentiment: {sentiment}
Summary: {summary}
Repeated contact for this issue: {repeated_contact} (previous related complaints on file: {previous_complaint_count})

Relevant policy excerpts (this is the ONLY source of truth for facts, procedures, and escalation rules):
{policy_context}

Instructions:
- Write a clear, professional, empathetic response addressed directly to the customer.
- Speak naturally, in your own words, as a support agent would. Never mention "policy", "guidelines",
  "excerpts", or that you are following internal instructions - the customer should never see the
  reasoning process, only the resulting help.
- Base every factual claim, procedure, or escalation statement ONLY on what the policy excerpts support,
  but rephrase it as normal customer-facing language rather than quoting or paraphrasing the excerpt's wording.
- Do NOT invent refunds, ticket numbers, technician visits, outage causes, resolution times, or compensation
  unless the policy excerpts explicitly support them.
- If the customer expresses strong frustration, acknowledge it before providing next steps.
- If next steps are uncertain, it is fine to say the team needs to look into the account further -
  do not say things like "our policy doesn't cover this" or "I cannot confirm from current information".
{retry_note}
Suggested response:"""

RETRY_NOTE_TEMPLATE = """
Note: a previous draft of this response FAILED validation for this reason: "{reason}"
Fix that issue in this new draft.
"""


def _format_policy_context(retrieved_documents: list) -> str:
    if not retrieved_documents:
        return "(No relevant policy excerpts were retrieved.)"
    lines = []
    for doc in retrieved_documents:
        lines.append(f"- Source: {doc['document']}\n  \"{doc['chunk_text']}\"")
    return "\n".join(lines)


def run(state: ComplaintState) -> dict:
    retry_note = ""
    if state.get("validation_status") == "FAIL" and state.get("validation_reason"):
        retry_note = RETRY_NOTE_TEMPLATE.format(reason=state["validation_reason"])

    # Check if customer is asking for complaint lookup/status
    complaint_text = state.get("complaint", "")
    history_context = ""
    if _should_lookup_complaint(complaint_text):
        history = _fetch_complaint_history(state.get("customer_id", ""))
        if history:
            history_context = _format_complaint_history(history)

    prompt = PROMPT_TEMPLATE.format(
        complaint=state["complaint"],
        category=state.get("category", "UNKNOWN"),
        sentiment=state.get("sentiment", "UNKNOWN"),
        summary=state.get("summary", ""),
        repeated_contact=state.get("repeated_contact", False),
        previous_complaint_count=state.get("previous_complaint_count", 0),
        policy_context=_format_policy_context(state.get("retrieved_documents", [])),
        retry_note=retry_note,
    )

    # If we have real complaint history, inject it into the prompt
    if history_context:
        prompt += f"\n\nCustomer complaint history retrieved from our system:{history_context}\n\nInclude this information in your response."

    suggested_response = llm_client.generate(prompt)
    return {"suggested_response": suggested_response}
