"""FastAPI entrypoint exposing the complaint resolution workflow.

Run with:
    uvicorn backend.main:app --reload
"""
import asyncio
import json
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.graph.progress import ProgressTracker
from backend.graph.workflow import get_compiled_graph, set_progress_tracker
from backend.services.complaint_service import (
    get_customer_complaints,
    get_recent_complaint,
)
from backend.utils.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Telecom Complaint Resolution Assistant",
    description="Local, zero-cost AI assistant for triaging telecom customer complaints.",
    version="1.0.0",
)


class ComplaintRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    complaint: str = Field(..., min_length=1)


class PolicySource(BaseModel):
    document: str
    chunk_text: str
    similarity_score: float


class ComplaintResponse(BaseModel):
    request_id: str
    category: str
    sentiment: str
    summary: str
    response: str
    validation_status: str
    validation_reason: str
    repeated_contact: bool
    escalated: bool
    policy_sources: list[PolicySource]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/complaints/{customer_id}")
def get_complaints(customer_id: str) -> dict:
    """Retrieve all complaints for a customer.

    Used by response agent to provide accurate status updates.
    """
    return get_customer_complaints(customer_id)


@app.get("/complaints/{customer_id}/recent")
def get_recent(customer_id: str) -> dict:
    """Get the most recent complaint for a customer."""
    recent = get_recent_complaint(customer_id)
    if not recent:
        return {"error": f"No complaints found for customer {customer_id}"}
    return recent


async def _stream_complaint_progress(request: ComplaintRequest, request_id: str):
    """Stream progress events and final result via SSE."""
    progress_tracker = ProgressTracker()
    set_progress_tracker(progress_tracker)

    initial_state = {
        "complaint": request.complaint,
        "customer_id": request.customer_id,
        "retry_count": 0,
        "escalated": False,
    }

    async def generator():
        started_at = time.perf_counter()

        try:
            graph = get_compiled_graph()
            # Invoke graph in a thread pool so we don't block the event loop
            final_state = await asyncio.to_thread(graph.invoke, initial_state)

            # Emit all remaining progress events
            while True:
                event = progress_tracker.get_event()
                if not event:
                    break
                data = {
                    "type": "progress",
                    "step": event.step,
                    "status": event.status,
                    "message": event.message,
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(0.01)

            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

            logger.info(
                "request_id=%s customer_id=%s category=%s sentiment=%s "
                "validation_status=%s retry_count=%s escalated=%s latency_ms=%s",
                request_id,
                request.customer_id,
                final_state.get("category"),
                final_state.get("sentiment"),
                final_state.get("validation_status"),
                final_state.get("retry_count"),
                final_state.get("escalated", False),
                latency_ms,
            )

            response_data = ComplaintResponse(
                request_id=request_id,
                category=final_state.get("category", ""),
                sentiment=final_state.get("sentiment", ""),
                summary=final_state.get("summary", ""),
                response=final_state.get("suggested_response", ""),
                validation_status=final_state.get("validation_status", ""),
                validation_reason=final_state.get("validation_reason", ""),
                repeated_contact=final_state.get("repeated_contact", False),
                escalated=final_state.get("escalated", False),
                policy_sources=[
                    PolicySource(
                        document=doc["document"],
                        chunk_text=doc["chunk_text"],
                        similarity_score=doc["similarity_score"],
                    )
                    for doc in final_state.get("retrieved_documents", [])
                ],
            )
            yield f"data: {json.dumps({'type': 'result', 'data': response_data.model_dump()})}\n\n"
        except Exception as e:
            logger.exception("request_id=%s stream failed", request_id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return generator()


@app.post("/complaint", response_model=ComplaintResponse)
def resolve_complaint(request: ComplaintRequest) -> ComplaintResponse:
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()

    initial_state = {
        "complaint": request.complaint,
        "customer_id": request.customer_id,
        "retry_count": 0,
        "escalated": False,
    }

    try:
        graph = get_compiled_graph()
        final_state = graph.invoke(initial_state)
    except Exception:
        logger.exception("request_id=%s workflow failed", request_id)
        raise HTTPException(status_code=500, detail="Failed to process complaint.")

    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

    logger.info(
        "request_id=%s customer_id=%s category=%s sentiment=%s "
        "validation_status=%s retry_count=%s escalated=%s latency_ms=%s "
        "retrieved_documents=%s",
        request_id,
        request.customer_id,
        final_state.get("category"),
        final_state.get("sentiment"),
        final_state.get("validation_status"),
        final_state.get("retry_count"),
        final_state.get("escalated", False),
        latency_ms,
        [doc["document"] for doc in final_state.get("retrieved_documents", [])],
    )

    return ComplaintResponse(
        request_id=request_id,
        category=final_state.get("category", ""),
        sentiment=final_state.get("sentiment", ""),
        summary=final_state.get("summary", ""),
        response=final_state.get("suggested_response", ""),
        validation_status=final_state.get("validation_status", ""),
        validation_reason=final_state.get("validation_reason", ""),
        repeated_contact=final_state.get("repeated_contact", False),
        escalated=final_state.get("escalated", False),
        policy_sources=[
            PolicySource(
                document=doc["document"],
                chunk_text=doc["chunk_text"],
                similarity_score=doc["similarity_score"],
            )
            for doc in final_state.get("retrieved_documents", [])
        ],
    )


@app.post("/complaint-stream")
async def resolve_complaint_stream(request: ComplaintRequest):
    """Stream complaint processing progress and result as Server-Sent Events."""
    request_id = str(uuid.uuid4())
    generator = await _stream_complaint_progress(request, request_id)
    return StreamingResponse(generator, media_type="text/event-stream")
