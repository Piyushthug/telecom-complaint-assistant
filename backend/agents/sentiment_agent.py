"""Analyzes customer sentiment. Runs in parallel with the categorization agent."""
from backend import config
from backend.graph.state import ComplaintState
from backend.llm import llm_client
from backend.utils.parsing import extract_json

PROMPT_TEMPLATE = """You are a telecom customer support sentiment classifier.

Classify the sentiment of the customer complaint below into exactly one of:
{sentiments}

Complaint:
\"\"\"{complaint}\"\"\"

Respond with ONLY a JSON object in this exact format, no other text:
{{"sentiment": "<ONE_OF_THE_LABELS>", "confidence": <number between 0 and 1>}}
"""


def run(state: ComplaintState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        sentiments=", ".join(config.SENTIMENTS),
        complaint=state["complaint"],
    )
    raw_response = llm_client.generate(prompt)

    try:
        parsed = extract_json(raw_response)
        sentiment = str(parsed["sentiment"]).strip().upper()
        confidence = float(parsed.get("confidence", 0.5))
    except (ValueError, KeyError, TypeError):
        sentiment = "NEUTRAL"
        confidence = 0.0

    if sentiment not in config.SENTIMENTS:
        sentiment = "NEUTRAL"

    return {"sentiment": sentiment, "sentiment_confidence": confidence}
