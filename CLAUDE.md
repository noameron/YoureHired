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

## Key Patterns

- Frontend proxies `/api/*` requests to backend (configured in `vite.config.ts`)
- Backend uses `pydantic-settings` for config; copy `.env.example` to `.env`
- All backend tests use `httpx.AsyncClient` with `ASGITransport`
