import os

from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

# Default model and LLM endpoint configuration (can be overridden by .env)
MODEL_NAME: str = os.getenv("MODEL_NAME", "openai-responses:o4-mini")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:8011/v1")
LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
USE_RATE_LIMITER: bool = (LLM_API_KEY or "no-key-required") != "no-key-required"


def get_model() -> str | OpenAIResponsesModel:
    """Get the configured model, using a local OpenAI-compatible endpoint if
    ``LLM_BASE_URL`` is set (default: ``http://localhost:8011/v1``).

    Returns a model **instance** (with a custom provider) when
    ``LLM_BASE_URL`` is non-empty, otherwise returns the plain model name
    string for pydantic-ai's default resolution.
    """
    if LLM_BASE_URL:
        return OpenAIResponsesModel(
            MODEL_NAME or "openai-responses:o4-mini",
            provider=OpenAIProvider(
                base_url=LLM_BASE_URL,
                api_key=LLM_API_KEY or "no-key-required",
            ),
        )
    return MODEL_NAME
