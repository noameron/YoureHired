import asyncio
from collections.abc import AsyncGenerator

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
from app.services.session_store import Session, session_store
from app.services.task_registry import run_agent_streamed


async def _plan_searches(company_name: str, role: str, session_id: str) -> SearchPlan:
    """Generate search plan with timeout."""
    plan_input = f"Company: {company_name}\nRole: {role}"
    output = await run_agent_streamed(
        planner_agent, plan_input, session_id,
        timeout=settings.company_research_agent_timeout,
    )
    if output is None:
        raise RuntimeError("Search planning returned no result — the agent may have been cancelled")
    return output  # type: ignore[no-any-return]


async def _run_single_search(
    item: SearchQuery, session_id: str
) -> tuple[str, str | None, str]:
    """Execute a single search. Returns (reason, result_or_none, status)."""
    try:
        search_input = f"Search term: {item.query}\nReason: {item.reason}"
        output = await run_agent_streamed(
            search_agent, search_input, session_id,
            timeout=settings.company_research_agent_timeout,
        )
        if output is None:
            return (item.reason, None, "failed")
        return (item.reason, str(output), "success")
    except TimeoutError:
        return (item.reason, None, "timed_out")
    except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
        raise
    except Exception:
        return (item.reason, None, "failed")


async def _summarize_results(
    company_name: str, role: str, search_results: list[str], session_id: str
) -> CompanySummary:
    """Summarize search results with timeout."""
    combined = "\n\n".join(search_results)
    summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
    output = await run_agent_streamed(
        summarizer_agent, summary_input, session_id,
        timeout=settings.company_research_agent_timeout,
    )
    if output is None:
        raise RuntimeError(
            "Research summarization returned no result"
            " — the agent may have been cancelled"
        )
    return output  # type: ignore[no-any-return]


async def _execute_searches(
    searches: list[SearchQuery], session_id: str
) -> AsyncGenerator[dict[str, object] | str, None]:
    """
    Execute searches in parallel, streaming progress.
    Yields status events (dict) and successful results (str).
    """
    tasks = [
        asyncio.create_task(_run_single_search(item, session_id))
        for item in searches
    ]
    total = len(tasks)
    completed = 0

    for coro in asyncio.as_completed(tasks):
        reason, result, status = await coro
        completed += 1

        if status == "success":
            msg = f"Completed ({completed}/{total}): {reason}"
        elif status == "timed_out":
            msg = f"Timed out ({completed}/{total}): {reason}, continuing..."
        else:
            msg = f"Failed ({completed}/{total}): {reason}, continuing..."
        yield {"type": "status", "message": msg}

        if status == "success" and result is not None:
            yield result


async def research_company_stream(
    company_name: str, role: str, session_id: str
) -> AsyncGenerator[dict[str, object], None]:
    """Stream research progress and final results with timeout."""
    try:
        # Step 1: Plan searches
        yield {"type": "status", "message": "Planning research strategy..."}
        search_plan = await _plan_searches(company_name, role, session_id)
        yield {"type": "status", "message": f"Found {len(search_plan.searches)} areas to research"}

        # Step 2: Execute searches, streaming progress
        search_results: list[str] = []
        async for item in _execute_searches(search_plan.searches, session_id):
            if isinstance(item, dict):
                yield item
            else:
                search_results.append(item)

        if not search_results:
            yield {"type": "error", "message": "All searches failed. Please try again."}
            return

        # Step 3: Summarize
        yield {"type": "status", "message": "Analyzing findings..."}
        summary = await _summarize_results(company_name, role, search_results, session_id)
        yield {"type": "complete", "data": summary.model_dump()}

    except InputGuardrailTripwireTriggered:
        yield {"type": "error", "message": SAFE_INJECTION_MESSAGE}
    except OutputGuardrailTripwireTriggered:
        yield {"type": "error", "message": SAFE_LEAKAGE_MESSAGE}
    except TimeoutError:
        yield {"type": "error", "message": "Research timed out. Please try again."}
    except Exception as e:
        yield {"type": "error", "message": f"Research failed: {str(e)}"}


async def consume_research_stream(
    company_name: str, role: str, session_id: str
) -> CompanySummary:
    """
    Consume research stream and return final summary.
    Raises RuntimeError on failure.
    """
    async for event in research_company_stream(company_name, role, session_id):
        if event["type"] == "complete":
            return CompanySummary.model_validate(event["data"])
        if event["type"] == "error":
            raise RuntimeError(str(event["message"]))
    raise RuntimeError("Research failed to complete")


async def ensure_company_research(
    session: Session, session_id: str
) -> CompanySummary | None:
    """Ensure company research is done, return summary (non-streaming)."""
    if session.company_summary:
        return session.company_summary

    async for event in research_company_stream(
        session.company_name, session.role, session_id
    ):
        if event["type"] == "complete":
            company_summary = CompanySummary.model_validate(event["data"])
            session_store.update_company_summary(session_id, company_summary)
            return company_summary

    return None
