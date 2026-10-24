"""Provider-selection helpers for the LangChain MCP client."""

from __future__ import annotations
import os
from dotenv import load_dotenv

class  MissingApiKeyError(RuntimeError):
    """Raised when an API key is missing."""

def get_model_identifier() -> str:
    """Return a LangChain model identifier string.

    Params:
        None

    Returns:
        Provider-prefixed model identifier accepted by LangChain create_agent.

    Raises:
        MissingApiKeyError: If the selected provider lacks an API key.
        ValueError: If MODEL_PROVIDER is unsupported.
    """
    provider = os.getenv("MODEL_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise MissingApiKeyError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai.")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return f"openai:{model_name}"
    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise MissingApiKeyError("ANTHROPIC_API_KEY is required when MODEL_PROVIDER=anthropic.")
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        return f"anthropic:{model_name}"
    if provider in {"google", "gemini", "google_genai"}:
        if not os.getenv("GOOGLE_API_KEY"):
            raise MissingApiKeyError("GOOGLE_API_KEY is required when MODEL_PROVIDER=google.")
        model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
        return f"google_genai:{model_name}"

    raise ValueError("MODEL_PROVIDER must be one of: openai, anthropic, google.")


        



        