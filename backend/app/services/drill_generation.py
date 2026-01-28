"""
Drill generation orchestration service.

Coordinates generator agents in parallel, then uses an evaluator
to select the best drill.
"""
import asyncio
from collections.abc import AsyncGenerator

from agents import Runner
from agents.exceptions import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

from app.agents.drill import (
    HOW_MANY_GENERATORS,
    coding_drill_agent,
    debugging_drill_agent,
    design_drill_agent,
    evaluator_agent,
)
from app.agents.guardrails.exceptions import (
    SAFE_INJECTION_MESSAGE,
    SAFE_LEAKAGE_MESSAGE,
)
from app.config import settings
from app.schemas.company_info import CompanySummary
from app.schemas.drill import (
    Drill,
    DrillCandidate,
    DrillEvaluation,
    DrillType,
)

# All available generators in priority order
ALL_GENERATORS = [
    (coding_drill_agent, DrillType.CODING, "coding challenge"),
    (debugging_drill_agent, DrillType.DEBUGGING, "debugging scenario"),
    (design_drill_agent, DrillType.SYSTEM_DESIGN, "system design problem"),
]


def _build_generator_input(
    company_name: str,
    role: str,
    role_description: str | None,
    company_summary: CompanySummary | None = None,
    previous_feedback_summary: str | None = None,
) -> str:
    """Build the input prompt for generator agents."""
    parts = [
        f"Company: {company_name}",
        f"Role: {role}",
    ]

    # Include full role description (up to 8000 chars)
    if role_description:
        parts.append(f"Role Description: {role_description}")

    # Include company research if available
    if company_summary:
        parts.append("\nCompany Context:")
        if company_summary.industry:
            parts.append(f"Industry: {company_summary.industry}")
        parts.append(f"Description: {company_summary.description}")
        if company_summary.tech_stack:
            tech = company_summary.tech_stack
            all_tech = tech.languages + tech.frameworks + tech.tools
            if all_tech:
                parts.append(f"Tech Stack: {', '.join(all_tech)}")
        if company_summary.engineering_culture:
            parts.append(f"Engineering Culture: {company_summary.engineering_culture}")
        if company_summary.interview_tips:
            parts.append(f"Interview Tips: {company_summary.interview_tips}")

    # Include feedback from previous drill to target weak areas
    if previous_feedback_summary:
        parts.append("\nPrevious Drill Feedback (target these weak areas):")
        parts.append(previous_feedback_summary)

    return "\n".join(parts)


def _build_evaluator_input(
    company_name: str,
    role: str,
    candidates: list[DrillCandidate],
) -> str:
    """Build the input prompt for the evaluator agent."""
    parts = [
        f"Company: {company_name}",
        f"Role: {role}",
        "",
        "CANDIDATES TO EVALUATE:",
        "",
    ]

    for i, candidate in enumerate(candidates, 1):
        parts.append(f"--- Candidate {i} ({candidate.generator_type.value}) ---")
        parts.append(f"Title: {candidate.drill.title}")
        parts.append(f"Type: {candidate.drill.type.value}")
        parts.append(f"Difficulty: {candidate.drill.difficulty.value}")
        parts.append(f"Description: {candidate.drill.description}")
        parts.append(f"Requirements: {', '.join(candidate.drill.requirements)}")
        parts.append(f"Expected Time: {candidate.drill.expected_time_minutes} minutes")
        parts.append(f"Tech Stack: {', '.join(candidate.drill.tech_stack)}")
        if candidate.drill.starter_code:
            parts.append(f"Starter Code:\n```\n{candidate.drill.starter_code}\n```")
        if candidate.drill.hints:
            parts.append(f"Hints: {', '.join(candidate.drill.hints)}")
        parts.append(f"Company Context: {candidate.drill.company_context or 'N/A'}")
        parts.append(f"Generator Reasoning: {candidate.reasoning}")
        parts.append(f"Generator Confidence: {candidate.confidence_score}")
        parts.append("")

    return "\n".join(parts)


