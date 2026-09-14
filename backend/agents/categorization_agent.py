"""Determines complaint category from a controlled, fixed list of categories."""
from backend import config
from backend.graph.state import ComplaintState
from backend.llm import llm_client
from backend.utils.parsing import extract_json

PROMPT_TEMPLATE = """You are a telecom customer support complaint classifier.

Classify the complaint below into exactly one of these categories:
{categories}

Complaint:
\"\"\"{complaint}\"\"\"

Respond with ONLY a JSON object in this exact format, no other text:
{{"category": "<ONE_OF_THE_CATEGORIES>", "confidence": <number between 0 and 1>}}
"""

DEFAULT_CATEGORY = "CUSTOMER_SERVICE"


def run(state: ComplaintState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        categories=", ".join(config.CATEGORIES),
        complaint=state["complaint"],
    )
    raw_response = llm_client.generate(prompt)

    try:
        parsed = extract_json(raw_response)
        category = str(parsed["category"]).strip().upper()
        confidence = float(parsed.get("confidence", 0.5))
    except (ValueError, KeyError, TypeError):
        category = DEFAULT_CATEGORY
        confidence = 0.0

    if category not in config.CATEGORIES:
        category = DEFAULT_CATEGORY

    return {"category": category, "category_confidence": confidence}
