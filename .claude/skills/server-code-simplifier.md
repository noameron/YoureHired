---
name: server-code-simplifier
description: "Server code simplification for FastAPI + Python 3.11+ + Pydantic + uv stack. Use when user asks to 'simplify backend code', 'clean up FastAPI routes', 'extract business logic to services', 'reduce route handler size', or 'prepare backend for review'. Enforces thin routes, proper extraction, and production-ready structure."
user-invocable: false
---

# Server Code Simplification

**Stack:** FastAPI | Python 3.11+ | Pydantic | uv

**Goal:** Thin routes, fat services. Routes handle HTTP, services handle logic.

## Size Limits

| Element | Max | Severity |
|---------|-----|----------|
| Route handler | 25 | 🟠 High |
| `router.py` total | 100 | 🟠 High |
| Service method | 40 | 🟡 Medium |
| **Any single file** | 200 | 🔴 Critical |
| Function parameters | 5 | 🟢 Low |

## Project Structure

```
app/{domain}/
├── router.py       # Route handlers ONLY
├── schemas.py      # Pydantic models
├── service.py      # Business logic
├── dependencies.py # Depends() functions
├── exceptions.py   # Domain exceptions
├── constants.py    # Domain constants
└── utils.py        # Helper functions
```

## Extraction Rules

### 1. Business Logic → Services
**Detect:** Handler > 25 lines, data transformation, API/agent calls | **Severity:** 🔴/🟠

Extract to `service.py`. Handler should ONLY: receive request → call ONE service method → return response.

### 2. Validation → Dependencies
**Detect:** `if not x: raise HTTPException(...)` in handler | **Severity:** 🟠 High

Extract to `dependencies.py` → use `Depends()` in route signature.

### 3. Exception Handling → Domain Exceptions
**Detect:** Multiple try/except blocks in handler | **Severity:** 🟡/🟠

Extract to `exceptions.py`. Service raises domain exceptions, router maps to HTTPException.

### 4. Helper Functions → Utils
**Detect:** `def _helper()` in router | **Severity:** 🟡 Medium

Extract to `utils.py` (multi-use) or private service method (single-use).

### 5. Pydantic Models → Schemas
**Detect:** Models defined in router/service | **Severity:** 🟡 Medium

Extract to `schemas.py`. Naming: `{Entity}Create`, `{Entity}Update`, `{Entity}Response`.

### 6. Constants → Constants File
**Detect:** Magic numbers, hardcoded limits | **Severity:** 🟢 Low

Extract to `constants.py` with ALL_CAPS names.

### 7. Configuration → Settings
**Detect:** `os.getenv()` scattered in code | **Severity:** 🟡 Medium

Extract to `core/config.py` → Pydantic `BaseSettings`.

## Anti-Patterns

**Router:** Handler > 25 lines, business logic, direct DB queries, multiple try/except, print()

**Service:** Method > 40 lines, HTTP concepts (HTTPException, status codes)

**General:** Bare `except:`, missing type hints, unused imports (F401)

## What Goes Where

| Code Type | Location |
|-----------|----------|
| `@router.get/post/...` | `router.py` |
| Pydantic models | `schemas.py` |
| Business logic | `service.py` |
| `Depends()` functions | `dependencies.py` |
| Domain exceptions | `exceptions.py` |

## Analysis Commands

```bash
# Ruff analysis
cd backend && uv run ruff check --select=F401,F841,C901 .

# Find violations
wc -l backend/app/**/*.py | sort -n
grep -c "raise HTTPException" backend/app/**/router.py
grep -c "try:" backend/app/**/router.py
grep -n "^def _" backend/app/**/router.py
```

## Output Format

```
### Server Analysis: `app/domain/router.py`

**Size:** XX lines | **Handlers:** N, avg XX lines

| # | Sev | Rule | Location | Issue |
|---|-----|------|----------|-------|
| 1 | 🔴 | Handler | L58-145 | 87 lines (limit 25) |
| 2 | 🟠 | Validation | L65-78 | Manual checks in handler |

**Extraction plan:**
1. Create `DomainService` in `service.py`
2. Move validation to dependency
```

## Refactoring Priority

1. 🔴 Extract service — if handler > 25 lines
2. 🟠 Extract dependencies — if validation in handler
3. 🟠 Extract exceptions — if 3+ exception types
4. 🟡 Extract helpers — if functions in router
5. 🟡 Extract schemas — if models in router
6. 🟢 Extract constants — if magic numbers present
