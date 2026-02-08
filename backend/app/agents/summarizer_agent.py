from agents import Agent

from app.agents.guardrails import (
    SECURITY_RULES,
    injection_guardrail,
    leakage_guardrail,
)
from app.model_config import DEFAULT_MODEL
from app.schemas.company_info import CompanySummary

SUMMARIZER_INSTRUCTIONS = f"""You are a company research summarizer.
Given search results about a company, create a structured summary
to help construct interview style questions based on company summary
and {{role}} position in the company.

Be concise but informative. Include tech stack if found.
{SECURITY_RULES}"""

summarizer_agent = Agent(
    name="CompanySummarizerAgent",
    instructions=SUMMARIZER_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=CompanySummary,
    input_guardrails=[injection_guardrail],
    output_guardrails=[leakage_guardrail],
)
