from agents import Agent, Tool, WebSearchTool
from agents.model_settings import ModelSettings

from app.agents.guardrails import (
    SECURITY_RULES,
    injection_guardrail,
    leakage_guardrail,
)
from app.model_config import DEFAULT_MODEL, SUPPORTS_WEB_SEARCH

SEARCH_INSTRUCTIONS = f"""You are a research assistant. Given a search query,
search the web and produce a concise 2-3 paragraph summary of the results.
Capture the main points relevant to understanding the company.
{SECURITY_RULES}"""

_tools: list[Tool] = [WebSearchTool(search_context_size="low")] if SUPPORTS_WEB_SEARCH else []
_model_settings = ModelSettings(tool_choice="required") if SUPPORTS_WEB_SEARCH else ModelSettings()

search_agent = Agent(
    name="CompanySearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=_tools,
    model=DEFAULT_MODEL,
    model_settings=_model_settings,
    input_guardrails=[injection_guardrail],
    output_guardrails=[leakage_guardrail],
)
