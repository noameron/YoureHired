# Design: Role Selection Feature

## Context

This is the first user-facing feature of YoureHired. The role selection flow is the entry point for the entire application - users must complete this step before they can receive tailored coding practice tasks. This design establishes patterns that will be reused throughout the application.

### Stakeholders
- End users (job candidates preparing for technical interviews)
- Backend team (API design patterns)
- Frontend team (form handling and state management patterns)

### Constraints
- Must follow TDD approach
- Must protect against prompt injection (user input will eventually reach LLM)
- Company validation skipped for MVP

## Goals / Non-Goals

### Goals
- Create a clean, user-friendly role selection form
- Establish reusable patterns for form validation (client + server)
- Store user selection for use in subsequent task generation
- Configurable role list that can be updated without code changes

### Non-Goals
- User authentication (not in MVP scope)
- Persisting selections to database (in-memory/session for MVP)
- External company validation API integration
- Difficulty level selection (mentioned in PRD but not in this feature scope)

## Technical Decisions

### 1. API Design

**Decision**: Use JSON request body for all parameters

```
POST /api/user-selection
Content-Type: application/json

{
  "company_name": "Google",
  "role": "backend_developer",
  "role_description": "Optional custom description..."
}
```

**Response (Success)**:
```json
{
  "success": true,
  "data": {
    "company_name": "Google",
    "role": "Backend Developer",
    "role_description": "...",
    "session_id": "uuid-here"
  },
  "next_step": "/api/generate-tasks"
}
```

**Response (Validation Error)**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "company_name": "Company name is required",
      "role": "Invalid role selected"
    }
  }
}
```

**Alternatives Considered**:
- Query parameters for company/role: Rejected - less RESTful, URL length limits
- GraphQL: Rejected - overkill for simple CRUD operations

### 2. Role Configuration

**Decision**: Store predefined roles in backend config.py

```python
# backend/app/config.py
PREDEFINED_ROLES = [
    {"id": "frontend_developer", "label": "Frontend Developer"},
    {"id": "backend_developer", "label": "Backend Developer"},
    {"id": "fullstack_developer", "label": "Full Stack Developer"},
    {"id": "devops_engineer", "label": "DevOps Engineer"},
    {"id": "qa_engineer", "label": "QA Engineer"},
    {"id": "data_engineer", "label": "Data Engineer"},
]
```

**Rationale**:
- Easy to update without database migrations
- Can be moved to database later if needed
- Roles exposed via `GET /api/roles` endpoint for frontend consumption

### 3. Frontend State Management

**Decision**: Use Pinia store for user selection state

```typescript
// frontend/src/stores/userSelection.ts
interface UserSelection {
  companyName: string
  role: string
  roleDescription: string
}
```

**Rationale**:
- Pinia is already in the project stack
- Selection state needed across multiple views (selection → task generation → feedback)
- Enables easy state persistence if needed later

### 4. Client-Side Validation

**Decision**: Validate before API call with clear error messages

| Field | Validation Rules |
|-------|-----------------|
| company_name | Required, max 20 chars, trimmed |
| role | Required, must match predefined role ID |
| role_description | Optional, max 500 chars |

**Rationale**:
- Immediate feedback improves UX
- Reduces unnecessary API calls
- Server-side validation still required for security

### 5. Input Sanitization (Prompt Injection Prevention)

**Decision**: Sanitize all text inputs on backend before storage/use

```python
def sanitize_input(text: str) -> str:
    """Remove potential prompt injection patterns."""
    # Strip excessive whitespace
    text = " ".join(text.split())
    # Limit length
    text = text[:500]
    # Additional sanitization as needed
    return text
```

**Rationale**:
- User input will eventually be used in LLM prompts
- Defense in depth - sanitize at API boundary
- More sophisticated sanitization can be added as LLM integration is built

## Component Architecture

```
Frontend                          Backend
─────────────────────────────────────────────────────────

RoleSelectionView.vue             GET /api/roles
  ├── Form inputs                   └── Returns predefined roles
  ├── Client validation
  └── Submit                      POST /api/user-selection
        │                           ├── Validate request
        ▼                           ├── Sanitize inputs
  userSelection store               └── Return success/error
        │
        ▼
  Router → TaskGeneration
  (future feature)
```

## File Changes

### Backend
| File | Change |
|------|--------|
| `app/config.py` | Add PREDEFINED_ROLES list |
| `app/api/roles.py` | NEW - GET /api/roles endpoint |
| `app/api/user_selection.py` | NEW - POST /api/user-selection endpoint |
| `app/api/__init__.py` | Register new routers |
| `app/schemas/user_selection.py` | NEW - Pydantic request/response models |
| `tests/test_roles.py` | NEW - Role endpoint tests |
| `tests/test_user_selection.py` | NEW - User selection tests |

### Frontend
| File | Change |
|------|--------|
| `src/views/RoleSelectionView.vue` | NEW - Role selection form |
| `src/stores/userSelection.ts` | NEW - Selection state store |
| `src/router/index.ts` | Add /select-role route |
| `src/types/api.ts` | NEW - API type definitions |
| `src/__tests__/RoleSelectionView.spec.ts` | NEW - Component tests |

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Role list becomes stale | Easy config update; can move to DB later |
| No company validation | Acceptable for MVP; can add API integration later |
| Session state lost on refresh | MVP accepts this; add persistence in future |
| Prompt injection via role_description | Input sanitization + length limits |

## Migration Plan

Not applicable - this is a new feature with no existing data or behavior to migrate.

## Open Questions

1. **Difficulty levels**: PRD mentions Junior/Mid/Senior levels. Should this be part of role selection or a separate step?
   - **Resolution**: Defer to task generation feature - not in current scope

2. **Session persistence**: Should selections persist across browser refreshes?
   - **Resolution**: Not for MVP; can add localStorage or backend sessions later
