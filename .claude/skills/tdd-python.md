---
name: tdd-python
description: TDD skill for Python/pytest. GIVEN/WHEN/THEN structure, pytest fixtures, async testing with httpx, mocking. Use for feature dev, bug fixes, refactoring.
user-invocable: false
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# TDD Skill for Python/pytest

## When to Activate
- Feature development, bug fixes, refactoring, API development

## Core Principles
1. **Write Tests First** - No production code without a failing test
2. **80% Coverage Minimum**
3. **One Assertion Per Concept**
4. **No For Loops in Tests** - Use `@pytest.mark.parametrize` instead
5. **Test Real-World Scenarios** - No unrealistic edge cases

## TDD Workflow
```
RED → Write failing test
GREEN → Write minimal code to pass
REFACTOR → Improve code, keep tests green
```

## GIVEN/WHEN/THEN Structure (Required)

```python
def test_example():
    # GIVEN - setup
    # WHEN - action
    # THEN - assertions
```

## Test Examples

### Unit Test
```python
def test_calculate_discount():
    # GIVEN
    price, discount = 100.0, 20
    # WHEN
    result = calculate_discount(price, discount)
    # THEN
    assert result == 80.0
```

### API Test (FastAPI + httpx)
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    # GIVEN
    user_data = {"email": "test@example.com", "name": "Test"}
    # WHEN
    response = await client.post("/api/users", json=user_data)
    # THEN
    assert response.status_code == 201
```

### Parametrized Test (Instead of For Loops)
```python
@pytest.mark.parametrize("email", ["valid@example.com", "test@domain.org"])
def test_valid_email(email: str):
    # GIVEN
    validator = EmailValidator()
    # WHEN
    result = validator.is_valid(email)
    # THEN
    assert result is True
```

### Exception Testing
```python
def test_division_by_zero():
    # GIVEN
    calc = Calculator()
    # WHEN / THEN
    with pytest.raises(ZeroDivisionError):
        calc.divide(10, 0)
```

## Fixtures
```python
@pytest.fixture
def sample_user():
    return User(id=1, email="test@example.com")

@pytest.fixture
async def db_session():
    session = await create_test_session()
    yield session
    await session.rollback()
```

## Mocking

### unittest.mock
```python
from unittest.mock import Mock, AsyncMock, patch

def test_service_calls_repo():
    # GIVEN
    mock_repo = Mock()
    mock_repo.get.return_value = User(id=1)
    service = UserService(repo=mock_repo)
    # WHEN
    user = service.get_user(1)
    # THEN
    mock_repo.get.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_async_service():
    # GIVEN
    mock_repo = AsyncMock()
    mock_repo.get.return_value = User(id=1)
    # WHEN
    user = await service.get_user(1)
    # THEN
    mock_repo.get.assert_awaited_once_with(1)
```

### patch decorator
```python
@patch("app.services.send_email")
def test_sends_email(mock_send: Mock):
    # GIVEN
    service = UserService()
    # WHEN
    service.create_user({"email": "new@example.com"})
    # THEN
    mock_send.assert_called_once()
```

## Coverage

pyproject.toml:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["app"]
branch = true

[tool.coverage.report]
fail_under = 80
```

Commands:
```bash
uv run pytest --cov=app                    # Run with coverage
uv run pytest --cov=app --cov-fail-under=80  # Fail if < 80%
```

## Best Practices

### Do
- Write test first, then code
- Descriptive names: `test_user_creation_with_valid_email_succeeds`
- Keep tests independent
- Use fixtures for common setup
- Test realistic edge cases

### Avoid
| Anti-Pattern | Solution |
|--------------|----------|
| For loops in tests | `@pytest.mark.parametrize` |
| Unrealistic edge cases | Test real user scenarios |
| Testing implementation details | Test public interface |
| Over-mocking | Mock only external deps |
| Shared mutable state | Use fixtures with cleanup |

**Bad - For loop:**
```python
def test_emails():
    for email in emails:
        assert is_valid(email)  # Which failed?
```

**Good - Parametrized:**
```python
@pytest.mark.parametrize("email", ["a@b.com", "x@y.org"])
def test_valid_email(email):
    assert is_valid(email)
```

**Bad - Unrealistic:**
```python
def test_10000_emojis_in_username(): ...  # Never happens
```

**Good - Realistic:**
```python
def test_username_with_spaces_rejected(): ...  # Users try this
```

## Quick Reference
```bash
uv run pytest                              # Run all
uv run pytest tests/test_user.py           # Run file
uv run pytest -k "user"                    # Match pattern
uv run pytest --lf                         # Failed only
uv run pytest -v                           # Verbose
uv run pytest --cov=app                    # Coverage
```
