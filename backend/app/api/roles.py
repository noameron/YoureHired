from fastapi import APIRouter

from app.config import PREDEFINED_ROLES, RoleDict

router = APIRouter(tags=["roles"])


@router.get("/roles")
async def get_roles() -> dict[str, list[RoleDict]]:
    """Return all predefined roles."""
    return {"roles": PREDEFINED_ROLES}