async def generate_drill(
    company_name: str,
    role: str,
    role_description: str | None = None,
    company_summary: CompanySummary | None = None,
    previous_feedback_summary: str | None = None,
) -> Drill:
    """
    Generate a drill using parallel generators and evaluation.

    Args:
        company_name: Target company name
        role: Job role
        role_description: Optional detailed role description
        company_summary: Optional company research summary for context
        previous_feedback_summary: Optional feedback from previous drill to target weak areas

    Returns:
        The best drill selected by the evaluator

    Raises:
        InputGuardrailTripwireTriggered: If input contains injection
        OutputGuardrailTripwireTriggered: If output contains leakage
        TimeoutError: If generation times out
        ValueError: If no valid candidates are generated
    """
    generator_input = _build_generator_input(
        company_name, role, role_description, company_summary, previous_feedback_summary
    )

    # Select generators based on configuration
    generators = ALL_GENERATORS[:HOW_MANY_GENERATORS]

    async def run_generator(
        agent, drill_type: DrillType
    ) -> DrillCandidate | None:
        """Run a single generator with error handling."""
        try:
            result = await asyncio.wait_for(
                Runner.run(agent, generator_input),
                timeout=settings.drill_generation_agent_timeout,
            )
            candidate: DrillCandidate = result.final_output
            # Ensure generator_type matches the agent
            candidate.generator_type = drill_type
            return candidate
        except TimeoutError:
            return None
        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            raise  # Re-raise guardrail exceptions
        except Exception:
            return None

    # Execute in parallel
    tasks = [
        asyncio.create_task(run_generator(agent, drill_type))
        for agent, drill_type, _ in generators
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter successful candidates
    candidates = [r for r in results if isinstance(r, DrillCandidate)]

    if not candidates:
        raise ValueError("All generators failed to produce candidates")

    # If only one candidate, return it directly
    if len(candidates) == 1:
        return candidates[0].drill

    # Evaluate and select the best
    evaluator_input = _build_evaluator_input(company_name, role, candidates)
    eval_result = await asyncio.wait_for(
        Runner.run(evaluator_agent, evaluator_input),
        timeout=settings.drill_generation_agent_timeout,
    )

    evaluation: DrillEvaluation = eval_result.final_output
    return evaluation.selected_drill


async def generate_drill_stream(
    company_name: str,
    role: str,
    role_description: str | None = None,
    company_summary: CompanySummary | None = None,
    previous_feedback_summary: str | None = None,
) -> AsyncGenerator[dict[str, object], None]:
    """
    Stream drill generation progress and final result.

    Yields dict events with type: "status", "candidate", "complete", or "error"
    """
    try:
        yield {"type": "status", "message": "Starting drill generation..."}

        generator_input = _build_generator_input(
            company_name, role, role_description, company_summary, previous_feedback_summary
        )

        # Select generators based on configuration
        generators = ALL_GENERATORS[:HOW_MANY_GENERATORS]

        yield {
            "type": "status",
            "message": f"Generating {len(generators)} drill candidates in parallel...",
        }

        candidates: list[DrillCandidate] = []

        async def run_generator_with_status(
            agent, drill_type: DrillType, desc: str
        ) -> tuple[str, DrillCandidate | str | None, str]:
            """Run generator and return status tuple."""
            try:
                result = await asyncio.wait_for(
                    Runner.run(agent, generator_input),
                    timeout=settings.drill_generation_agent_timeout,
                )
                candidate: DrillCandidate = result.final_output
                candidate.generator_type = drill_type
                return ("success", candidate, desc)
            except TimeoutError:
                return ("timeout", None, desc)
            except InputGuardrailTripwireTriggered:
                raise  # Re-raise guardrail exceptions
            except OutputGuardrailTripwireTriggered:
                raise  # Re-raise guardrail exceptions
            except Exception as e:
                return ("error", str(e), desc)

        tasks = [
            asyncio.create_task(run_generator_with_status(agent, dt, desc))
            for agent, dt, desc in generators
        ]

        # Process as they complete
        for coro in asyncio.as_completed(tasks):
            status, result, desc = await coro

            if status == "success" and isinstance(result, DrillCandidate):
                candidate = result
                candidates.append(candidate)
                yield {
                    "type": "candidate",
                    "generator": candidate.generator_type.value,
                    "title": candidate.drill.title,
                }
                yield {
                    "type": "status",
                    "message": f"Generated {desc}: {candidate.drill.title}",
                }
            elif status == "timeout":
                yield {
                    "type": "status",
                    "message": f"{desc.capitalize()} timed out, continuing...",
                }
            else:
                yield {
                    "type": "status",
                    "message": f"{desc.capitalize()} failed, continuing...",
                }

        # Check if we have any candidates
        if not candidates:
            yield {
                "type": "error",
                "message": "All generators failed. Please try again.",
            }
            return

        # Single candidate - return directly
        if len(candidates) == 1:
            yield {
                "type": "status",
                "message": "Only one candidate generated, using it directly.",
            }
            yield {"type": "complete", "data": candidates[0].drill.model_dump()}
            return

        # Multiple candidates - evaluate
        yield {
            "type": "status",
            "message": f"Evaluating {len(candidates)} candidates...",
        }

        evaluator_input = _build_evaluator_input(company_name, role, candidates)

        eval_result = await asyncio.wait_for(
            Runner.run(evaluator_agent, evaluator_input),
            timeout=settings.drill_generation_agent_timeout,
        )

        evaluation: DrillEvaluation = eval_result.final_output

        reasoning_preview = evaluation.selection_reasoning[:100]
        yield {
            "type": "status",
            "message": f"Selected: {evaluation.selected_generator.value} - "
            f"{reasoning_preview}...",
        }

        yield {"type": "complete", "data": evaluation.selected_drill.model_dump()}

    except InputGuardrailTripwireTriggered:
        yield {"type": "error", "message": SAFE_INJECTION_MESSAGE}
    except OutputGuardrailTripwireTriggered:
        yield {"type": "error", "message": SAFE_LEAKAGE_MESSAGE}
    except TimeoutError:
        yield {
            "type": "error",
            "message": "Drill generation timed out. Please try again.",
        }
    except ValueError as e:
        yield {"type": "error", "message": str(e)}
    except Exception as e:
        yield {"type": "error", "message": f"Drill generation failed: {e!s}"}
