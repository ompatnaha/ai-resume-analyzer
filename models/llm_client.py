"""
models/llm_client.py
LangChain-based LLM client wrapper supporting Gemini and OpenAI.

Provides a unified interface regardless of the selected provider.
All prompts are built externally; this module handles client init,
retry logic, and response normalisation.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_llm_client(config: dict):
    """
    Instantiate and return a LangChain LLM client based on config.

    Args:
        config: Application config dict (from utils/config.py).

    Returns:
        A LangChain BaseChatModel instance (ChatGoogleGenerativeAI or ChatOpenAI).

    Raises:
        ValueError: If provider is unsupported or API key is missing.
        ImportError: If required package is not installed.
    """
    provider = config.get("llm_provider", "gemini").lower()

    if provider == "gemini":
        return _get_gemini_client(config)
    if provider == "openai":
        return _get_openai_client(config)

    raise ValueError(f"Unsupported LLM provider: '{provider}'. Use 'gemini' or 'openai'.")


def _get_gemini_client(config: dict):
    """Build a ChatGoogleGenerativeAI client."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise ImportError(
            "langchain-google-genai is not installed. "
            "Run: pip install langchain-google-genai"
        ) from exc

    api_key = config.get("gemini_api_key", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Cannot create Gemini client.")

    return ChatGoogleGenerativeAI(
        model=config.get("gemini_model", "gemini-1.5-flash"),
        google_api_key=api_key,
        temperature=config.get("temperature", 0.7),
        max_output_tokens=config.get("max_tokens", 2048),
        convert_system_message_to_human=True,   # Gemini requires this
    )


def _get_openai_client(config: dict):
    """Build a ChatOpenAI client."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise ImportError(
            "langchain-openai is not installed. "
            "Run: pip install langchain-openai"
        ) from exc

    api_key = config.get("openai_api_key", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Cannot create OpenAI client.")

    return ChatOpenAI(
        model=config.get("openai_model", "gpt-4o-mini"),
        openai_api_key=api_key,
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 2048),
    )


def invoke_llm(llm, prompt: str) -> Optional[str]:
    """
    Invoke an LLM client with a plain string prompt.

    Handles both ChatModel (returns AIMessage) and plain LLM types.

    Args:
        llm:    LangChain LLM / chat model instance.
        prompt: String prompt to send.

    Returns:
        Response text string, or None on error.
    """
    try:
        response = llm.invoke(prompt)
        # ChatModel returns AIMessage with .content attribute
        if hasattr(response, "content"):
            return response.content
        # Plain LLM returns string directly
        return str(response)
    except Exception as exc:
        logger.error("LLM invocation failed: %s", exc)
        return None


def stream_llm(llm, prompt: str):
    """
    Generator that streams tokens from the LLM.

    Args:
        llm:    LangChain chat model instance.
        prompt: String prompt.

    Yields:
        Text chunks (str).
    """
    try:
        for chunk in llm.stream(prompt):
            if hasattr(chunk, "content"):
                yield chunk.content
            else:
                yield str(chunk)
    except Exception as exc:
        logger.error("LLM streaming failed: %s", exc)
        yield f"\n⚠️ Streaming error: {exc}"
