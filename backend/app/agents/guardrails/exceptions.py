"""
Safe error messages for security guardrails.

These messages are designed to be informative to the user while
not revealing details about the security checks or internal workings.
"""

SAFE_INJECTION_MESSAGE = (
    "Unable to process this request. Please provide a valid company name and role."
)

SAFE_LEAKAGE_MESSAGE = (
    "Research completed but results could not be displayed. Please try again."
)
