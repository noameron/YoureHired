# Plan 3: Profile API

**Branch:** `scout/03-profile-api`
**Depends on:** plan_2 (needs `scout_db.py`)
**Blocks:** plan_7

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "New API endpoints for [...] managing profiles"
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 3.2 (router endpoints), Task 3.3 (include router), Task 3.4 (tests)

## Production Files (2)

### 1. CREATE `backend/app/api/scout.py`

Follow pattern from `backend/app/api/company_info.py` and `backend/app/api/drill.py`.

```python
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.scout import DeveloperProfile, DeveloperProfileResponse
from app.services.scout_db import scout_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scout"])


@router.post("/scout/profile")
async def save_profile(profile: DeveloperProfile) -> dict[str, str]:
    """Save or update the developer profile."""
    profile_id = await scout_db.save_profile(profile)
    return {"id": profile_id}


@router.get("/scout/profile")
async def get_profile() -> DeveloperProfileResponse:
    """Retrieve the developer profile."""
    profile = await scout_db.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No developer profile found")
    return profile
```

### 2. MODIFY `backend/app/api/__init__.py`

Add after line 7 (`from app.api.user_selection import router as user_selection_router`):

```python
from app.api.scout import router as scout_router
```

Add after line 21 (`router.include_router(evaluation_router)`):

```python
router.include_router(scout_router)
```

## Test Files

- `backend/tests/test_scout_profile_api.py`
  - `POST /api/scout/profile` with valid data → 200, returns `{"id": "default"}`
  - `GET /api/scout/profile` after save → 200, returns full profile
  - `GET /api/scout/profile` when empty → 404
  - `POST /api/scout/profile` twice → second overwrites first
  - `POST /api/scout/profile` with empty languages → 422 validation error
  - `POST /api/scout/profile` with goals > 500 chars → 422

**Test pattern:** Use `httpx.AsyncClient` with `ASGITransport(app=app)` as in `backend/tests/test_main.py`.

## Edge Cases

- Invalid data (empty languages, goals too long) → automatic 422 from Pydantic
- GET before any POST → 404
- POST overwrites previous → `INSERT OR REPLACE` in `scout_db.save_profile`
- Extra fields in POST body → ignored by Pydantic

## Verification

```bash
cd backend && uv run pytest tests/test_scout_profile_api.py -v
```
