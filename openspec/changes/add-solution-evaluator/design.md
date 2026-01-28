## Context

Users complete drill exercises but receive no feedback. This change adds a solution evaluator agent that:
1. Analyzes submitted solutions against drill requirements
2. Provides structured feedback (strengths, improvements, score)
3. Persists feedback as markdown files for tracking
4. Feeds a summary back to drill generators to personalize future drills

**Stakeholders**: End users practicing for interviews, drill generation agents

**Constraints**:
- Must use existing guardrail patterns for security
- Feedback summary must be concise (max 500 chars) to fit in LLM context efficiently
- File paths must follow `docs/drills/feedbacks/<dd-mm-yyyy_hh-mm>/<company_name>_<role>.md`

## Goals / Non-Goals

**Goals**:
- Provide actionable, concrete feedback with examples from user's code
- Enable learning loop where weak areas inform next drill
- Persist feedback history for user review

**Non-Goals**:
- Code execution or automated testing of solutions
- Real-time collaboration or live feedback
- Grading against a reference solution (agent uses judgment)

## Decisions

### 1. Single Evaluator Agent (not multiple specialized)
**Decision**: Use one evaluator agent that assesses all aspects (correctness, quality, practices, edge cases).

**Alternatives considered**:
- Multiple specialized agents (correctness agent, style agent, etc.) - rejected due to added complexity, latency, and cost without clear benefit

### 2. Feedback File Format: Markdown
**Decision**: Store feedback as human-readable markdown files.

**Alternatives considered**:
- JSON files - rejected; less readable for users browsing history
- Database storage - rejected; adds infrastructure complexity, markdown files are sufficient for MVP

### 3. Summary Length: 500 Characters
**Decision**: Cap `summary_for_next_drill` at 500 chars.

**Rationale**: Enough context for drill generators to understand weak areas without bloating prompts. Roughly 100-125 tokens.

### 4. Feedback UI: Expandable Cards
**Decision**: Display feedback in expandable card sections rather than inline text.

**Rationale**: Allows users to scan quickly (titles visible) then drill into details. Matches existing hint UI pattern.

## Data Flow

```
User submits solution
        │
        ▼
POST /api/evaluate-solution/{session_id}
        │
        ▼
Solution Evaluator Agent
  - Input: drill, solution, company/role context
  - Output: SolutionFeedback (strengths, improvements, score, summary)
        │
        ├──► Persist to docs/drills/feedbacks/<timestamp>/<company_role>.md
        │
        └──► Return to frontend
                │
                ▼
        Display FeedbackCard UI
                │
                ▼
        User clicks "Practice Weak Areas"
                │
                ▼
POST /api/generate-drill/{session_id}?feedback_summary=...
        │
        ▼
Drill Generators receive summary as context
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Evaluator hallucinating code examples | Instruct agent to quote directly from submitted solution |
| Long solutions causing timeouts | Set reasonable timeout, truncate very long solutions with note |
| File system permissions | Use project-relative path, create directories as needed |
| Prompt injection in solutions | Apply existing input guardrail |

## Open Questions

- None currently; design is straightforward extension of existing patterns
