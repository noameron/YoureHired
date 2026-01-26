"""
API endpoints for drill generation.
"""
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.drill import (
    Drill,
    DrillGenerationData,
    DrillGenerationResponse,
    DrillType,
)
from app.services.company_research import research_company_stream
from app.services.drill_generation import generate_drill, generate_drill_stream
from app.services.session_store import session_store

router = APIRouter(tags=["drill"])


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

    # Run research if not already done
    company_summary = session.company_summary
    if not company_summary:
        async for event in research_company_stream(
            session.company_name,
            session.role,
        ):
            if event["type"] == "complete":
                from app.schemas.company_info import CompanySummary

                company_summary = CompanySummary.model_validate(event["data"])
                session_store.update_company_summary(session_id, company_summary)
            # For non-streaming, we ignore status/error and continue

    drill: Drill = await generate_drill(
        company_name=session.company_name,
        role=session.role,
        role_description=session.role_description,
        company_summary=company_summary,
    )

    # Determine which generators were used
    from app.agents.drill import HOW_MANY_GENERATORS

    generator_names = [
        DrillType.CODING.value,
        DrillType.DEBUGGING.value,
        DrillType.SYSTEM_DESIGN.value,
    ][:HOW_MANY_GENERATORS]

    return DrillGenerationResponse(
        data=DrillGenerationData(
            session_id=session_id,
            company_name=session.company_name,
            role=session.role,
            drill=drill,
            generation_metadata={
                "generators_used": generator_names,
            },
        )
    )


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

        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"

        return StreamingResponse(
            error_gen(),
            media_type="text/event-stream",
        )

    async def event_generator():
        company_summary = session.company_summary

        # If no research done yet, run it first
        if not company_summary:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Researching company...'})}\n\n"
            async for event in research_company_stream(
                session.company_name,
                session.role,
            ):
                if event["type"] == "status":
                    yield f"data: {json.dumps(event)}\n\n"
                elif event["type"] == "complete":
                    # Import here to avoid circular import
                    from app.schemas.company_info import CompanySummary

                    company_summary = CompanySummary.model_validate(event["data"])
                    session_store.update_company_summary(session_id, company_summary)
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Research complete, generating drill...'})}\n\n"
                elif event["type"] == "error":
                    # Research failed - continue without company context (degraded mode)
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Research unavailable, continuing without company context...'})}\n\n"

        # Now generate the drill
        async for event in generate_drill_stream(
            company_name=session.company_name,
            role=session.role,
            role_description=session.role_description,
            company_summary=company_summary,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
