"""Validates the generated response against the retrieved policy context."""
from backend.graph.state import ComplaintState
from backend.llm import llm_client
from backend.utils.parsing import extract_json

PROMPT_TEMPLATE = """You are a strict compliance reviewer for a telecom customer support assistant.

Customer complaint:
\"\"\"{complaint}\"\"\"

Policy excerpts available to the assistant:
{policy_context}

Draft response to review:
\"\"\"{response}\"\"\"

Check ONLY the following substantive criteria:
1. Addresses the customer's complaint.
2. Does not state or imply any fact that contradicts or goes beyond the policy excerpts - specifically,
   does not invent refunds, ticket numbers, technician visits, outage causes, resolution times, or
   compensation unless the policy excerpts explicitly support them.
3. Does not make unsupported promises (e.g. guaranteeing a specific outcome, timeline, or compensation
   the policy excerpts do not confirm).
4. Does not contradict the applicable policy's rules or restrictions.

Do NOT fail the response for style, tone, phrasing, word choice, or for using generic professional
language such as "we will look into it" or "our team will review this" - those are acceptable ways to
express uncertainty without inventing facts. Only fail for concrete factual, promise, or policy violations.

Respond with ONLY a JSON object in this exact format, no other text:
{{"status": "PASS" or "FAIL", "reason": "<short explanation>"}}
"""


def _format_policy_context(retrieved_documents: list) -> str:
    if not retrieved_documents:
        return "(No relevant policy excerpts were retrieved.)"
    lines = []
    for doc in retrieved_documents:
        lines.append(f"- Source: {doc['document']}\n  \"{doc['chunk_text']}\"")
    return "\n".join(lines)


def run(state: ComplaintState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        complaint=state["complaint"],
        policy_context=_format_policy_context(state.get("retrieved_documents", [])),
        response=state.get("suggested_response", ""),
    )
    raw_response = llm_client.generate(prompt)

    try:
        parsed = extract_json(raw_response)
        status = str(parsed["status"]).strip().upper()
        reason = str(parsed.get("reason", "")).strip()
    except (ValueError, KeyError, TypeError):
        status = "FAIL"
        reason = "Validator could not parse a decision from the LLM response."

    if status not in ("PASS", "FAIL"):
        status = "FAIL"
        reason = reason or "Validator returned an unrecognized status."

    retry_count = state.get("retry_count", 0)
    if status == "FAIL":
        retry_count += 1

    return {
        "validation_status": status,
        "validation_reason": reason,
        "retry_count": retry_count,
    }
