import asyncio
from collections.abc import AsyncGenerator

from agents import Runner
from agents.exceptions import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

from app.agents.guardrails.exceptions import (
    SAFE_INJECTION_MESSAGE,
    SAFE_LEAKAGE_MESSAGE,
)
from app.agents.planner_agent import planner_agent
from app.agents.search_agent import search_agent
from app.agents.summarizer_agent import summarizer_agent
from app.config import settings
from app.schemas.company_info import CompanySummary, SearchPlan, SearchQuery


async def research_company_stream(
    company_name: str, role: str
) -> AsyncGenerator[dict[str, object], None]:
    """
    Stream research progress and final results with timeout.
    Yields dict events: {"type": "status"|"complete"|"error", ...}
    """
    try:
        # Step 1: Plan searches
        yield {"type": "status", "message": "Planning research strategy..."}
        plan_input = f"Company: {company_name}\nRole: {role}"
        plan_result = await asyncio.wait_for(
            Runner.run(planner_agent, plan_input), timeout=settings.company_research_agent_timeout
        )
        search_plan: SearchPlan = plan_result.final_output
        yield {"type": "status", "message": f"Found {len(search_plan.searches)} areas to research"}

        # Step 2: Execute searches in parallel with streaming progress
        # Note: We use asyncio.as_completed() instead of asyncio.gather() to stream
        # progress updates as each search completes, rather than waiting for all to finish.
        # This provides better UX by showing real-time progress. The function complexity
        # (cyclomatic ~13) is inherent to handling multiple status types (success/timeout/error)
        # while streaming updates for each completed search.
        async def run_search(item: SearchQuery) -> tuple[str, str | None, str]:
            """Run a single search and return (reason, result_or_none, status)."""
            try:
                search_input = f"Search term: {item.query}\nReason: {item.reason}"
                result = await asyncio.wait_for(
                    Runner.run(search_agent, search_input),
                    timeout=settings.company_research_agent_timeout,
                )
                return (item.reason, str(result.final_output), "success")
            except TimeoutError:
                return (item.reason, None, "timed_out")
            except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
                raise
            except Exception:
                return (item.reason, None, "failed")

        search_results: list[str] = []
        tasks = [asyncio.create_task(run_search(item)) for item in search_plan.searches]
        total_tasks = len(tasks)
        completed = 0

        for coro in asyncio.as_completed(tasks):
            reason, result, status = await coro
            completed += 1
            if status == "success" and result is not None:
                search_results.append(result)
                yield {
                    "type": "status",
                    "message": f"Completed ({completed}/{total_tasks}): {reason}",
                }
            elif status == "timed_out":
                msg = f"Timed out ({completed}/{total_tasks}): {reason}, continuing..."
                yield {"type": "status", "message": msg}
            else:
                msg = f"Failed ({completed}/{total_tasks}): {reason}, continuing..."
                yield {"type": "status", "message": msg}

        if not search_results:
            yield {"type": "error", "message": "All searches failed. Please try again."}
            return

        # Step 3: Summarize
        yield {"type": "status", "message": "Analyzing findings..."}
        combined = "\n\n".join(search_results)
        summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
        summary_result = await asyncio.wait_for(
            Runner.run(summarizer_agent, summary_input),
            timeout=settings.company_research_agent_timeout,
        )

        # Final result
        yield {"type": "complete", "data": summary_result.final_output.model_dump()}

    except InputGuardrailTripwireTriggered:
        yield {"type": "error", "message": SAFE_INJECTION_MESSAGE}
    except OutputGuardrailTripwireTriggered:
        yield {"type": "error", "message": SAFE_LEAKAGE_MESSAGE}
    except TimeoutError:
        yield {"type": "error", "message": "Research timed out. Please try again."}
    except Exception as e:
        yield {"type": "error", "message": f"Research failed: {str(e)}"}


async def research_company(company_name: str, role: str) -> CompanySummary:
    """
    Execute company research flow.

    Args:
        company_name: Validated company name from session
        role: Validated role from session

    Raises:
        InputGuardrailTripwireTriggered: If input contains potential injection
        OutputGuardrailTripwireTriggered: If output contains potential leakage
    """
    # Step 1: Plan searches
    plan_input = f"Company: {company_name}\nRole: {role}"
    plan_result = await Runner.run(planner_agent, plan_input)
    search_plan: SearchPlan = plan_result.final_output

    # Step 2: Execute searches in parallel
    async def run_search(item: SearchQuery) -> str:
        search_input = f"Search term: {item.query}\nReason: {item.reason}"
        result = await Runner.run(search_agent, search_input)
        return str(result.final_output)

    tasks = [asyncio.create_task(run_search(s)) for s in search_plan.searches]
    search_results = await asyncio.gather(*tasks)

    # Step 3: Summarize results
    combined = "\n\n".join(search_results)
    summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
    summary_result = await Runner.run(summarizer_agent, summary_input)

    result: CompanySummary = summary_result.final_output
    return result
