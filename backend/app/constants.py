"""Shared constants for the application."""

# SSE (Server-Sent Events) response headers
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# Maximum length for solution text before truncation
MAX_SOLUTION_LENGTH = 10000
