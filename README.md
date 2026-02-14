# YoureHired

Practice real interview-style tasks tailored to your target company and role. Pick a company and role, then the app researches the company, summarizes what matters, and generates coding, debugging, and design drills specific to that position — with LLM-powered feedback on your solutions.

## What It Does

- **Role selection:** Choose a target company and developer role (e.g., Frontend Developer). Optionally paste the job description to give the agents more context.
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
   # --- Model Provider (pick one) ---
   # Option 1: OpenAI (default if set)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini

   # Option 2: Google Gemini (free tier fallback — used when OPENAI_API_KEY is empty)
   GOOGLE_API_KEY=
   GEMINI_MODEL=litellm/gemini/gemini-2.5-flash

   # Backend Settings
   DEBUG=false
   CORS_ORIGINS=["http://localhost:3000"]
   ```

   ### Model Providers

   The app picks a model based on which API key is available:

   | Provider | When used | Default model | Web search |
   |----------|-----------|---------------|------------|
   | **OpenAI** | `OPENAI_API_KEY` is set | `gpt-4o-mini` | Enabled — company research uses live web results |
   | **Google Gemini** | `OPENAI_API_KEY` is **not** set | `gemini-2.5-flash` | Disabled — research relies on the model's training data only |

   Override the default model with `OPENAI_MODEL` or `GEMINI_MODEL` in your `.env`.

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
   - Optionally paste a **role description** (e.g., from the job listing) — the agents use it as extra context when generating drills and research, so tasks match the actual position more closely.
   - Submit to create a session.
3. You'll be redirected to the Practice view:
   - Watch live status updates as agents research the company and generate a tailored drill.
   - You can **cancel** at any time during generation — you'll return to the home screen with your form fields preserved.
   - When complete, the drill appears with a description, requirements, starter code, and hints.
4. Write your solution in the editor and submit for LLM-powered feedback (score, strengths, areas for improvement).

## Main Endpoints (Backend)

- `GET /health` → Health check
- `GET /api/roles` → Returns predefined roles
- `POST /api/user-selection` → Creates a session for the selected company/role
- `GET /api/company-info/{session_id}` → Returns researched summary (non-streaming)
- `GET /api/company-research/{session_id}/stream` → Streams research progress via SSE
- `POST /api/generate-drill/{session_id}` → Generates a practice drill (non-streaming)
- `GET /api/generate-drill/{session_id}/stream` → Streams drill generation progress via SSE
- `POST /api/cancel/{session_id}` → Cancels all active agent runs for a session
- `POST /api/evaluate-solution/{session_id}` → Evaluates a user's submitted solution

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

docs/               # Documentation and generated artifacts
├── drills/
│   └── feedbacks/  # Timestamped LLM-generated drill feedback
│       └── DD-MM-YYYY_HH-MM/
│           └── {company}_{role}.md
└── *.md            # Agent specifications and internal docs
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
- Model selection is automatic: set `OPENAI_API_KEY` for OpenAI, or leave it empty to fall back to Google Gemini (see [Model Providers](#model-providers)).
