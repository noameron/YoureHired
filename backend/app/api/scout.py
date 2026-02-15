import logging

from fastapi import APIRouter, HTTPException

from app.schemas.scout import DeveloperProfile, DeveloperProfileResponse, ProfileIdResponse
from app.services.github_repos_db import github_repos_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scout"])


@router.post("/scout/profile")
async def save_profile(profile: DeveloperProfile) -> ProfileIdResponse:
    """Save or update the developer profile."""
    profile_id = await github_repos_db.save_profile(profile)
    return ProfileIdResponse(id=profile_id)


@router.get("/scout/profile")
async def get_profile() -> DeveloperProfileResponse:
    """Retrieve the developer profile."""
    profile = await github_repos_db.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No developer profile found")
    return profile
