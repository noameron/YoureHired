import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services import research_company
from app.services.company_research import research_company_stream
from app.schemas.company_info import (
    CompanyInfoData,
    CompanyInfoResponse,
)
from app.services import session_store

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

    summary = await research_company(
        company_name=session.company_name,
        role=session.role,
    )

    return CompanyInfoResponse(
        data=CompanyInfoData(
            session_id=session_id,
            company_name=session.company_name,
            role=session.role,
            summary=summary,
        )
    )


@router.get("/company-research/{session_id}/stream")
async def stream_company_research(session_id: str):
    """Stream company research progress via Server-Sent Events."""
    session = session_store.get(session_id)

    if not session:
        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
        return StreamingResponse(
            error_gen(),
            media_type="text/event-stream",
        )

    async def event_generator():
        async for event in research_company_stream(session.company_name, session.role):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
