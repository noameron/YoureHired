# Project Context

## Purpose

YoureHired is a tailored coding practice platform for tech job candidates. Users select their target company and developer role, then receive LLM-generated coding, debugging, and design tasks specific to that role, with AI-powered performance feedback.

### Core User Flow
1. **Role Selection** → User picks company + developer role
2. **Company Research** → AI agents research the company (planning → searching → summarizing)
3. **Task Generation** → LLM creates tailored practice drills
4. **Feedback** → User completes tasks and receives AI-evaluated performance feedback

## Tech Stack

### Frontend
- Vue 3 with Composition API
- TypeScript (strict mode via vue-tsc)
- Vite (dev server, build tooling)
- Pinia (state management)
- Vue Router (navigation)
- Axios (HTTP client)

### Backend
- FastAPI (Python 3.11+)
- Pydantic v2 (request/response validation)
- pydantic-settings (configuration from .env)
- openai-agents (AI agent orchestration)
- uvicorn (ASGI server)

### Package Managers
- npm (frontend)
- uv (backend)

## Project Conventions

### Code Style

**Frontend:**
- ESLint with Vue and TypeScript plugins
- Prettier for formatting
- Never use `eslint-disable` comments - fix the underlying issue instead
- Use `@/` path alias for src imports

**Backend:**
- Ruff for linting and formatting (line length: 100)
- mypy with strict mode for type checking
- Target Python 3.11 features
- Import sorting: standard library → third-party → first-party (`app`)

### Architecture Patterns

**Frontend:**
- Views (`src/views/`) are page components connected to Vue Router
- Components (`src/components/`) are reusable UI elements
- Stores (`src/stores/`) use Pinia for state management
- Services (`src/services/`) handle API communication
- Composables (`src/composables/`) contain reusable composition logic
- Types (`src/types/`) define TypeScript interfaces

**Backend:**
- Routes (`app/api/`) are FastAPI routers mounted on `/api`
- Schemas (`app/schemas/`) define Pydantic models for request/response
- Services (`app/services/`) contain business logic
- Agents (`app/agents/`) implement AI agent pipelines
- Config (`app/config.py`) uses pydantic-settings loading from `.env`

**Communication:**
- Frontend proxies `/api/*` requests to backend (configured in `vite.config.ts`)
- Server-Sent Events (SSE) for streaming progress updates
- JSON payloads for all API requests/responses

### Testing Strategy

**Frontend (`npm run test`):**
- Vitest as test runner
- @vue/test-utils for component testing
- jsdom for DOM simulation
- Coverage via @vitest/coverage-v8

**Backend (`uv run pytest`):**
- pytest with pytest-asyncio (auto mode)
- httpx.AsyncClient with ASGITransport for API testing
- pytest-cov for coverage reporting
- Tests in `backend/tests/` directory

### Git Workflow

- Feature branches for development
- Pull requests to `main` branch
- GitHub Actions CI runs on all branches:
  - Lint (ruff check / eslint)
  - Type check (mypy)
  - Test (pytest / vitest)
  - Build (frontend only)
- Commit messages require file list format (enforced by hook)

## Domain Context

- **Roles**: Predefined developer roles (Frontend, Backend, Fullstack, etc.) fetched from backend
- **Sessions**: User selections create sessions that track research and drill progress
- **Company Research**: Multi-agent pipeline that plans searches, gathers findings, and summarizes
- **Drills**: Practice coding tasks tailored to company/role context
- **Evaluation**: AI agent evaluates user solutions and provides structured feedback

## Important Constraints

- Never commit API keys (use `.env` for local development)
- Python 3.11+ required (uses modern typing features)
- Node.js 18+ required
- CORS origins must include frontend URL (`http://localhost:3000` for dev)
- Default LLM model is `gpt-4o-mini` (configurable via `OPENAI_MODEL`)

## External Dependencies

### Required
- **OpenAI API**: Powers AI agents for research, task generation, and evaluation
  - Configured via `OPENAI_API_KEY` environment variable

### Optional
- **Anthropic API**: Alternative LLM provider
- **Google API**: Alternative LLM provider
- **Groq API**: Alternative LLM provider
