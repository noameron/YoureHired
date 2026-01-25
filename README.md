# YoureHired

**🚧 Work in Progress** - Practice real interview-style tasks tailored to your target company and role. Pick a company and role, then the app researches the company, summarizes what matters, and sets you up to practice with relevant context.

Currently, I am developing the AI agents that create tailored coding tasks and challenges based on your target role and company research. Later, I will build an evaluator agent to assess your solutions and provide detailed feedback on your performance.

## What It Does

- **Role selection:** Choose a target company and developer role (e.g., Frontend Developer).
- **Company research:** The backend orchestrates agents to plan searches, gather findings, and summarize results.
- **Live feedback:** The Practice view streams status updates and shows a structured company summary to guide your practice.

## Tech Stack

- **Frontend:** Vue 3, TypeScript, Vite, Pinia, Vue Router
- **Backend:** FastAPI (Python 3.11+), Pydantic, `openai-agents`
- **Dev tooling:** npm (frontend), uv (backend), Vitest/Pytest for tests

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- `uv` (Python package/dependency manager)
  - Install: see https://docs.astral.sh/uv/ (or use `pip install uv`)

## Setup

1. Create a `.env` file at the repository root (it is loaded by the backend). You can start from the example:

   ```bash
   cp .env.example .env
   ```

   Or create one manually:

   Example `.env` (do not commit real keys):
   
   ```env
   # API Keys (required for agents/tools)
   OPENAI_API_KEY=your_openai_api_key
   # Optional: other providers if you enable them
   ANTHROPIC_API_KEY=
   GOOGLE_API_KEY=
   GROQ_API_KEY=

   # Backend Settings
   DEBUG=false
   CORS_ORIGINS=["http://localhost:3000"]
   OPENAI_MODEL=gpt-4o-mini
   ```

2. Install dependencies:
   - Backend: `cd backend && uv sync`
   - Frontend: `cd frontend && npm install`

## Run Locally

Run both backend and frontend in separate terminals.

- Backend (FastAPI on port 8000):
  ```bash
  cd backend
  uv run uvicorn app.main:app --reload
  ```

- Frontend (Vite dev server on port 3000):
  ```bash
  cd frontend
  npm run dev
  ```

The Vite dev server proxies calls to `/api` → `http://localhost:8000` (see `frontend/vite.config.ts`).

## How To Use

1. Open `http://localhost:3000` in your browser.
2. On the Role Selection page:
   - Enter a company name (e.g., "Acme Corp").
   - Pick a role from the dropdown (roles are fetched from the backend).
   - Optionally add a role description to tailor the context.
   - Submit to create a session.
3. You’ll be redirected to the Practice view:
   - Watch live status updates as the research runs (planning → searching → summarizing).
   - When complete, a structured summary appears (overview, tech stack, culture, news, interview tips, sources).
4. Use the summary as context to practice answering questions or designing solutions relevant to the company and role.

## Main Endpoints (Backend)

- `GET /health` → Health check
- `GET /api/roles` → Returns predefined roles
- `POST /api/user-selection` → Creates a session for the selected company/role
- `GET /api/company-info/{session_id}` → Returns researched summary (non-streaming)
- `GET /api/company-research/{session_id}/stream` → Streams research progress via SSE

## Project Structure

```
frontend/           # Vue 3 + TypeScript + Vite
├── src/
│   ├── views/      # Pages: RoleSelection, Practice
│   ├── stores/     # Pinia store for user/session
│   └── services/   # API client (fetch roles, submit, stream)

backend/            # FastAPI + agents
├── app/
│   ├── main.py     # App init, CORS, /api router, /health
│   ├── api/        # Roles, user-selection, company-info routes
│   ├── schemas/    # Pydantic models (requests/responses/streaming)
│   ├── services/   # Session store and company research pipeline
│   └── agents/     # Planner/Search/Summarizer agents + guardrails
└── tests/          # Pytest suite
```

Key patterns:
- Frontend proxies `/api/*` to backend (configured in `vite.config.ts`).
- Backend loads settings from the repo root `.env` (see `app/config.py` and `app/main.py`).
- Streaming uses Server-Sent Events; the frontend parses `data: {json}\n\n` frames.

## Testing

- Frontend (from `frontend/`):
  ```bash
  npm run test        # watch mode
  npm run test:run    # single run
  npm run lint        # ESLint
  npm run format      # Prettier
  ```

- Backend (from `backend/`):
  ```bash
  uv run pytest                       # run tests
  uv run pytest --cov=app             # with coverage
  uv run ruff check .                 # lint
  uv run ruff format .                # format
  uv run mypy app                     # type check
  ```

## Troubleshooting

- 404 on practice route: Make sure you created a session (submit on the selection page) before navigating to `/practice`.
- CORS errors: Ensure backend CORS origins include `http://localhost:3000` (set via `.env` and `app/config.py`).
- Streaming issues: Check backend logs and browser console; verify the backend is reachable at `http://localhost:8000`.

## Notes

- Do not commit real API keys. Use a local `.env` for development.
- Default model is `gpt-4o-mini` (configurable via `.env`).
