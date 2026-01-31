"""
Regex patterns for security guardrails.

Contains patterns for detecting:
- Prompt injection attempts
- API key and secret leakage
"""

import re

# ==================== INJECTION DETECTION PATTERNS ====================

INJECTION_PATTERNS = [
    # Direct instruction override attempts
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?|guidelines?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?|guidelines?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?|guidelines?)",
    r"override\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?|guidelines?)",
    # System prompt extraction
    r"(show|print|display|reveal|tell|share|output|give)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions?|rules?|guidelines?)",
    r"what\s+(are|is)\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?|guidelines?)",
    r"repeat\s+(your|the)\s+(system\s+)?(prompt|instructions?|configuration)",
    # API key and secret extraction
    r"(show|print|display|reveal|tell|share|output|give)\s+(me\s+)?(the\s+)?(api\s*key|secret|token|password|credential)",
    r"what\s+(is|are)\s+(the\s+)?(api\s*key|secret|token|password|credential)",
    r"(access|read|show|print|display)\s+(the\s+)?\.env",
    r"(what|show|print).+(in|from|inside)\s+(the\s+)?\.env",
    r"environment\s+variable",
    r"OPENAI_API_KEY",
    r"ANTHROPIC_API_KEY",
    # Role/persona manipulation
    r"(you\s+are|act\s+as|pretend\s+to\s+be|roleplay\s+as)\s+(now\s+)?(a\s+)?(different|new|another)",
    r"(switch|change)\s+(to\s+)?(a\s+)?(new|different)\s+(mode|role|persona)",
    r"jailbreak",
    r"DAN\s+mode",
    # Delimiter/context manipulation
    r"<\/?system>",
    r"\[\/?INST\]",
    r"```(system|instructions?|prompt)",
    r"---\s*(system|instructions?|prompt)",
    # Code execution attempts
    r"(execute|run|eval)\s+(this\s+)?(code|script|command)",
    r"import\s+os|subprocess|exec\(",
]

# Compile patterns for efficiency
COMPILED_INJECTION_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS]


def check_injection_patterns(text: str) -> tuple[bool, str | None]:
    """
    Check text against injection patterns.

    Returns:
        Tuple of (is_injection, matched_pattern)
    """
    for i, pattern in enumerate(COMPILED_INJECTION_PATTERNS):
        if pattern.search(text):
            return True, INJECTION_PATTERNS[i]
    return False, None


# ==================== LEAKAGE DETECTION PATTERNS ====================

LEAKAGE_PATTERNS = [
    # OpenAI API keys
    r"sk-proj-[A-Za-z0-9_-]{20,}",
    r"sk-[A-Za-z0-9]{20,}",
    # Anthropic API keys
    r"sk-ant-[A-Za-z0-9_-]{20,}",
    # Google API keys
    r"AIzaSy[A-Za-z0-9_-]{33}",
    # Groq API keys
    r"gsk_[A-Za-z0-9]{20,}",
    # Generic API key patterns
    r"[A-Za-z0-9_]*(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[=:]\s*['\"]?[A-Za-z0-9_-]{20,}",
    # Bearer tokens
    r"Bearer\s+[A-Za-z0-9_.-]{20,}",
    r"Authorization:\s*(Bearer\s+)?[A-Za-z0-9_.-]{20,}",
    # Environment variable assignments
    r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|API_KEY|SECRET_KEY|ACCESS_TOKEN)\s*=\s*['\"]?[A-Za-z0-9_-]{10,}",
    # AWS keys
    r"AKIA[0-9A-Z]{16}",
    r"aws_secret_access_key\s*=\s*['\"]?[A-Za-z0-9/+=]{40}",
    # Database connection strings with credentials
    r"(postgres|mysql|mongodb)://[^:]+:[^@]+@",
    # JWT tokens (header.payload.signature)
    r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{20,}",
    # Private keys
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
]

# Compile patterns for efficiency
COMPILED_LEAKAGE_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in LEAKAGE_PATTERNS]


def check_leakage_patterns(text: str) -> tuple[bool, str | None]:
    """
    Check text against leakage patterns.

    Returns:
        Tuple of (has_leakage, matched_pattern)
    """
    for i, pattern in enumerate(COMPILED_LEAKAGE_PATTERNS):
        if pattern.search(text):
            return True, LEAKAGE_PATTERNS[i]
    return False, None
