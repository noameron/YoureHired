import os
from unittest.mock import patch

from app.config import Settings
from app.model_config import resolve_model


def test_resolve_model_openai_when_key_set():
    # GIVEN an OpenAI API key is configured
    mock_settings = Settings(openai_api_key="sk-test-key", openai_model="gpt-4o-mini")

    # WHEN resolve_model is called
    with patch("app.model_config.settings", mock_settings):
        model, supports_web_search = resolve_model()

    # THEN it returns the OpenAI model with web search support
    assert model == "gpt-4o-mini"
    assert supports_web_search is True


def test_resolve_model_gemini_fallback_when_no_openai_key():
    # GIVEN no OpenAI API key is set
    mock_settings = Settings(openai_api_key="", gemini_model="litellm/gemini/gemini-2.5-flash")

    # WHEN resolve_model is called
    with patch("app.model_config.settings", mock_settings):
        model, supports_web_search = resolve_model()

    # THEN it falls back to Gemini without web search
    assert model == "litellm/gemini/gemini-2.5-flash"
    assert supports_web_search is False


def test_resolve_model_sets_google_api_key_env(monkeypatch):
    # GIVEN no GOOGLE_API_KEY in environment and a Google API key in settings
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    mock_settings = Settings(openai_api_key="", google_api_key="test-google-key")

    # WHEN resolve_model is called
    with patch("app.model_config.settings", mock_settings):
        resolve_model()

    # THEN GOOGLE_API_KEY is set in the environment
    assert os.environ.get("GOOGLE_API_KEY") == "test-google-key"


def test_resolve_model_respects_custom_openai_model():
    # GIVEN a custom OpenAI model is configured
    mock_settings = Settings(openai_api_key="sk-test", openai_model="gpt-4o")

    # WHEN resolve_model is called
    with patch("app.model_config.settings", mock_settings):
        model, _ = resolve_model()

    # THEN it uses the custom model name
    assert model == "gpt-4o"


def test_resolve_model_respects_custom_gemini_model():
    # GIVEN a custom Gemini model is configured with no OpenAI key
    mock_settings = Settings(openai_api_key="", gemini_model="litellm/gemini/gemini-pro")

    # WHEN resolve_model is called
    with patch("app.model_config.settings", mock_settings):
        model, _ = resolve_model()

    # THEN it uses the custom Gemini model name
    assert model == "litellm/gemini/gemini-pro"
