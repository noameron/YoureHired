from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings

SEARCH_INSTRUCTIONS = """You are a research assistant. Given a search query,
search the web and produce a concise 2-3 paragraph summary of the results.
Capture the main points relevant to understanding the company."""

search_agent = Agent(
    name="CompanySearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
