# Change: Add Company Research Agent

## Why

After users select their target company and role, the application needs to research the company to provide tailored practice tasks. This is the first AI agent in the system, establishing patterns for future agent development.

## What Changes

- **NEW** Company research agent using OpenAI Agents SDK with multi-agent flow
- **NEW** WebSearchTool integration for web search (OpenAI hosted tool)
- **NEW** `/api/company-info/{session_id}` endpoint
- **NEW** Session storage to link user selection with company research
- **NEW** Structured outputs using Pydantic models
- **UPDATE** User selection endpoint to store sessions
- **UPDATE** Config to include OpenAI API key and model settings

## Impact

- Affected specs: `company-research` (new capability)
- Affected code:
  - `backend/app/config.py` - Add OpenAI settings
  - `backend/app/api/user_selection.py` - Store session after creation
  - `backend/app/api/company_info.py` - NEW endpoint
  - `backend/app/agents/` - NEW directory for agent definitions
  - `backend/app/services/session_store.py` - NEW session storage
  - `backend/app/schemas/company_info.py` - NEW response models
