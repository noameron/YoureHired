## Context

YoureHired helps users practice for tech interviews by generating tailored tasks based on their target company and role. The platform currently supports role selection and company research. This change adds the core drill generation capability.

**Stakeholders:**
- End users: Need relevant, challenging practice tasks
- Platform: Needs diverse drill types to cover interview formats
- LLM costs: Must balance quality with API usage

**Constraints:**
- Must follow existing agent patterns (guardrails, structured outputs)
- Must integrate with existing session-based flow
- Should provide real-time feedback during generation

## Goals / Non-Goals

**Goals:**
- Generate diverse drill types (coding, debugging, system design)
- Select best drill based on role/company fit
- Configurable number of generators (like HOW_MANY_SEARCHES)
- Stream progress for responsive UX
- Reuse existing guardrails for security

**Non-Goals:**
- User solution evaluation/grading (future feature)
- Drill history tracking (future feature)
- Difficulty progression based on performance (future feature)
- Frontend UI for drills (separate change)

## Decisions

### Decision 1: Use 3 specialized generators + 1 evaluator (not single agent)

**What:** Separate agents for coding, debugging, and design drills, with an evaluator to pick the best.

**Why:**
- Each drill type needs specialized prompting (debugging needs buggy code, design needs scale requirements)
- Evaluator provides quality control and reasoning for selection
- Parallel execution reduces latency vs sequential attempts

**Alternatives considered:**
- Single agent with drill type parameter: Less specialized, lower quality output
- User chooses drill type: Removes intelligent selection benefit
- Random single generator: Misses opportunity to pick best fit for role

### Decision 2: Parallel execution with asyncio.gather

**What:** Run all configured generators simultaneously, not sequentially.

**Why:**
- 3 sequential LLM calls = ~15-30 seconds total
- 3 parallel LLM calls = ~5-10 seconds total (3x faster)
- Pattern proven in existing `research_manager.py` from OpenAI examples

### Decision 3: Module constant for generator count (not env var)

**What:** `HOW_MANY_GENERATORS = 3` in `__init__.py`, matching `HOW_MANY_SEARCHES` pattern.

**Why:**
- Consistent with existing planner_agent.py pattern
- Rarely needs runtime changes
- Simpler than environment variable configuration

### Decision 4: Skip evaluator for single candidate

**What:** If only 1 generator succeeds (or count=1), return drill directly without evaluation.

**Why:**
- Evaluating 1 candidate is wasteful (no comparison to make)
- Saves an LLM call when generators fail
- Faster response for count=1 configuration

### Decision 5: 90-second timeout per agent (vs 60s for research)

**What:** Longer timeout for drill generation than company research.

**Why:**
- Drill generation is more complex (code, requirements, hints)
- Structured output has more fields to populate
- Worth waiting slightly longer for quality output

### Decision 6: Pass full context (roleDescription + CompanySummary) to generators

**What:** Generators receive all available context for maximum drill tailoring.

**Why:**
- `roleDescription` (up to 8000 chars) contains user-specific requirements
- `CompanySummary` provides tech stack, culture, interview tips from research
- More context = more relevant drills = better interview prep

**Implementation:**
- Extend `Session` dataclass to store `company_summary` after research
- `company_info.py` updates session when research completes
- `drill_generation.py` reads both from session and builds rich input

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| All generators fail | User gets error, no drill | Clear error message, retry option |
| LLM generates invalid structure | Pydantic validation fails | Catch exception, use any valid candidate |
| Evaluator picks suboptimal drill | User gets less relevant task | Clear scoring criteria, tunable weights |
| High LLM cost (4 calls per drill) | Increased API spend | Configurable count, caching (future) |
| Long generation time (~10s) | Poor UX | SSE streaming shows progress |

## Migration Plan

No migration needed - this is a new capability.

**Rollback:** Remove drill router from `api/__init__.py` to disable feature.

## Open Questions

1. **Caching:** Should we cache drills for identical (company, role) pairs?
   - Deferred: Start without caching, add if needed for cost/performance

2. **User preferences:** Should users request specific drill types?
   - Deferred: Evaluator selection provides good default experience

3. **Difficulty progression:** Adapt difficulty based on prior performance?
   - Deferred: Requires drill history tracking (future feature)

4. **Company context:** How to get CompanySummary for drill generation?
   - **Decision:** Extend Session to store `company_summary: CompanySummary | None`
   - Session updated when company research completes
   - Drill generation reads from session (no re-fetch needed)
   - Drill generation works without it (graceful degradation)
