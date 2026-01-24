from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings

from app.agents.guardrails import (
    SECURITY_RULES,
    injection_guardrail,
    leakage_guardrail,
)

SEARCH_INSTRUCTIONS = f"""You are a research assistant. Given a search query,
search the web and produce a concise 2-3 paragraph summary of the results.
Capture the main points relevant to understanding the company.
{SECURITY_RULES}"""

search_agent = Agent(
    name="CompanySearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
    input_guardrails=[injection_guardrail],
    output_guardrails=[leakage_guardrail],
)
