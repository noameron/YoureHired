"""
Pydantic models for security guardrail outputs.
"""

from pydantic import BaseModel


class InjectionDetectorOutput(BaseModel):
    """Output schema for the injection detection LLM agent."""

    is_injection: bool
    reasoning: str
    matched_pattern: str | None = None


class LeakageDetectorOutput(BaseModel):
    """Output schema for the leakage detection LLM agent."""

    has_leakage: bool
    reasoning: str
    leaked_type: str | None = None
