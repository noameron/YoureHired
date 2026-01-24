"""
Security guardrails for company research agents.

This module provides input and output guardrails to protect against:
- Prompt injection attacks
- API key and secret leakage
"""

from app.agents.guardrails.exceptions import (
    SAFE_INJECTION_MESSAGE,
    SAFE_LEAKAGE_MESSAGE,
)
from app.agents.guardrails.injection_detector import injection_guardrail
from app.agents.guardrails.leakage_detector import leakage_guardrail
from app.agents.guardrails.patterns import (
    check_injection_patterns,
    check_leakage_patterns,
)
from app.agents.guardrails.prompts import SECURITY_RULES

__all__ = [
    "SECURITY_RULES",
    "injection_guardrail",
    "leakage_guardrail",
    "SAFE_INJECTION_MESSAGE",
    "SAFE_LEAKAGE_MESSAGE",
    "check_injection_patterns",
    "check_leakage_patterns",
]
