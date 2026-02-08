"""
Output guardrail for detecting API key and secret leakage.

Uses a two-tier approach:
1. Fast regex check for known patterns
2. LLM fallback for subtle leakage
"""

import re
from typing import Any

from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, output_guardrail

from app.agents.guardrails.patterns import check_leakage_patterns
from app.model_config import DEFAULT_MODEL
from app.schemas.guardrails import LeakageDetectorOutput

LEAKAGE_DETECTOR_INSTRUCTIONS = """You are a security analyst detecting sensitive data leakage.

Analyze the output and determine if it contains:
- API keys (OpenAI, Anthropic, Google, AWS, etc.)
- Passwords or secrets
- Authentication tokens (Bearer, JWT, etc.)
- Database connection strings with credentials
- Private keys or certificates
- Environment variable values with secrets
- Internal system paths or configurations that should not be exposed

Context: This output is company research information that should only contain
public information about companies, their tech stack, culture, and interview processes.

Flag anything that looks like it could be a secret or credential, even if partially obscured.
"""

leakage_detector_agent = Agent(
    name="LeakageDetectorAgent",
    instructions=LEAKAGE_DETECTOR_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=LeakageDetectorOutput,
)


@output_guardrail
async def leakage_guardrail(
    ctx: RunContextWrapper[Any], agent: Agent[Any], output: Any
) -> GuardrailFunctionOutput:
    """
    Output guardrail that detects API key and secret leakage.

    Uses fast regex check first, then LLM fallback for edge cases.
    """
    # Convert output to string if needed
    output_text = str(output) if not isinstance(output, str) else output

    # Fast path: check against known patterns
    has_leakage, matched_pattern = check_leakage_patterns(output_text)

    if has_leakage:
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info={
                "has_leakage": True,
                "reasoning": "Matched known leakage pattern",
                "leaked_type": matched_pattern,
            },
        )

    # LLM fallback for subtle leakage
    # Only run if output contains patterns that might indicate secrets
    if _might_contain_secrets(output_text):
        result = await Runner.run(leakage_detector_agent, output_text)
        detection: LeakageDetectorOutput = result.final_output

        if detection.has_leakage:
            return GuardrailFunctionOutput(
                tripwire_triggered=True,
                output_info={
                    "has_leakage": True,
                    "reasoning": detection.reasoning,
                    "leaked_type": detection.leaked_type,
                },
            )

    return GuardrailFunctionOutput(
        tripwire_triggered=False,
        output_info={"has_leakage": False, "reasoning": "Output appears safe"},
    )


def _might_contain_secrets(text: str) -> bool:
    """
    Heuristic check to determine if text might contain secrets.

    Returns True if text has characteristics that might indicate secrets:
    - Contains long alphanumeric strings
    - Contains key/token/secret keywords
    - Contains environment variable patterns
    """
    # Check for secret-like keywords
    secret_keywords = [
        "api_key",
        "apikey",
        "api-key",
        "secret",
        "token",
        "password",
        "credential",
        "bearer",
        "authorization",
        "private_key",
        "access_key",
        ".env",
        "environ",
    ]
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in secret_keywords):
        return True

    # Check for patterns that look like keys (long alphanumeric strings)
    long_strings = re.findall(r"[A-Za-z0-9_-]{32,}", text)
    if long_strings:
        return True

    # Check for assignment patterns
    if re.search(r"[A-Z_]+=\S+", text):
        return True

    return False
