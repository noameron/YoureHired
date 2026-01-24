import asyncio
from typing import AsyncGenerator

from agents import Runner
from app.schemas.company_info import SearchPlan, SearchQuery, CompanySummary
from app.agents.planner_agent import planner_agent
from app.agents.search_agent import search_agent
from app.agents.summarizer_agent import summarizer_agent

AGENT_TIMEOUT = 60  # seconds


async def research_company_stream(
    company_name: str,
    role: str
) -> AsyncGenerator[dict, None]:
    """
    Stream research progress and final results with timeout.
    Yields dict events: {"type": "status"|"complete"|"error", ...}
    """
    try:
        # Step 1: Plan searches
        yield {"type": "status", "message": "Planning research strategy..."}
        plan_input = f"Company: {company_name}\nRole: {role}"
        plan_result = await asyncio.wait_for(
            Runner.run(planner_agent, plan_input),
            timeout=AGENT_TIMEOUT
        )
        search_plan: SearchPlan = plan_result.final_output
        yield {"type": "status", "message": f"Found {len(search_plan.searches)} areas to research"}

        # Step 2: Execute searches sequentially, streaming each one
        search_results = []
        for i, item in enumerate(search_plan.searches, 1):
            yield {"type": "status", "message": f"Searching ({i}/{len(search_plan.searches)}): {item.reason}"}
            try:
                search_input = f"Search term: {item.query}\nReason: {item.reason}"
                result = await asyncio.wait_for(
                    Runner.run(search_agent, search_input),
                    timeout=AGENT_TIMEOUT
                )
                search_results.append(result.final_output)
            except asyncio.TimeoutError:
                yield {"type": "status", "message": f"Search {i} timed out, continuing..."}
            except Exception:
                yield {"type": "status", "message": f"Search {i} failed, continuing..."}

        if not search_results:
            yield {"type": "error", "message": "All searches failed. Please try again."}
            return

        # Step 3: Summarize
        yield {"type": "status", "message": "Analyzing findings..."}
        combined = "\n\n".join(search_results)
        summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
        summary_result = await asyncio.wait_for(
            Runner.run(summarizer_agent, summary_input),
            timeout=AGENT_TIMEOUT
        )

        # Final result
        yield {"type": "complete", "data": summary_result.final_output.model_dump()}

    except asyncio.TimeoutError:
        yield {"type": "error", "message": "Research timed out. Please try again."}
    except Exception as e:
        yield {"type": "error", "message": f"Research failed: {str(e)}"}


async def research_company(company_name: str, role: str) -> CompanySummary:
    """
    Execute company research flow.

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
        search_input = f"Search term: {item.query}\nReason: {item.reason}"
        result = await Runner.run(search_agent, search_input)
        return result.final_output

    tasks = [asyncio.create_task(run_search(s)) for s in search_plan.searches]
    search_results = await asyncio.gather(*tasks)

    # Step 3: Summarize results
    combined = "\n\n".join(search_results)
    summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
    summary_result = await Runner.run(summarizer_agent, summary_input)

    return summary_result.final_output
