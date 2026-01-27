## ADDED Requirements

### Requirement: Drill Data Model

The system SHALL define a Drill model with the following fields:
- `title` (string, required): Concise drill title
- `type` (enum, required): One of `coding`, `debugging`, `system_design`
- `difficulty` (enum, required): One of `easy`, `medium`, `hard`
- `description` (string, required): Full problem description
- `requirements` (list of strings, required): Specific acceptance criteria
- `starter_code` (string, optional): Code template for the user
- `hints` (list of strings, optional): Progressive hints
- `expected_time_minutes` (integer, required): Between 5 and 120
- `tech_stack` (list of strings, optional): Relevant technologies
- `company_context` (string, optional): How drill relates to target company

#### Scenario: Valid drill with all fields
- **WHEN** a drill is created with all required and optional fields
- **THEN** the drill is valid and can be serialized

#### Scenario: Invalid drill with time outside bounds
- **WHEN** a drill is created with `expected_time_minutes` less than 5 or greater than 120
- **THEN** validation fails with an appropriate error

---

### Requirement: Configurable Generator Count

The system SHALL define a module constant `HOW_MANY_GENERATORS` that controls how many drill generator agents run in parallel.

- Default value: 3
- Valid range: 1-3
- Location: `backend/app/agents/drill/__init__.py`

Generator selection order based on count:
1. Coding Agent (always included)
2. Debugging Agent (if count >= 2)
3. Design Agent (if count == 3)

#### Scenario: Run with default 3 generators
- **WHEN** `HOW_MANY_GENERATORS = 3`
- **THEN** all three agents (coding, debugging, design) run in parallel

#### Scenario: Run with 2 generators
- **WHEN** `HOW_MANY_GENERATORS = 2`
- **THEN** only coding and debugging agents run in parallel

#### Scenario: Run with 1 generator
- **WHEN** `HOW_MANY_GENERATORS = 1`
- **THEN** only the coding agent runs
- **AND** evaluation is skipped (single candidate returned directly)

---

### Requirement: Parallel Drill Generation

The system SHALL generate drill candidates using specialized agents in parallel:
1. **Coding Agent**: Generates algorithm and data structure challenges
2. **Debugging Agent**: Generates bug-finding and troubleshooting exercises
3. **Design Agent**: Generates system architecture problems

The number of agents used is controlled by `HOW_MANY_GENERATORS`.

Each agent receives full context including:
- `company_name` and `role` from session
- `role_description` from session (if provided, up to 8000 chars)
- `CompanySummary` from company research (if completed)

#### Scenario: All configured generators succeed
- **WHEN** all configured generator agents complete successfully
- **THEN** the system has that many drill candidates for evaluation

#### Scenario: Partial generator failure
- **WHEN** 1 or more configured generator agents fail (timeout or error)
- **THEN** the system continues with the remaining successful candidates
- **AND** streams status messages about failures

#### Scenario: All generators fail
- **WHEN** all configured generator agents fail
- **THEN** the system returns an error indicating generation failed

---

### Requirement: Drill Evaluation and Selection

The system SHALL use an evaluator agent to select the best drill when multiple candidates exist.

Evaluation criteria with weights:
- **Role Relevance** (40%): Does the drill test skills needed for the role?
- **Difficulty Appropriateness** (30%): Is difficulty calibrated to seniority?
- **Company Fit** (30%): Does the drill reflect the company's domain?

The evaluator outputs a `DrillEvaluation` containing:
- The selected drill (full content)
- Which generator type produced it
- Selection reasoning
- Individual scores for each candidate

#### Scenario: Multiple candidates evaluated
- **WHEN** 2 or more candidates are available
- **THEN** the evaluator scores each candidate
- **AND** selects the highest-scoring drill
- **AND** provides reasoning for the selection

#### Scenario: Single candidate available
- **WHEN** only 1 candidate is available (from config or failures)
- **THEN** the system skips evaluation
- **AND** returns the single candidate's drill directly

---

### Requirement: Drill Generation API

The system SHALL expose drill generation via REST API endpoints.

#### POST `/api/generate-drill/{session_id}`

Generates a drill synchronously and returns the result.

Response (success):
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "company_name": "string",
    "role": "string",
    "drill": { /* Drill object */ },
    "generation_metadata": {
      "generators_used": ["coding", "debugging", "design"]
    }
  }
}
```

#### GET `/api/generate-drill/{session_id}/stream`

Streams drill generation progress via Server-Sent Events (SSE).

Event types:
- `status`: Progress updates with message
- `candidate`: When a generator completes (includes type and title)
- `complete`: Final drill result
- `error`: Generation error

#### Scenario: Generate drill for valid session
- **WHEN** POST `/api/generate-drill/{session_id}` is called with a valid session
- **THEN** the system generates a drill using the configured number of generators
- **AND** returns the selected drill in the response

#### Scenario: Generate drill for missing session
- **WHEN** POST `/api/generate-drill/{session_id}` is called with an invalid session_id
- **THEN** the system returns HTTP 404

#### Scenario: Stream drill generation
- **WHEN** GET `/api/generate-drill/{session_id}/stream` is called
- **THEN** the system streams SSE events showing generation progress
- **AND** the final event is either `complete` with the drill or `error`

---

### Requirement: Security Guardrails

All drill generation agents SHALL use the same security guardrails as existing agents:
- Input guardrail: Detect and block prompt injection attempts
- Output guardrail: Detect and block API key/secret leakage
- Agents include `SECURITY_RULES` in their instructions

#### Scenario: Injection attempt blocked
- **WHEN** user input contains prompt injection patterns
- **THEN** the input guardrail triggers
- **AND** the system returns a safe error message

#### Scenario: Leakage attempt blocked
- **WHEN** agent output contains potential secrets
- **THEN** the output guardrail triggers
- **AND** the system returns a safe error message

---

### Requirement: Session CompanySummary Storage

The system SHALL extend the Session dataclass to store company research results.

- Add `company_summary: CompanySummary | None` field to Session
- Update session after company research completes
- Drill generation reads CompanySummary from session

#### Scenario: Company research completes
- **WHEN** company research stream emits a `complete` event
- **THEN** the session is updated with the CompanySummary

#### Scenario: Drill generation with CompanySummary
- **WHEN** drill generation starts and session has CompanySummary
- **THEN** CompanySummary data is included in generator input

#### Scenario: Drill generation without CompanySummary
- **WHEN** drill generation starts and session has no CompanySummary
- **THEN** drill generation proceeds with only session data (graceful degradation)
