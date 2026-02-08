"""Central model configuration for all agents.

Resolves which LLM model to use based on available API keys:
- If OPENAI_API_KEY is set → use settings.openai_model (default: gpt-4o-mini)
- If not → use settings.gemini_model (default: litellm/gemini/gemini-2.5-flash)
"""

import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)


def resolve_model() -> tuple[str, bool]:
    """Resolve the default model and capabilities based on available API keys.

    Side effects:
        Sets GOOGLE_API_KEY environment variable when falling back to Gemini.

    Returns:
        A tuple of (model_name, supports_web_search).
    """
    if settings.openai_api_key:
        logger.info("Using OpenAI model: %s", settings.openai_model)
        return settings.openai_model, True

    if settings.google_api_key:
        os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)

    logger.info("OPENAI_API_KEY not set — falling back to Gemini model: %s", settings.gemini_model)
    return settings.gemini_model, False


DEFAULT_MODEL, SUPPORTS_WEB_SEARCH = resolve_model()
