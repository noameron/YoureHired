# Tasks: Add Company Research Agent

Each group is **stateless** - contains all context needed to implement without external dependencies.

---

## Group 1: Configuration & Dependencies

**Files to modify:**
- `backend/app/config.py`
- `backend/.env.example`
- `backend/pyproject.toml`

**Tasks:**
- [ ] 1.1 Add settings to `backend/app/config.py`:
```python
# Add these fields to the Settings class:
openai_api_key: str = ""
openai_model: str = "gpt-4o-mini"
```

- [ ] 1.2 Add to `backend/.env.example`:
```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

- [ ] 1.3 Add dependency to `backend/pyproject.toml` in dependencies list:
```
"openai-agents>=0.1.0",
```

- [ ] 1.4 Run `cd backend && uv sync`

---

## Group 2: Session Storage Service

**Files to create:**
- `backend/app/services/__init__.py`
- `backend/app/services/session_store.py`

**Context:** This service stores user sessions after role selection, so company-info endpoint can retrieve validated data.

**Tasks:**
- [ ] 2.1 Create `backend/app/services/__init__.py`:
```python
from app.services.session_store import session_store, Session, SessionStore

__all__ = ["session_store", "Session", "SessionStore"]
```

- [ ] 2.2 Create `backend/app/services/session_store.py`:
```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Session:
    session_id: str
    company_name: str
    role: str
    role_description: str | None
    created_at: datetime = field(default_factory=datetime.utcnow)


