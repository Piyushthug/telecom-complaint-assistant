"""Helpers for pulling structured data out of free-form LLM text."""
import json
import re
from typing import Any, Dict


def extract_json(text: str) -> Dict[str, Any]:
    """Extract the first JSON object found in an LLM response.

    LLMs sometimes wrap JSON in markdown fences or add surrounding prose;
    this pulls out the {...} block and parses it.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {text!r}")
    return json.loads(match.group(0))
