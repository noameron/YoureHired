# company-research Specification

## Purpose
TBD - created by archiving change add-company-research-agent. Update Purpose after archive.
## Requirements
### Requirement: Company Research Agent
The system SHALL provide a multi-agent research flow that gathers and summarizes company information for job candidates.

#### Scenario: Research company for role
- **WHEN** GET /api/company-info/{session_id} is called with a valid session
- **THEN** the system executes the research flow (plan → search → summarize)
- **THEN** returns a structured CompanySummary with company details

#### Scenario: Session not found
- **WHEN** GET /api/company-info/{session_id} is called with invalid session_id
- **THEN** return 404 with "Session not found" error

### Requirement: Session Storage
The system SHALL store user selection sessions for retrieval by company-info endpoint.

#### Scenario: Store session after selection
- **WHEN** POST /api/user-selection completes successfully
- **THEN** the session is stored with session_id, company_name, role, role_description

#### Scenario: Retrieve session
- **WHEN** session_store.get(session_id) is called with valid id
- **THEN** return the Session object with validated company_name and role

### Requirement: Structured Agent Outputs
The system SHALL use Pydantic models for all agent structured outputs.

#### Scenario: Planner returns SearchPlan
- **WHEN** PlannerAgent completes
- **THEN** output is a SearchPlan with list of SearchQuery items

#### Scenario: Summarizer returns CompanySummary
- **WHEN** SummarizerAgent completes
- **THEN** output is a CompanySummary with name, description, tech_stack, etc.

### Requirement: Configurable Model
The system SHALL support configurable LLM model via environment variable.

#### Scenario: Change model via config
- **WHEN** OPENAI_MODEL is set in .env
- **THEN** agents use the specified model

