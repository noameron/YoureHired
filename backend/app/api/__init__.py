from fastapi import APIRouter

from app.api.roles import router as roles_router

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "YoureHired API"}


router.include_router(roles_router)
