def sanitize_input(text: str, max_length: int = 8000) -> str:
    """Normalize and sanitize user input before LLM usage.

    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length (default: 8000)

    Returns:
        Sanitized text with normalized whitespace and enforced length limit
    """
    # Normalize whitespace (replace tabs, newlines, multiple spaces with single space)
    text = " ".join(text.split())
    # Enforce length limit
    text = text[:max_length]
    return text
