<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## TDD: Red → Green → Refactor (Always)

Every feature/fix follows this cycle — no exceptions:

1. **RED** — Delegate to `tdd-dev` agent. Include: feature description, file paths, expected behavior, edge cases. Agent writes failing tests.
2. **GREEN** — Main orchestrator writes minimal production code to pass tests.
3. **REFACTOR** — Delegate to `tdd-dev` again with implementation context. Agent refactors tests and verifies 80%+ coverage.

**Rule**: `tdd-dev` owns test files, main orchestrator owns production code. Never write production code without a failing test first.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YoureHired is a tailored coding practice platform for tech job candidates. Users select their target company and role, then receive LLM-generated coding, debugging, and design tasks specific to that role, with performance feedback.

### Core User Flow
1. **Role Selection** → User picks company + developer role
2. **Task Generation** → LLM creates tailored practice tasks
3. **Feedback** → User completes tasks and receives performance feedback

### Tech Stack

| Layer | Stack |
|-------|-------|
| Frontend | Vue 3 + TypeScript + Vite + Pinia |
| Backend | FastAPI + Python 3.11+ + Pydantic |
| Package Managers | npm (frontend), uv (backend) |

### Main Modules

| Module | Path | Description |
|--------|------|-------------|
| API Routes | `backend/app/api/` | FastAPI routers (endpoints) |
| Schemas | `backend/app/schemas/` | Pydantic request/response models |
| Config | `backend/app/config.py` | App settings, predefined roles |
| Views | `frontend/src/views/` | Vue page components (routed) |
| Stores | `frontend/src/stores/` | Pinia state management |
| Router | `frontend/src/router/` | Vue Router configuration |
| Types | `frontend/src/types/` | TypeScript type definitions |

## Commands

### Frontend (from `frontend/`)
```bash
npm install          # Install dependencies
npm run dev          # Start dev server on port 3000
npm run build        # Production build
npm run lint         # ESLint fix
npm run format       # Prettier format
npm run test         # Run tests in watch mode
npm run test:run     # Run tests once
```

### Backend (from `backend/`)
```bash
uv sync                                     # Install dependencies
uv run uvicorn app.main:app --reload        # Start dev server on port 8000
uv run pytest                               # Run all tests
uv run pytest tests/test_main.py::test_health  # Run single test
uv run pytest --cov=app                     # Run with coverage
uv run ruff check .                         # Lint
uv run ruff format .                        # Format
uv run mypy app                             # Type check
```

## Architecture

```
frontend/           # Vue 3 + TypeScript + Vite
├── src/
│   ├── views/      # Page components (routed)
│   ├── stores/     # Pinia state management
│   └── router/     # Vue Router config

backend/            # FastAPI + Python 3.11+
├── app/
│   ├── main.py     # FastAPI app, middleware, router mounting
│   ├── config.py   # Pydantic settings (loads from .env)
│   └── api/        # API routes
└── tests/          # pytest async tests
```

## Test Structure

Tests are kept in a single `tests/` directory (not scattered in `src/`):

```
frontend/tests/           # All frontend tests in one place
├── components/           # Component tests
├── composables/          # Composable tests
├── services/             # API/service tests
├── stores/               # Pinia store tests
└── views/                # View component tests

backend/tests/            # All backend tests
└── ...
```

## Key Patterns

- Frontend proxies `/api/*` requests to backend (configured in `vite.config.ts`)
- Backend uses `pydantic-settings` for config; copy `.env.example` to `.env`
- All backend tests use `httpx.AsyncClient` with `ASGITransport`

### Plan Output Format
Before presenting any plan, verify:
- [ ] No branch modifies more than 5 files
- [ ] Files are grouped by logical cohesion
- [ ] If >2 branches: base branch strategy is used
- [ ] Merge order is clearly documented

## Code Style Guidelines

- **Avoid ESLint disable comments**: Never use `eslint-disable`, `eslint-enable`, or inline `eslint-disable-next-line` comments to suppress lint or compile errors. Instead, fix the underlying issue. If a disable comment is absolutely necessary (e.g., external library limitations, intentional edge cases), always prompt the user first explaining why it's needed and get approval before adding it.

- **No imports inside functions or classes**: Always place imports at the top of the file. Never use imports inside function or class bodies.

- **Avoid nested function definitions**: Helper functions should be defined at module level, not inside other functions. Keep functions standalone for better readability and testability.

- **Use decorators for cleaner code**: Prefer decorators over repetitive boilerplate when they improve readability (e.g., for logging, caching, validation, retry logic).

## Git Commands

- **Always run git commands from project root**: Use absolute paths or explicitly `cd` to project root before git operations. Working directory may be `frontend/` or `backend/` from earlier commands.
  ```bash
  # Good - explicit project root
  cd /path/to/YoureHired && git add .claude/...

  # Bad - assumes current directory is project root
  git add .claude/...
  ```
