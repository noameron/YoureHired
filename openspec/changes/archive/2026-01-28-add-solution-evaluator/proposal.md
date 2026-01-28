# Change: Add Solution Evaluator Agent

## Why
Users complete drill exercises but currently have no way to receive feedback on their solutions. Adding an evaluator agent will provide structured feedback highlighting strengths and areas for improvement, enabling a learning loop where the next drill can target weak areas.

## What Changes
- Add new `solution-evaluation` capability with evaluator agent
- Add backend API endpoint to submit solutions and receive evaluation
- Add frontend UI to display structured feedback after submission
- Save feedback as markdown files at `docs/drills/feedbacks/<dd-mm-yyyy_hh-mm>/<company_name_role>.md`
- Generate a concise LLM-friendly summary of feedback to pass to drill generation agent
- Integrate evaluation summary into drill generation to personalize future drills
- Add new Pydantic schemas for evaluation requests/responses

## Impact
- Affected specs: `drill-generation` (MODIFIED - receives feedback summary context)
- New spec: `solution-evaluation`
- Affected code:
  - `backend/app/agents/` - new solution evaluator agent
  - `backend/app/schemas/` - new evaluation schemas
  - `backend/app/api/` - new evaluation endpoint
  - `frontend/src/views/PracticeView.vue` - display feedback UI
  - `frontend/src/views/practice/usePractice.ts` - wire up submission
  - `frontend/src/services/` - API client for evaluation
  - `docs/drills/feedbacks/` - persisted feedback files
