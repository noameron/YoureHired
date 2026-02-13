import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.constants import SSE_HEADERS
from app.schemas.company_info import (
    CompanyInfoData,
    CompanyInfoResponse,
    CompanySummary,
)
from app.services import session_store
from app.services.company_research import (
    consume_research_stream,
    research_company_stream,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["company-info"])


@router.get(
    "/company-info/{session_id}",
    response_model=CompanyInfoResponse,
)
async def get_company_info(session_id: str) -> CompanyInfoResponse:
    """Research and return company information for a session."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        summary = await consume_research_stream(
            company_name=session.company_name,
            role=session.role,
            session_id=session_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Store summary in session for drill generation
    session_store.update_company_summary(session_id, summary)

    return CompanyInfoResponse(
        data=CompanyInfoData(
            session_id=session_id,
            company_name=session.company_name,
            role=session.role,
            summary=summary,
        )
    )


async def _stream_error_session_not_found() -> AsyncGenerator[str, None]:
    """Generate SSE error for session not found."""
    yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"


async def _generate_research_events(
    session_id: str, company_name: str, role: str
) -> AsyncGenerator[str, None]:
    """Generate SSE events for company research stream."""
    async for event in research_company_stream(company_name, role, session_id):
        # Store company summary when research completes
        if event.get("type") == "complete" and "data" in event:
            try:
                # event["data"] is already a dict from the research stream
                summary = CompanySummary.model_validate(event["data"])
                session_store.update_company_summary(session_id, summary)
            except (ValidationError, TypeError) as e:
                # Log but don't block stream on invalid data
                logger.warning(f"Failed to parse company summary: {e}")
        yield f"data: {json.dumps(event)}\n\n"


@router.get("/company-research/{session_id}/stream")
async def stream_company_research(session_id: str) -> StreamingResponse:
    """Stream company research progress via Server-Sent Events."""
    session = session_store.get(session_id)

    if not session:
        return StreamingResponse(
            _stream_error_session_not_found(),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        _generate_research_events(session_id, session.company_name, session.role),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
