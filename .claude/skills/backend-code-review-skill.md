---
name: backend-code-review-skill
description: Conducts code review on Python 3.11+ and FastAPI backend changes. Checks type hints, Pydantic models, async patterns, security, SOLID principles, and clean code. Used exclusively by pr-review for backend/ directory changes.
user-invocable: false
context: fork
agent: pr-review
allowed-tools: Bash, Read, Grep, Glob
---

# Backend Code Review Skill

Code reviewer for Python 3.11+ FastAPI backend in the `backend/` directory.

## Review Workflow

1. **Count Changed Files**
   ```bash
   git diff --name-only HEAD -- backend/ | wc -l
   ```
   If > 8 files, flag as warning (not blocking).

2. **Run Verification**
   ```bash
   cd backend && uv run ruff check . && uv run mypy app && uv run pytest
   ```
   Stop and report immediately if any fail.

3. **Read and Analyze Each Changed File**

4. **Generate Report**

---

## Review Criteria

### BLOCKING (Stop Review)
- `uv run ruff check .` has errors
- `uv run mypy app` has errors
- `uv run pytest` fails

### CRITICAL (Must Fix)

**Security**
- Hardcoded credentials (API keys, tokens, passwords)
- SQL injection vulnerabilities (raw string queries)
- Missing input validation on endpoints
- Secrets in logs or error messages
- Missing authentication on protected routes

**Test Compliance**
- New endpoints/functions require test coverage
- Tests follow `# GIVEN / # WHEN / # THEN` structure

```python
async def test_create_user(client: AsyncClient):
    # GIVEN
    user_data = {"email": "test@example.com", "name": "Test"}

    # WHEN
    response = await client.post("/api/users", json=user_data)

    # THEN
    assert response.status_code == 201
```

### HIGH (Should Fix)

**Type Hints**
- Missing return type annotations
- Using `Any` without justification
- Missing parameter type hints on public functions

**Pydantic Best Practices**
- Use Pydantic models for request/response bodies
- Use `Field()` for validation constraints
- Prefer `model_validator` over `__init__` for complex validation

**Async Patterns**
- Blocking calls in async functions (use `asyncio.to_thread()`)
- Missing `await` on coroutines
- Sync database calls in async endpoints

**Code Quality**
- Functions > 40 lines
- Files > 500 lines
- Nesting > 4 levels
- Missing error handling (try/except)
- `print()` statements (use `logging`)
- Bare `except:` clauses

**Clean Code Naming**
- Variables: descriptive, snake_case (`user_count`, not `x`)
- Functions: verb phrases (`get_user_by_id`, not `user`)
- Classes: PascalCase nouns (`UserService`)

### MEDIUM (Consider Fixing)

**Documentation**
Documentation is NOT required for:
- Very short functions/classes with minimal logic
- Self-explanatory naming that clearly conveys purpose

When documentation IS needed, verify reST docstring style:
```python
def calculate_discount(price, percentage):
    """
    Calculate discounted price.

    :param price: original price
    :param percentage: discount percentage (0-100)
    :return: discounted price
    """
```

**FastAPI Patterns**
- Use dependency injection for shared logic
- Use `HTTPException` with appropriate status codes
- Use `status` module constants (`status.HTTP_201_CREATED`)

**Performance**
- N+1 query patterns
- Missing pagination for list endpoints
- Missing caching for expensive operations

**Best Practices**
- TODO/FIXME without tickets
- Magic numbers without explanation

---

## Project-Specific Rules

- Use `pydantic-settings` for configuration
- Use async/await consistently
- Use `httpx.AsyncClient` with `ASGITransport` for tests
- Prefer `type` aliases over raw Union types

---

## Output Format

```
## Backend Code Review Report

### Build Status
| Check | Status |
|-------|--------|
| Ruff | ✅/❌ |
| Mypy | ✅/❌ |
| Tests | ✅/❌ |
| Files Changed | X |

### Critical Issues (Must Fix)
- [ ] `file.py:123` - Description

### High Issues (Should Fix)
- [ ] `service.py:45` - Description

### Medium Issues (Consider Fixing)
- [ ] `utils.py:30` - Description

### What's Good
- [Positive observations]

### Summary
X critical | Y high | Z medium issues found
**Verdict:** ✅ APPROVE | ⚠️ WARNING | ❌ BLOCK
```
