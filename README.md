# YoureHired

Practice real interview-style tasks tailored to your target company and role — and discover open-source repos to contribute to. YoureHired combines LLM-powered coding drills with AI-driven GitHub repository discovery, all with real-time streaming feedback.

---

## Table of Contents

- [Features at a Glance](#features-at-a-glance) — what the app does
- [Tech Stack](#tech-stack) — languages, frameworks, tooling
- [Prerequisites](#prerequisites) — what you need installed
- [Setup](#setup) — environment configuration and dependencies
  - [Model Providers](#model-providers) — OpenAI vs Gemini
  - [GitHub Scout Setup](#github-scout-setup) — token for repo discovery
- [Run Locally](#run-locally) — start the dev servers
- [How To Use](#how-to-use) — walkthrough of each feature
  - [Interview Practice](#interview-practice) — drills and feedback
  - [GitHub Scout](#github-scout) — repo discovery and analysis
- [API Endpoints](#api-endpoints) — backend route reference
- [Project Structure](#project-structure) — directory layout
- [Testing](#testing) — running tests and linters
- [Troubleshooting](#troubleshooting) — common issues
- [Notes](#notes) — security and config reminders

---

## Features at a Glance

### Interview Practice
- **Role selection:** Choose a target company and developer role. Optionally paste the job description for extra context.
- **Company research:** Agents plan searches, gather findings, and summarize what matters about the company.
- **Tailored drills:** LLM generates coding, debugging, and design tasks specific to the role.
- **Live feedback:** Stream status updates in real time, then submit solutions for scored feedback.

### GitHub Scout
- **Developer profile:** Define your languages, topics, skill level, and contribution goals.
- **Smart search:** Query GitHub via GraphQL with filters (stars, topics, activity, license) and rule-based heuristics that remove tutorials, awesome-lists, and inactive repos.
- **AI analysis:** An LLM agent scores each repo on a 0–10 fit scale with personalized contribution suggestions.
- **Real-time streaming:** SSE streams progress through discovery, filtering, and analysis phases — with cancel support.
- **Result cards:** Color-coded scores, metadata badges, and direct links to repos.

## Tech Stack

- **Frontend:** Vue 3, TypeScript, Vite, Pinia, Vue Router
- **Backend:** FastAPI (Python 3.11+), Pydantic, `openai-agents`
- **Data:** SQLite (Scout profiles, search runs, analysis results)
- **External APIs:** GitHub GraphQL API (repo discovery)
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

   # GitHub Scout (optional — enables repo discovery)
   GITHUB_TOKEN=your_github_personal_access_token
   ```

   ### Model Providers

   The app picks a model based on which API key is available:

   | Provider | When used | Default model | Web search |
   |----------|-----------|---------------|------------|
   | **OpenAI** | `OPENAI_API_KEY` is set | `gpt-4o-mini` | Enabled — company research uses live web results |
   | **Google Gemini** | `OPENAI_API_KEY` is **not** set | `gemini-2.5-flash` | Disabled — research relies on the model's training data only |

   Override the default model with `OPENAI_MODEL` or `GEMINI_MODEL` in your `.env`.

   ### GitHub Scout Setup

   Scout requires a GitHub personal access token with `public_repo` scope:

   1. Go to **GitHub Settings > Developer settings > Personal access tokens**.
   2. Generate a token with `public_repo` scope (classic) or `Repository access: Public` (fine-grained).
   3. Add it to your `.env` as `GITHUB_TOKEN`.

   Without a token Scout will return authentication errors. The token is never exposed in API responses or SSE events.

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

### Interview Practice

1. Open `http://localhost:3000` in your browser.
2. On the **Role Selection** page:
   - Enter a company name (e.g., "Acme Corp").
   - Pick a role from the dropdown (roles are fetched from the backend).
   - Optionally paste a **role description** (e.g., from the job listing) — the agents use it as extra context when generating drills and research, so tasks match the actual position more closely.
   - Submit to create a session.
3. You'll be redirected to the **Practice** view:
   - Watch live status updates as agents research the company and generate a tailored drill.
   - You can **cancel** at any time during generation — you'll return to the home screen with your form fields preserved.
   - When complete, the drill appears with a description, requirements, starter code, and hints.
4. Write your solution in the editor and submit for LLM-powered feedback (score, strengths, areas for improvement).

### GitHub Scout

1. Navigate to `/scout` (or click **Scout** in the nav bar).
2. **Set up your profile:**
   - Enter your programming languages, topics of interest, skill level, and contribution goals.
   - Save the profile (it persists across sessions in SQLite).
3. **Configure search filters** (all optional):
   - Languages, star range, topics, recent activity date, license.
4. **Run a search:**
   - Watch real-time progress as the pipeline discovers repos → filters out noise → analyzes matches with AI.
   - Cancel mid-search if needed.
5. **Browse results:**
   - Each repo card shows a color-coded fit score (green 8–10, yellow 5–7, red 1–4), a fit reason, contribution suggestions, and metadata (stars, language, issues, license).
   - Click through to the repo on GitHub.

Rate limit: 5 searches per hour per IP.

## API Endpoints

### Core (Interview Practice)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/roles` | List predefined roles |
| `POST` | `/api/user-selection` | Create a session for company/role |
| `GET` | `/api/company-info/{session_id}` | Researched company summary |
| `GET` | `/api/company-research/{session_id}/stream` | Stream research progress (SSE) |
| `POST` | `/api/generate-drill/{session_id}` | Generate a practice drill |
| `GET` | `/api/generate-drill/{session_id}/stream` | Stream drill generation (SSE) |
| `POST` | `/api/cancel/{session_id}` | Cancel active agent runs |
| `POST` | `/api/evaluate-solution/{session_id}` | Evaluate submitted solution |

### GitHub Scout

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/scout/profile` | Save/update developer profile |
| `GET` | `/api/scout/profile` | Retrieve developer profile |
| `POST` | `/api/scout/search` | Start a search run (returns `run_id`) |
| `GET` | `/api/scout/search/{run_id}/stream` | Stream search progress (SSE) |
| `GET` | `/api/scout/search/{run_id}/results` | Fetch results for a completed search |
| `POST` | `/api/scout/search/{run_id}/cancel` | Cancel an in-progress search |

## Project Structure

```
frontend/                # Vue 3 + TypeScript + Vite
├── src/
│   ├── views/           # Pages: RoleSelection, Practice, Scout
│   ├── components/      # Reusable components (ScoutResultCard, ...)
│   ├── stores/          # Pinia stores (userSelection, scout)
│   ├── services/        # API clients (api.ts, scout.ts)
│   ├── types/           # TypeScript type definitions (scout.ts)
│   └── router/          # Vue Router configuration
├── tests/               # Vitest suite

backend/                 # FastAPI + agents
├── app/
│   ├── main.py          # App init, CORS, /api router, /health
│   ├── config.py        # Settings loaded from .env
│   ├── api/             # Route modules (roles, drill, scout, ...)
│   ├── schemas/         # Pydantic models (requests/responses/streaming)
│   ├── services/        # Business logic
│   │   ├── scout_orchestrator.py   # Search pipeline (discover → filter → analyze)
│   │   ├── scout_analysis.py       # Batched LLM repo scoring
│   │   ├── github_client.py        # GitHub GraphQL client
│   │   ├── github_repos_db.py      # SQLite persistence layer
│   │   ├── repo_filtering.py       # Rule-based repo filtering
│   │   └── ...                     # Session store, research, drill generation
│   └── agents/          # LLM agent definitions
│       ├── repo_analyst_agent.py   # Repo fit scoring agent
│       └── drill/                  # Planner/Search/Summarizer agents
├── tests/               # Pytest suite
└── data/                # SQLite database (auto-created at runtime)

docs/                    # Documentation and generated artifacts
├── drills/
│   └── feedbacks/       # Timestamped LLM-generated drill feedback
└── *.md                 # Agent specifications and internal docs
```

Key patterns:
- Frontend proxies `/api/*` to backend (configured in `vite.config.ts`).
- Backend loads settings from the repo root `.env` (see `app/config.py` and `app/main.py`).
- Streaming uses Server-Sent Events; the frontend parses `data: {json}\n\n` frames.
- Scout data persists in SQLite (`data/scout.db` by default); stale repos are pruned after 30 days.

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

- **404 on practice route:** Make sure you created a session (submit on the selection page) before navigating to `/practice`.
- **CORS errors:** Ensure backend CORS origins include `http://localhost:3000` (set via `.env` and `app/config.py`).
- **Streaming issues:** Check backend logs and browser console; verify the backend is reachable at `http://localhost:8000`.
- **Scout authentication errors:** Verify `GITHUB_TOKEN` is set in `.env` and has `public_repo` scope.
- **Scout rate limit (429):** Searches are limited to 5 per hour per IP. Wait and retry.

## Notes

- Do not commit real API keys. Use a local `.env` for development.
- Model selection is automatic: set `OPENAI_API_KEY` for OpenAI, or leave it empty to fall back to Google Gemini (see [Model Providers](#model-providers)).
- `GITHUB_TOKEN` is never exposed in API responses or SSE events.