class SessionStore:
    def __init__(self, ttl_hours: int = 24):
        self._sessions: dict[str, Session] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def create(
        self,
        session_id: str,
        company_name: str,
        role: str,
        role_description: str | None = None,
    ) -> Session:
        session = Session(
            session_id=session_id,
            company_name=company_name,
            role=role,
            role_description=role_description,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session and datetime.utcnow() - session.created_at < self._ttl:
            return session
        return None


session_store = SessionStore()
```

- [ ] 2.3 Create `backend/tests/test_session_store.py`:
```python
import pytest
from app.services.session_store import SessionStore, Session


class TestSessionStore:
    def test_create_session(self):
        store = SessionStore()
        session = store.create("id-1", "Google", "backend_developer")
        assert session.session_id == "id-1"
        assert session.company_name == "Google"

    def test_get_existing_session(self):
        store = SessionStore()
        store.create("id-1", "Google", "backend_developer")
        session = store.get("id-1")
        assert session is not None
        assert session.company_name == "Google"

    def test_get_nonexistent_session(self):
        store = SessionStore()
        assert store.get("nonexistent") is None
```

---

## Group 3: Company Info Schemas

**Files to create:**
- `backend/app/schemas/company_info.py`

**Context:** Pydantic models for structured outputs from agents and API responses.

**Tasks:**
- [ ] 3.1 Create `backend/app/schemas/company_info.py`:
```python
from pydantic import BaseModel, Field


# Agent structured outputs
class SearchQuery(BaseModel):
    reason: str = Field(description="Why this search helps understand the company")
    query: str = Field(description="The search query to execute")


class SearchPlan(BaseModel):
    searches: list[SearchQuery] = Field(description="List of searches to perform")


class TechStack(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class CompanySummary(BaseModel):
    name: str
    industry: str | None = None
    description: str = Field(description="2-3 sentence company overview")
    size: str | None = Field(default=None, description="e.g., '1000-5000 employees'")
    tech_stack: TechStack | None = None
    engineering_culture: str | None = None
    recent_news: list[str] = Field(default_factory=list)
    interview_tips: str | None = Field(default=None, description="Role-specific tips")
    sources: list[str] = Field(default_factory=list)


# API response models
class CompanyInfoData(BaseModel):
    session_id: str
    company_name: str
    role: str
    summary: CompanySummary


class CompanyInfoResponse(BaseModel):
    success: bool = True
    data: CompanyInfoData


class CompanyInfoErrorDetail(BaseModel):
    code: str
    message: str


class CompanyInfoError(BaseModel):
    success: bool = False
    error: CompanyInfoErrorDetail
```

---

## Group 4: Agent Module

**Files to create:**
- `backend/app/agents/__init__.py`
- `backend/app/agents/company_research.py`

**Context:** Multi-agent flow using OpenAI Agents SDK. Pattern from lab4.ipynb:
```python
from agents import Agent, WebSearchTool, Runner
from agents.model_settings import ModelSettings
# Agent with structured output:
agent = Agent(name="...", instructions="...", model="gpt-4o-mini", output_type=PydanticModel)
# Agent with tool:
agent = Agent(name="...", tools=[WebSearchTool()], model_settings=ModelSettings(tool_choice="required"))
# Run agent:
result = await Runner.run(agent, "input")
output = result.final_output
```

**Tasks:**
- [ ] 4.1 Create `backend/app/agents/__init__.py`:
```python
from app.agents.company_research import research_company

__all__ = ["research_company"]
```

- [ ] 4.2 Create `backend/app/agents/company_research.py`:
```python
import asyncio
from agents import Agent, WebSearchTool, Runner
from agents.model_settings import ModelSettings
from app.schemas.company_info import SearchPlan, SearchQuery, CompanySummary


PLANNER_INSTRUCTIONS = """You are a research planner. Given a company name and role,
plan 3 web searches to gather information about the company.

Focus on:
1. Company overview and industry
2. Tech stack and engineering culture
3. Recent news and interview experiences for the role
"""

SEARCH_INSTRUCTIONS = """You are a research assistant. Given a search query,
search the web and produce a concise 2-3 paragraph summary of the results.
Capture the main points relevant to understanding the company."""

SUMMARIZER_INSTRUCTIONS = """You are a company research summarizer.
Given search results about a company, create a structured summary
to help a job candidate prepare for a {role} position.

Be concise but informative. Include tech stack if found.
Provide interview tips specific to the role."""


planner_agent = Agent(
    name="CompanyPlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SearchPlan,
)

search_agent = Agent(
    name="CompanySearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

summarizer_agent = Agent(
    name="CompanySummarizerAgent",
    instructions=SUMMARIZER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=CompanySummary,
)


async def research_company(company_name: str, role: str) -> CompanySummary:
    """
    Execute company research flow.

    Args:
        company_name: Validated company name from session
        role: Validated role from session
    """
    # Step 1: Plan searches
    plan_input = f"Company: {company_name}\nRole: {role}"
    plan_result = await Runner.run(planner_agent, plan_input)
    search_plan: SearchPlan = plan_result.final_output

    # Step 2: Execute searches in parallel
    async def run_search(item: SearchQuery) -> str:
        search_input = f"Search term: {item.query}\nReason: {item.reason}"
        result = await Runner.run(search_agent, search_input)
        return result.final_output

    tasks = [asyncio.create_task(run_search(s)) for s in search_plan.searches]
    search_results = await asyncio.gather(*tasks)

    # Step 3: Summarize results
    combined = "\n\n".join(search_results)
    summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
    summary_result = await Runner.run(summarizer_agent, summary_input)

    return summary_result.final_output
```

---

## Group 5: API Integration

**Files to modify:**
- `backend/app/api/user_selection.py` - Add session storage
- `backend/app/api/__init__.py` - Register router
- `backend/app/main.py` - Mount router

**Files to create:**
- `backend/app/api/company_info.py`

**Context:**
- Session store interface: `session_store.create(session_id, company_name, role, role_description)` and `session_store.get(session_id) -> Session | None`
- Agent interface: `await research_company(company_name, role) -> CompanySummary`

**Tasks:**
- [ ] 5.1 Update `backend/app/api/user_selection.py` - add after `session_id=str(uuid.uuid4())`:
```python
# Add import at top:
from app.services import session_store

# Add after creating session_id, before return:
session_store.create(
    session_id=session_id,
    company_name=request.company_name,
    role=role_label,
    role_description=request.role_description,
)
```

- [ ] 5.2 Create `backend/app/api/company_info.py`:
```python
from fastapi import APIRouter, HTTPException

from app.agents import research_company
from app.schemas.company_info import (
    CompanyInfoData,
    CompanyInfoResponse,
)
from app.services import session_store

router = APIRouter(tags=["company-info"])


@router.get(
    "/company-info/{session_id}",
    response_model=CompanyInfoResponse,
)
async def get_company_info(session_id: str) -> CompanyInfoResponse:
    """Research and return company information for a session."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = await research_company(
        company_name=session.company_name,
        role=session.role,
    )

    return CompanyInfoResponse(
        data=CompanyInfoData(
            session_id=session_id,
            company_name=session.company_name,
            role=session.role,
            summary=summary,
        )
    )
```

- [ ] 5.3 Update `backend/app/api/__init__.py` - add import and include router:
```python
from app.api import company_info
# In the list or wherever routers are registered
```

- [ ] 5.4 Update `backend/app/main.py` - mount the router:
```python
from app.api import company_info
app.include_router(company_info.router, prefix="/api")
```
