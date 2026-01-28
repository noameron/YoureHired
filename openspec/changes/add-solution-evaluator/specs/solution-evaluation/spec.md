## ADDED Requirements

### Requirement: Solution Evaluation Data Model

The system SHALL define an evaluation feedback model with the following structure:
- `strengths` (list of objects): What the user did well, each with:
  - `title` (string): Brief strength category
  - `description` (string): Explanation with concrete examples from the solution
- `improvements` (list of objects): Areas needing improvement, each with:
  - `title` (string): Brief improvement category
  - `description` (string): Explanation with concrete examples from the solution
  - `suggestion` (string): Actionable advice for improvement
- `overall_score` (integer, 1-10): Overall solution quality score
- `summary_for_next_drill` (string, max 500 chars): Concise LLM-friendly summary of weak areas to inform next drill generation

#### Scenario: Valid evaluation with strengths and improvements
- **WHEN** the evaluator agent produces feedback with all required fields
- **THEN** the feedback is valid and can be serialized

#### Scenario: Summary length constraint
- **WHEN** the evaluator generates `summary_for_next_drill` exceeding 500 characters
- **THEN** validation fails with an appropriate error

---

### Requirement: Solution Evaluator Agent

The system SHALL provide a solution evaluator agent that analyzes user submissions against drill requirements.

The agent receives:
- The original drill (title, description, requirements, starter_code)
- The user's submitted solution
- Company and role context from session

The agent evaluates:
- **Correctness**: Does the solution meet the stated requirements?
- **Code Quality**: Is the code readable, maintainable, and well-structured?
- **Best Practices**: Does it follow language/framework conventions?
- **Edge Cases**: Are edge cases and error conditions handled?

#### Scenario: Evaluate complete solution
- **WHEN** a user submits a solution for a drill
- **THEN** the evaluator agent analyzes the solution
- **AND** returns structured feedback with concrete examples from the submitted code

#### Scenario: Evaluate partial solution
- **WHEN** a user submits an incomplete solution
- **THEN** the evaluator acknowledges completed parts as strengths
- **AND** identifies missing requirements as areas for improvement

---

### Requirement: Feedback Persistence

The system SHALL save evaluation feedback as markdown files at:
`docs/drills/feedbacks/<dd-mm-yyyy_hh-mm>/<company_name>_<role>.md`

File naming rules:
- Date format: `dd-mm-yyyy_hh-mm` (24-hour format, UTC)
- Company name and role: lowercase, spaces replaced with underscores
- Example: `docs/drills/feedbacks/28-01-2026_14-30/google_senior_backend_engineer.md`

The markdown file SHALL contain:
- Drill title and type
- Submission timestamp
- Overall score
- Strengths section with bullet points
- Improvements section with bullet points and suggestions
- Summary for next drill

#### Scenario: Save feedback to file
- **WHEN** evaluation completes successfully
- **THEN** a markdown file is created at the specified path
- **AND** the directory structure is created if it doesn't exist

#### Scenario: Multiple submissions same minute
- **WHEN** a user submits multiple solutions within the same minute
- **THEN** subsequent files append a counter suffix (e.g., `_2`, `_3`)

---

### Requirement: Solution Evaluation API

The system SHALL expose solution evaluation via REST API endpoint.

#### POST `/api/evaluate-solution/{session_id}`

Request body:
```json
{
  "drill_id": "string",
  "solution": "string"
}
```

Response (success):
```json
{
  "success": true,
  "data": {
    "strengths": [
      {
        "title": "string",
        "description": "string"
      }
    ],
    "improvements": [
      {
        "title": "string",
        "description": "string",
        "suggestion": "string"
      }
    ],
    "overall_score": 7,
    "summary_for_next_drill": "string",
    "feedback_file_path": "string"
  }
}
```

#### Scenario: Evaluate solution for valid session
- **WHEN** POST `/api/evaluate-solution/{session_id}` is called with valid session and solution
- **THEN** the system evaluates the solution
- **AND** returns structured feedback
- **AND** persists feedback to markdown file

#### Scenario: Evaluate solution for missing session
- **WHEN** POST `/api/evaluate-solution/{session_id}` is called with invalid session_id
- **THEN** the system returns HTTP 404

#### Scenario: Empty solution rejected
- **WHEN** POST `/api/evaluate-solution/{session_id}` is called with empty solution
- **THEN** the system returns HTTP 422 with validation error

---

### Requirement: Feedback UI Display

The system SHALL display evaluation feedback in a visually structured format after submission.

UI structure:
- **Score Badge**: Prominent display of overall score (1-10) with color coding
  - 1-4: Red (needs improvement)
  - 5-7: Yellow (satisfactory)
  - 8-10: Green (excellent)
- **Strengths Section**: Green-accented card with checkmark icons
  - Each strength as expandable item showing title and description
- **Improvements Section**: Orange-accented card with lightbulb icons
  - Each improvement as expandable item showing title, description, and suggestion
- **Next Steps**: Call-to-action button to generate next drill based on feedback

#### Scenario: Display feedback after submission
- **WHEN** the user submits a solution and evaluation completes
- **THEN** the feedback UI replaces the solution input section
- **AND** displays score, strengths, and improvements in structured cards

#### Scenario: Generate next drill from feedback
- **WHEN** the user clicks "Practice Weak Areas" button
- **THEN** the system triggers drill generation with the `summary_for_next_drill` as additional context

---

### Requirement: Security Guardrails

The solution evaluator agent SHALL use the same security guardrails as existing agents:
- Input guardrail: Detect and block prompt injection attempts in submitted solutions
- Output guardrail: Detect and block API key/secret leakage in feedback
- Agent includes `SECURITY_RULES` in its instructions

#### Scenario: Injection attempt in solution blocked
- **WHEN** submitted solution contains prompt injection patterns
- **THEN** the input guardrail triggers
- **AND** the system returns a safe error message

#### Scenario: Leakage attempt blocked
- **WHEN** agent output contains potential secrets
- **THEN** the output guardrail triggers
- **AND** the system returns a safe error message
