# Design: GitHub Actions CI Workflow

## Context
The project uses a monorepo structure with:
- **Backend**: Python 3.11+ with FastAPI, managed by `uv`
- **Frontend**: Vue 3 + TypeScript, managed by `npm`

Both have existing tooling for linting, type checking, testing, and building that needs to run in CI.

## Goals
- Automate quality checks on every push and pull request
- Fast feedback with parallelized jobs
- Clear, readable workflow with descriptive step names
- Efficient caching to minimize CI time

## Non-Goals
- Deployment automation (separate workflow)
- E2E tests with Playwright (can be added later)
- Container builds

## Decisions

### Workflow Structure: Parallel Jobs
**Decision**: Use separate jobs for backend and frontend that run in parallel
**Rationale**: Faster feedback; failures are isolated and clear

### Trigger Events
**Decision**: Run on `push` to main and all `pull_request` events
**Rationale**: Validates main branch and all PRs before merge

### Caching Strategy
**Decision**: Use GitHub Actions cache for npm and uv dependencies
**Rationale**: Significant time savings on subsequent runs

### Python Version
**Decision**: Use Python 3.11 (single version)
**Rationale**: Matches project requirement (`>=3.11`); add matrix later if needed

### Node Version
**Decision**: Use Node 20 LTS
**Rationale**: Current LTS version with broad ecosystem support

### Job Dependencies
**Decision**: No strict dependencies between backend/frontend jobs
**Rationale**: They are independent; parallel execution is faster

## Workflow Structure

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    # Lint → Type Check → Test (sequential in job)

  frontend:
    # Lint → Type Check → Test → Build (sequential in job)
```

## Step Details

### Backend Job
1. **Checkout code** - Get repository
2. **Install uv** - Fast Python package manager
3. **Set up Python** - Python 3.11
4. **Install dependencies** - `uv sync`
5. **Lint** - `ruff check .`
6. **Type check** - `mypy app`
7. **Test** - `pytest --cov=app`

### Frontend Job
1. **Checkout code** - Get repository
2. **Set up Node.js** - Node 20 with npm cache
3. **Install dependencies** - `npm ci`
4. **Lint** - `npm run lint`
5. **Type check** - `vue-tsc --noEmit`
6. **Test** - `npm run test:run`
7. **Build** - `npm run build`

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| CI takes too long | Use caching; parallelize jobs |
| Flaky tests | Tests should be deterministic; add retry if needed |
| Environment differences | Pin versions; use exact lock files |

## Open Questions
- Should E2E tests be added? (Recommend: separate workflow later)
- Should we add coverage reporting? (Recommend: yes, via pytest-cov and vitest coverage)
