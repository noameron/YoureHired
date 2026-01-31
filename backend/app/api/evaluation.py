"""
API endpoints for solution evaluation.
"""

import asyncio
from pathlib import Path

from agents import Runner
from agents.exceptions import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from fastapi import APIRouter, HTTPException

from app.agents.evaluation import solution_evaluator_agent
from app.agents.guardrails.exceptions import (
    SAFE_INJECTION_MESSAGE,
    SAFE_LEAKAGE_MESSAGE,
)
from app.config import settings
from app.schemas.evaluation import (
    EvaluationData,
    EvaluationErrorDetail,
    EvaluationErrorResponse,
    EvaluationRequest,
    EvaluationResponse,
    SolutionFeedback,
)
from app.services.feedback_persistence import save_feedback
from app.services.session_store import session_store

router = APIRouter(tags=["evaluation"])


def _build_evaluator_input(
    drill_title: str,
    drill_description: str,
    drill_requirements: list[str],
    solution: str,
    company_name: str,
    role: str,
) -> str:
    """Build input prompt for the solution evaluator agent."""
    parts = [
        f"Company: {company_name}",
        f"Role: {role}",
        "",
        "ORIGINAL DRILL:",
        f"Title: {drill_title}",
        f"Description: {drill_description}",
        f"Requirements: {', '.join(drill_requirements)}",
        "",
        "USER'S SUBMITTED SOLUTION:",
        "```",
        solution[:10000],  # Truncate very long solutions
        "```",
    ]

    if len(solution) > 10000:
        parts.append("(Note: Solution was truncated for evaluation due to length)")

    return "\n".join(parts)


@router.post(
    "/evaluate-solution/{session_id}",
    response_model=EvaluationResponse,
    responses={
        400: {"model": EvaluationErrorResponse},
        404: {"model": EvaluationErrorResponse},
        500: {"model": EvaluationErrorResponse},
    },
)
async def evaluate_solution(
    session_id: str,
    request: EvaluationRequest,
) -> EvaluationResponse:
    """
    Evaluate a user's solution for the current drill.

    Returns structured feedback including score, strengths, improvements,
    and a summary for the next drill generation.
    """
    # Validate session exists
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=EvaluationErrorDetail(
                code="session_not_found",
                message="Session not found or expired",
            ).model_dump(),
        )

    # Validate drill exists
    if not session.current_drill:
        raise HTTPException(
            status_code=400,
            detail=EvaluationErrorDetail(
                code="no_drill",
                message="No drill found for this session. Generate a drill first.",
            ).model_dump(),
        )

    drill = session.current_drill

    # Build evaluator input
    evaluator_input = _build_evaluator_input(
        drill_title=drill.title,
        drill_description=drill.description,
        drill_requirements=drill.requirements,
        solution=request.solution,
        company_name=session.company_name,
        role=session.role,
    )

    try:
        # Run evaluator agent
        result = await asyncio.wait_for(
            Runner.run(solution_evaluator_agent, evaluator_input),
            timeout=settings.drill_generation_agent_timeout,
        )

        feedback: SolutionFeedback = result.final_output

        # Persist feedback to file
        # Use backend directory as project root for file storage
        project_root = Path(__file__).parent.parent.parent.parent
        feedback_path = save_feedback(
            feedback=feedback,
            company_name=session.company_name,
            role=session.role,
            drill_title=drill.title,
            project_root=project_root,
        )

        # Update session with feedback summary for next drill
        session_store.update_last_feedback_summary(session_id, feedback.summary_for_next_drill)

        return EvaluationResponse(
            data=EvaluationData(
                session_id=session_id,
                feedback=feedback,
                feedback_file_path=str(feedback_path),
            )
        )

    except InputGuardrailTripwireTriggered:
        raise HTTPException(
            status_code=400,
            detail=EvaluationErrorDetail(
                code="input_blocked",
                message=SAFE_INJECTION_MESSAGE,
            ).model_dump(),
        )
    except OutputGuardrailTripwireTriggered:
        raise HTTPException(
            status_code=500,
            detail=EvaluationErrorDetail(
                code="output_blocked",
                message=SAFE_LEAKAGE_MESSAGE,
            ).model_dump(),
        )
    except TimeoutError:
        raise HTTPException(
            status_code=500,
            detail=EvaluationErrorDetail(
                code="timeout",
                message="Evaluation timed out. Please try again.",
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=EvaluationErrorDetail(
                code="evaluation_failed",
                message=f"Evaluation failed: {e!s}",
            ).model_dump(),
        )
