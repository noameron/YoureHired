from fastapi import APIRouter

from app.api.company_info import router as company_info_router
from app.api.roles import router as roles_router
from app.api.user_selection import router as user_selection_router

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "YoureHired API"}


router.include_router(roles_router)
router.include_router(user_selection_router)
router.include_router(company_info_router)
