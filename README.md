# YoureHired

Full-stack hiring/recruitment application.

## Tech Stack

- **Frontend:** Vue.js 3, TypeScript, Vite, Pinia, Vue Router
- **Backend:** Python 3.11+, FastAPI, Pydantic

## Quick Start

### Backend
```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000, backend on http://localhost:8000.
