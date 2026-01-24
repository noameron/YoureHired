from agents import Agent
from app.schemas.company_info import SearchPlan

HOW_MANY_SEARCHES = 2

PLANNER_INSTRUCTIONS = f"""You are a research planner. Given a company name and role,
plan {HOW_MANY_SEARCHES} web searches to gather information about the company.

Focus on:
1. Company overview and industry
2. Tech stack and engineering culture
3. Recent news and interview experiences for the role
"""

planner_agent = Agent(
    name="CompanyPlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SearchPlan,
)
