"""
API endpoints for drill generation.
"""

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.drill import HOW_MANY_GENERATORS
from app.constants import SSE_HEADERS
from app.schemas.company_info import CompanySummary
from app.schemas.drill import (
    CancelResponse,
    Drill,
    DrillGenerationData,
    DrillGenerationResponse,
    DrillType,
    GenerationMetadata,
)
from app.services.company_research import (
    ensure_company_research,
    research_company_stream,
)
from app.services.drill_generation import generate_drill, generate_drill_stream
from app.services.session_store import Session, session_store
from app.services.task_registry import task_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["drill"])


@router.post("/cancel/{session_id}", response_model=CancelResponse, status_code=200)
async def cancel_generation(session_id: str) -> CancelResponse:
    """Cancel all active agent runs for a session."""
    logger.info("Cancellation requested for session %s", session_id)
    task_registry.cancel_all(session_id)
    return CancelResponse(status="cancelled")


async def _generate_sse_error(message: str) -> AsyncGenerator[str, None]:
    """Generate SSE error event."""
    yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"


def _sse_error_response(message: str) -> StreamingResponse:
    """Create an SSE error response."""
    return StreamingResponse(
        _generate_sse_error(message), media_type="text/event-stream", headers=SSE_HEADERS
    )


def _get_generation_metadata() -> GenerationMetadata:
    """Build drill generation metadata."""
    generator_names = [
        DrillType.CODING.value,
        DrillType.DEBUGGING.value,
        DrillType.SYSTEM_DESIGN.value,
    ][:HOW_MANY_GENERATORS]
    return GenerationMetadata(generators_used=generator_names)


async def _stream_research_events(
    session_id: str, company_name: str, role: str
) -> AsyncGenerator[str, None]:
    """Stream company research events with status updates."""
    yield f"data: {json.dumps({'type': 'status', 'message': 'Researching company...'})}\n\n"
    async for event in research_company_stream(company_name, role, session_id):
        if event["type"] == "status":
            yield f"data: {json.dumps(event)}\n\n"
        elif event["type"] == "complete":
            company_summary = CompanySummary.model_validate(event["data"])
            session_store.update_company_summary(session_id, company_summary)
            status = {"type": "status", "message": "Research complete, generating drill..."}
            yield f"data: {json.dumps(status)}\n\n"
        elif event["type"] == "error":
            # Research failed - continue without company context (degraded mode)
            status = {
                "type": "status",
                "message": "Research unavailable, continuing without company context...",
            }
            yield f"data: {json.dumps(status)}\n\n"


async def _run_research_if_needed(
    session: Session, session_id: str
) -> tuple[CompanySummary | None, AsyncGenerator[str, None] | None]:
    """
    Run company research if not already available.
    Returns (company_summary, status_events_generator).
    For streaming, returns the generator for events; for non-streaming, returns None.
    """
    company_summary = session.company_summary
    if company_summary:
        return company_summary, None

    return company_summary, _stream_research_events(
        session_id, session.company_name, session.role
    )


@router.post(
    "/generate-drill/{session_id}",
    response_model=DrillGenerationResponse,
)
async def generate_drill_endpoint(session_id: str) -> DrillGenerationResponse:
    """
    Generate a practice drill for the given session.

    Uses session data (company, role, role_description) and company research
    (if available) to create a tailored coding/debugging/design challenge.
    Runs research internally if not already available.
    """
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    company_summary = await ensure_company_research(session, session_id)

    drill: Drill = await generate_drill(
        company_name=session.company_name,
        role=session.role,
        session_id=session_id,
        role_description=session.role_description,
        company_summary=company_summary,
        previous_feedback_summary=session.last_feedback_summary,
    )

    session_store.update_current_drill(session_id, drill)

    return DrillGenerationResponse(
        data=DrillGenerationData(
            session_id=session_id,
            company_name=session.company_name,
            role=session.role,
            drill=drill,
            generation_metadata=_get_generation_metadata(),
        )
    )


async def _generate_drill_stream_events(
    session: Session, session_id: str
) -> AsyncGenerator[str, None]:
    """Generate SSE events for drill generation, including research phase if needed."""
    try:
        # Run research phase if needed
        company_summary, research_gen = await _run_research_if_needed(session, session_id)
        if research_gen:
            async for event_str in research_gen:
                yield event_str
            # Re-fetch updated summary after research completes
            updated_session = session_store.get(session_id)
            company_summary = updated_session.company_summary if updated_session else None

        # Generate drill phase
        async for event in generate_drill_stream(
            company_name=session.company_name,
            role=session.role,
            session_id=session_id,
            role_description=session.role_description,
            company_summary=company_summary,
            previous_feedback_summary=session.last_feedback_summary,
        ):
            # Capture the drill when complete
            if event["type"] == "complete" and "data" in event:
                generated_drill = Drill.model_validate(event["data"])
                session_store.update_current_drill(session_id, generated_drill)
            yield f"data: {json.dumps(event)}\n\n"
    finally:
        task_registry.cleanup(session_id)


@router.get("/generate-drill/{session_id}/stream")
async def stream_drill_generation(session_id: str) -> StreamingResponse:
    """
    Stream drill generation progress via Server-Sent Events.

    Events:
    - status: Progress updates
    - candidate: When a candidate is generated
    - complete: Final drill result
    - error: Generation error
    """
    session = session_store.get(session_id)
    if not session:
        return _sse_error_response("Session not found")

    return StreamingResponse(
        _generate_drill_stream_events(session, session_id),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
