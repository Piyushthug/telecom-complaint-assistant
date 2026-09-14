"""LangGraph orchestration for the complaint resolution workflow.

    START --> analyze_sentiment --\
    START --> categorization ------+--> summarize --> check_history --> rag_retrieve
                                                                          |
                                                                          v
                                                                 generate_response
                                                                          |
                                                                          v
                                                                      validate
                                                                     /    |    \
                                                                  PASS  RETRY  MAX_RETRIES
                                                                   |      |         |
                                                                  END <---+     escalate --> END
"""
from functools import lru_cache
from typing import Optional

from langgraph.graph import StateGraph, START, END

from backend import config
from backend.agents import (
    categorization_agent,
    history_agent,
    response_agent,
    sentiment_agent,
    summarization_agent,
    validator_agent,
)
from backend.graph.progress import ProgressTracker
from backend.graph.state import ComplaintState
from backend.rag import retriever
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

_progress_tracker: Optional[ProgressTracker] = None

def set_progress_tracker(tracker: ProgressTracker) -> None:
    global _progress_tracker
    _progress_tracker = tracker

def record_progress(step: str, status: str, message: str) -> None:
    if _progress_tracker:
        _progress_tracker.record(step, status, message)


def _rag_retrieve_node(state: ComplaintState) -> dict:
    record_progress("rag_retrieve", "started", "Retrieving relevant policies...")
    query = f"{state.get('category', '')}: {state['complaint']}"
    retrieved_documents = retriever.retrieve(query, top_k=config.TOP_K)
    record_progress("rag_retrieve", "completed", f"Retrieved {len(retrieved_documents)} policy excerpts")
    return {"retrieved_documents": retrieved_documents}


def _escalate_node(state: ComplaintState) -> dict:
    sources = sorted({doc["document"] for doc in state.get("retrieved_documents", [])})
    fallback_response = (
        "Thank you for reaching out, and I'm sorry for the ongoing trouble. "
        "I wasn't able to confidently confirm a resolution for this from our current "
        "policy information, so I'm escalating this complaint to a human support "
        "representative who can review your account and take the next steps."
    )
    logger.warning(
        "Escalating complaint after %s failed validation attempt(s). policy_sources=%s",
        state.get("retry_count"),
        sources,
    )
    return {
        "suggested_response": fallback_response,
        "validation_status": "ESCALATED",
        "escalated": True,
    }


def _route_after_validation(state: ComplaintState) -> str:
    if state.get("validation_status") == "PASS":
        return "end"
    if state.get("retry_count", 0) >= config.MAX_RETRIES:
        return "escalate"
    return "retry"


def _wrap_agent(agent_func, node_name: str, display_name: str):
    def wrapped(state: ComplaintState):
        record_progress(node_name, "started", f"{display_name}...")
        result = agent_func(state)
        record_progress(node_name, "completed", f"{display_name} complete")
        return result
    return wrapped


def build_graph():
    graph = StateGraph(ComplaintState)

    graph.add_node("analyze_sentiment", _wrap_agent(sentiment_agent.run, "analyze_sentiment", "Analyzing sentiment"))
    graph.add_node("categorization", _wrap_agent(categorization_agent.run, "categorization", "Categorizing complaint"))
    graph.add_node("summarize", _wrap_agent(summarization_agent.run, "summarize", "Summarizing complaint"))
    graph.add_node("check_history", _wrap_agent(history_agent.run, "check_history", "Checking complaint history"))
    graph.add_node("rag_retrieve", _rag_retrieve_node)
    graph.add_node("generate_response", _wrap_agent(response_agent.run, "generate_response", "Generating response"))
    graph.add_node("validate", _wrap_agent(validator_agent.run, "validate", "Validating response"))
    graph.add_node("escalate", _escalate_node)

    # Sentiment and categorization are independent analyses of the same
    # complaint text, so they run in parallel and fan in to "summarize".
    graph.add_edge(START, "analyze_sentiment")
    graph.add_edge(START, "categorization")
    graph.add_edge("analyze_sentiment", "summarize")
    graph.add_edge("categorization", "summarize")

    graph.add_edge("summarize", "check_history")
    graph.add_edge("check_history", "rag_retrieve")
    graph.add_edge("rag_retrieve", "generate_response")
    graph.add_edge("generate_response", "validate")

    graph.add_conditional_edges(
        "validate",
        _route_after_validation,
        {
            "end": END,
            "retry": "generate_response",
            "escalate": "escalate",
        },
    )
    graph.add_edge("escalate", END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_compiled_graph():
    return build_graph()
