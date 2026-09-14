"""Produces a concise summary of the complaint for downstream agents."""
from backend.graph.state import ComplaintState
from backend.llm import llm_client

PROMPT_TEMPLATE = """Summarize the following telecom customer complaint in 1-3 sentences.
Be factual and do not add information that is not in the complaint.

Category: {category}
Sentiment: {sentiment}

Complaint:
\"\"\"{complaint}\"\"\"

Summary:"""


def run(state: ComplaintState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        category=state.get("category", "UNKNOWN"),
        sentiment=state.get("sentiment", "UNKNOWN"),
        complaint=state["complaint"],
    )
    summary = llm_client.generate(prompt)
    return {"summary": summary}
