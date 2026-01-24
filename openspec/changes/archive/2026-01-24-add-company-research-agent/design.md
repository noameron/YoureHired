# Design: Company Research Agent

## Context

This is the first AI agent in YoureHired. It researches companies using a multi-agent flow with structured outputs, following the OpenAI Agents SDK pattern from `lab4.ipynb`.

### Constraints
- Must use OpenAI Agents SDK with structured outputs
- Must use WebSearchTool for web search
- gpt-4o-mini as default model (configurable)
- Company name must come from validated session (not direct user input to agent)

## Goals / Non-Goals

### Goals
- Create a company research flow using OpenAI Agents SDK
- Use structured outputs (Pydantic models) for agent responses
- Multi-agent pattern: Planner → Search → Summarizer
- Return structured company data for task generation

### Non-Goals
- Database persistence (in-memory for MVP)
- Frontend display (separate feature)

## Technical Decisions

### 1. Data Flow (Validated Input)

```
User Input → POST /api/user-selection → Validation → Session Store
                                                          ↓
                                              (company_name, role stored)
                                                          ↓
              GET /api/company-info/{session_id} ← Session Lookup
                                                          ↓
                                              research_company(
                                                  company_name=session.company_name,  # validated
                                                  role=session.role                   # validated
                                              )
```

The agent never receives raw user input - only validated data from the session.

### 2. Agent Architecture

Using OpenAI Agents SDK with the exact patterns from lab4.ipynb:

```python
from agents import Agent, WebSearchTool, trace, Runner
from agents.model_settings import ModelSettings
from pydantic import BaseModel, Field
```

**Flow**:
```
1. PlannerAgent → Plans 3 search queries (output_type=SearchPlan)
2. SearchAgent → Executes searches with WebSearchTool
3. SummarizerAgent → Creates CompanySummary (output_type=CompanySummary)
```

### 3. Structured Outputs

**Search Plan** (Planner output):
```python
class SearchQuery(BaseModel):
    reason: str = Field(description="Why this search helps understand the company")
    query: str = Field(description="The search query to execute")

class SearchPlan(BaseModel):
    searches: list[SearchQuery] = Field(description="List of searches to perform")
```

**Company Summary** (Summarizer output):
```python
class TechStack(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)

class CompanySummary(BaseModel):
    name: str
    industry: str | None = None
    description: str = Field(description="2-3 sentence company overview")
    size: str | None = Field(description="e.g., '1000-5000 employees'")
    tech_stack: TechStack | None = None
    engineering_culture: str | None = None
    recent_news: list[str] = Field(default_factory=list)
    interview_tips: str | None = Field(description="Role-specific preparation tips")
    sources: list[str] = Field(default_factory=list)
```

### 4. Agent Definitions

**Planner Agent**:
```python
PLANNER_INSTRUCTIONS = """You are a research planner. Given a company name and role,
plan 3 web searches to gather information about the company.

Focus on:
1. Company overview and industry
2. Tech stack and engineering culture
3. Recent news and interview experiences for the role
"""

planner_agent = Agent(
    name="CompanyPlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SearchPlan,
)
```

**Search Agent**:
```python
SEARCH_INSTRUCTIONS = """You are a research assistant. Given a search query,
search the web and produce a concise 2-3 paragraph summary of the results.
Capture the main points relevant to understanding the company."""

search_agent = Agent(
    name="CompanySearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
```

**Summarizer Agent**:
```python
SUMMARIZER_INSTRUCTIONS = """You are a company research summarizer.
Given search results about a company, create a structured summary
to help a job candidate prepare for a {role} position.

Be concise but informative. Include tech stack if found.
Provide interview tips specific to the role."""

summarizer_agent = Agent(
    name="CompanySummarizerAgent",
    instructions=SUMMARIZER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=CompanySummary,
)
```

### 5. API Endpoint (Receives Validated Data)

```python
# api/company_info.py
@router.get("/company-info/{session_id}")
async def get_company_info(session_id: str) -> CompanyInfoResponse:
    # 1. Get validated session
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # 2. Pass validated data to agent (not raw user input)
    summary = await research_company(
        company_name=session.company_name,  # Already validated by user_selection
        role=session.role,                   # Already validated by user_selection
    )

    return CompanyInfoResponse(...)
```

### 6. Research Flow

```python
async def research_company(company_name: str, role: str) -> CompanySummary:
    """
    Execute the company research flow.

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
        input = f"Search term: {item.query}\nReason: {item.reason}"
        result = await Runner.run(search_agent, input)
        return result.final_output

    tasks = [asyncio.create_task(run_search(s)) for s in search_plan.searches]
    search_results = await asyncio.gather(*tasks)

    # Step 3: Summarize results
    combined = "\n\n".join(search_results)
    summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
    summary_result = await Runner.run(summarizer_agent, summary_input)

    return summary_result.final_output
```

### 7. Configuration

```python
# config.py additions
class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
```

### 8. Model Switching

To switch models, change `OPENAI_MODEL` in `.env`:
```
OPENAI_MODEL=gpt-4o  # More capable, higher cost
```

## File Structure

```
backend/app/
├── agents/                    # NEW
│   ├── __init__.py
│   └── company_research.py   # Agents and flow
├── api/
│   ├── company_info.py       # NEW endpoint
│   └── user_selection.py     # UPDATE: store session
├── schemas/
│   └── company_info.py       # NEW models
├── services/
│   └── session_store.py      # NEW
└── config.py                 # UPDATE
```

## Dependencies

```toml
dependencies = [
    "openai-agents>=0.1.0",
]
```
