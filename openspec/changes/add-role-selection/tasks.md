# Tasks: Add Role Selection Feature

## Overview

Implementation tasks for the Role Selection feature following TDD approach. Tasks are ordered for incremental delivery with each task producing testable, working functionality.

**Total Tasks**: 12
**Parallelizable**: Backend (1-6) and Frontend (7-12) can be developed in parallel after task 1

---

## Backend Tasks

### Task 1: Add predefined roles configuration
**Priority**: P0 (Blocking)
**Files**: `backend/app/config.py`

Add the PREDEFINED_ROLES list to the settings configuration.

```python
PREDEFINED_ROLES = [
    {"id": "frontend_developer", "label": "Frontend Developer"},
    {"id": "backend_developer", "label": "Backend Developer"},
    {"id": "fullstack_developer", "label": "Full Stack Developer"},
    {"id": "devops_engineer", "label": "DevOps Engineer"},
    {"id": "qa_engineer", "label": "QA Engineer"},
    {"id": "data_engineer", "label": "Data Engineer"},
]
```

**Validation**: Config loads without error, roles accessible

---

### Task 2: Create GET /api/roles endpoint (TDD)
**Priority**: P0
**Files**:
- `backend/tests/test_roles.py` (write first)
- `backend/app/api/roles.py`
- `backend/app/api/__init__.py`

**TDD Steps**:
1. Write test `test_get_roles_returns_all_configured_roles`
2. Implement endpoint returning roles from config
3. Register router in `__init__.py`

**Validation**: `uv run pytest tests/test_roles.py` passes

---

### Task 3: Create Pydantic schemas for user selection
**Priority**: P0
**Files**: `backend/app/schemas/user_selection.py`

Create request and response models:
- `UserSelectionRequest`: company_name, role, role_description (optional)
- `UserSelectionResponse`: success, data, next_step
- `UserSelectionError`: success=false, error details

**Validation**: Models instantiate correctly with valid/invalid data

---

### Task 4: Create input sanitization utility
**Priority**: P1
**Files**:
- `backend/tests/test_sanitization.py` (write first)
- `backend/app/utils/sanitization.py`

**TDD Steps**:
1. Write tests for whitespace normalization, length limiting
2. Implement `sanitize_input()` function

**Validation**: `uv run pytest tests/test_sanitization.py` passes

---

### Task 5: Create POST /api/user-selection endpoint (TDD)
**Priority**: P0
**Files**:
- `backend/tests/test_user_selection.py` (write first)
- `backend/app/api/user_selection.py`
- `backend/app/api/__init__.py`

**TDD Steps**:
1. Write all tests from spec (see Test Coverage Requirements)
2. Implement endpoint with validation logic
3. Use sanitization utility for role_description
4. Generate session_id (UUID)
5. Register router

**Validation**: `uv run pytest tests/test_user_selection.py` passes

---

### Task 6: Backend integration test
**Priority**: P1
**Files**: `backend/tests/test_integration.py`

End-to-end test:
1. Fetch roles
2. Submit valid selection
3. Verify response format

**Validation**: `uv run pytest tests/test_integration.py` passes

---

## Frontend Tasks

### Task 7: Create TypeScript types for API
**Priority**: P0
**Files**: `frontend/src/types/api.ts`

Define interfaces:
- `Role`: id, label
- `RolesResponse`: roles array
- `UserSelectionRequest`: company_name, role, role_description
- `UserSelectionResponse`: success, data, next_step
- `UserSelectionError`: success, error details

**Validation**: TypeScript compiles without errors

---

### Task 8: Create userSelection Pinia store
**Priority**: P0
**Files**:
- `frontend/src/stores/__tests__/userSelection.spec.ts` (write first)
- `frontend/src/stores/userSelection.ts`

**TDD Steps**:
1. Write tests for store actions and state
2. Implement store with state: companyName, role, roleDescription, sessionId
3. Add actions: setSelection, clearSelection

**Validation**: `npm run test:run` passes for store tests

---

### Task 9: Create API service functions
**Priority**: P0
**Files**: `frontend/src/services/api.ts`

Implement:
- `fetchRoles()`: GET /api/roles
- `submitUserSelection(data)`: POST /api/user-selection

**Validation**: Functions compile, types are correct

---

### Task 10: Create RoleSelectionView component (TDD)
**Priority**: P0
**Files**:
- `frontend/src/views/__tests__/RoleSelectionView.spec.ts` (write first)
- `frontend/src/views/RoleSelectionView.vue`

**TDD Steps**:
1. Write component tests (see spec Test Coverage Requirements)
2. Implement form with:
   - Company name input (text, max 20 chars)
   - Role dropdown (populated from API)
   - Role description textarea (optional, max 500 chars)
   - Submit button
3. Add client-side validation
4. Connect to API service and Pinia store

**Validation**: `npm run test:run` passes for component tests

---

### Task 11: Add route for role selection
**Priority**: P0
**Files**: `frontend/src/router/index.ts`

Add route:
```typescript
{
  path: '/select-role',
  name: 'role-selection',
  component: () => import('@/views/RoleSelectionView.vue')
}
```

**Validation**: Navigation to /select-role renders the view

---

### Task 12: End-to-end manual verification
**Priority**: P1
**Depends on**: All previous tasks

Manual verification checklist:
- [ ] Navigate to /select-role
- [ ] Roles dropdown populated
- [ ] Submit without company name → error shown
- [ ] Submit without role → error shown
- [ ] Submit with long company name → error shown
- [ ] Submit valid form → success, store updated
- [ ] Check browser console for errors

**Validation**: All checklist items pass

---

## Dependency Graph

```
Task 1 (config)
    │
    ├──► Task 2 (GET /roles)
    │        │
    │        └──► Task 6 (integration)
    │
    ├──► Task 3 (schemas)
    │        │
    │        └──► Task 5 (POST /user-selection)
    │                 │
    │                 └──► Task 6 (integration)
    │
    └──► Task 4 (sanitization)
             │
             └──► Task 5 (POST /user-selection)

Task 7 (types) ──► Task 8 (store) ──► Task 10 (view)
       │                                    │
       └──► Task 9 (api service) ──────────┘
                                            │
                                            └──► Task 11 (router)
                                                      │
                                                      └──► Task 12 (e2e)
```

## Parallel Execution

**Stream A (Backend)**: Tasks 1 → 2/3/4 → 5 → 6
**Stream B (Frontend)**: Tasks 7 → 8/9 → 10 → 11 → 12

Frontend tasks 7-9 can start immediately. Task 10 can use mocked API responses for testing while waiting for backend to be ready.
