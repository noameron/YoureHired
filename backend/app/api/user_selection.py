import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import PREDEFINED_ROLES
from app.services import session_store
from app.schemas.user_selection import (
    ErrorDetails,
    UserSelectionData,
    UserSelectionError,
    UserSelectionRequest,
    UserSelectionResponse,
)

router = APIRouter(tags=["user-selection"])

# Map role IDs to labels for response
ROLE_ID_TO_LABEL = {role["id"]: role["label"] for role in PREDEFINED_ROLES}


@router.post(
    "/user-selection",
    response_model=UserSelectionResponse,
    responses={
        400: {"model": UserSelectionError},
        422: {"description": "Validation Error"},
    },
)
async def create_user_selection(
    request: UserSelectionRequest,
) -> UserSelectionResponse | JSONResponse:
    """Submit user's company and role selection to start a practice session."""
    role_label = ROLE_ID_TO_LABEL.get(request.role)
    if role_label is None:
        return JSONResponse(
            status_code=400,
            content=UserSelectionError(
                error=ErrorDetails(
                    code="VALIDATION_ERROR",
                    message="Invalid role selection",
                    details={"role": f"Role '{request.role}' is not valid"},
                )
            ).model_dump(),
        )

    session_id = str(uuid.uuid4())

    session_store.create(
        session_id=session_id,
        company_name=request.company_name,
        role=role_label,
        role_description=request.role_description,
    )

    return UserSelectionResponse(
        data=UserSelectionData(
            company_name=request.company_name,
            role=role_label,
            role_description=request.role_description,
            session_id=session_id,
        )
    )
