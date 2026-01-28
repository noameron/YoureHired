# Change: Add Drill Generation Agents

## Why

The platform currently helps users select a role and research companies, but lacks the core practice functionality. Users need tailored coding/debugging/design drills based on their target company and role to prepare for interviews effectively.

## What Changes

- Add 3 specialized drill generator agents (coding, debugging, system design)
- Add evaluator agent to select the best drill from candidates
- Add orchestration service for parallel agent execution
- Add streaming API endpoint for real-time progress feedback
- Add Pydantic schemas for drill data models

## Impact

- Affected specs: None existing (new capability)
- New spec: `drill-generation`
- Affected code:
  - `backend/app/schemas/drill.py` (new)
  - `backend/app/agents/drill/` (new package with 4 agents)
  - `backend/app/services/drill_generation.py` (new)
  - `backend/app/api/drill.py` (new)
  - `backend/app/agents/__init__.py` (update exports)
  - `backend/app/api/__init__.py` (add router)
