"""Thin wrapper around the LLM provider.

The rest of the application only calls `generate(prompt)`. This keeps the
LLM provider replaceable (Gemini today, Ollama or anything else tomorrow)
without touching agent code.
"""
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from backend import config


@lru_cache(maxsize=1)
def _get_model() -> ChatGoogleGenerativeAI:
    if not config.GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env file "
            "(see .env.example)."
        )
    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        temperature=config.GEMINI_TEMPERATURE,
        google_api_key=config.GOOGLE_API_KEY,
    )


def generate(prompt: str) -> str:
    """Send a prompt to the LLM and return its raw text response."""
    model = _get_model()
    response = model.invoke(prompt)
    return response.content.strip()
