from agents import Agent
from app.schemas.company_info import CompanySummary

SUMMARIZER_INSTRUCTIONS = """You are a company research summarizer.
Given search results about a company, create a structured summary
to help construct interview style questions based on company summary and {role} position in the company.

Be concise but informative. Include tech stack if found."""

summarizer_agent = Agent(
    name="CompanySummarizerAgent",
    instructions=SUMMARIZER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=CompanySummary,
)
