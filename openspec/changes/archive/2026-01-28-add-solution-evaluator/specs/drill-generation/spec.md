## MODIFIED Requirements

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
- `previous_feedback_summary` from last evaluation (if available, max 500 chars)

When `previous_feedback_summary` is provided, generators SHALL:
- Prioritize creating drills that address the identified weak areas
- Adjust difficulty based on previous performance
- Focus on skill gaps mentioned in the summary

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

#### Scenario: Generate drill with feedback context
- **WHEN** drill generation is triggered with `previous_feedback_summary`
- **THEN** all generator agents receive the summary as additional context
- **AND** prioritize drills targeting the identified weak areas
