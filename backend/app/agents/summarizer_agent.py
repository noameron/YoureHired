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

For the tech_stack field, only include well-known, real-world technologies such as:
- Languages: Python, Java, JavaScript, TypeScript, Go, Rust, C, C++, C#, Ruby, Kotlin, Swift, Scala, PHP, R, etc.
- Frameworks: React, Angular, Vue, Django, Flask, Spring, .NET, Rails, Express, Next.js, FastAPI, etc.
- Tools: Docker, Kubernetes, AWS, GCP, Azure, Terraform, Jenkins, Git, PostgreSQL, MongoDB, Redis, Kafka, etc.
If a technology name is unfamiliar or looks nonsensical, omit it.
{SECURITY_RULES}"""

summarizer_agent = Agent(
    name="CompanySummarizerAgent",
    instructions=SUMMARIZER_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=CompanySummary,
    input_guardrails=[injection_guardrail],
    output_guardrails=[leakage_guardrail],
)
