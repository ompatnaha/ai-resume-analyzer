"""
utils/config.py
Loads configuration from environment variables / .env file.
Validates required API keys and returns a config dict used app-wide.
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load .env if it exists (local development)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def load_config() -> dict:
    """
    Read environment variables and build the application config.

    Returns:
        dict: Configuration dictionary with API keys and settings.
    """
    config = {
        # ── LLM Provider ────────────────────────────────────────────────────
        "llm_provider":    os.getenv("LLM_PROVIDER", "gemini").lower(),
        "gemini_api_key":  os.getenv("GEMINI_API_KEY", ""),
        "openai_api_key":  os.getenv("OPENAI_API_KEY", ""),

        # ── Model names ─────────────────────────────────────────────────────
        "gemini_model":    os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "openai_model":    os.getenv("OPENAI_MODEL", "gpt-4o-mini"),

        # ── Embedding model ─────────────────────────────────────────────────
        "embedding_model": os.getenv(
            "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
        ),

        # ── Vector store ────────────────────────────────────────────────────
        "vector_store":    os.getenv("VECTOR_STORE", "faiss"),  # faiss | chroma

        # ── Misc ────────────────────────────────────────────────────────────
        "max_tokens":      int(os.getenv("MAX_TOKENS", "2048")),
        "temperature":     float(os.getenv("TEMPERATURE", "0.7")),
        "debug":           os.getenv("DEBUG", "false").lower() == "true",
    }

    # ── Sidebar API key override (for demo / hosted deployments) ────────────
    if not config["gemini_api_key"] and not config["openai_api_key"]:
        _show_api_key_input(config)

    return config


def _show_api_key_input(config: dict) -> None:
    """
    If no API key is set via env vars, render a sidebar input
    so the user can paste one in at runtime.
    """
    with st.sidebar:
        st.warning("⚠️ No API key detected in environment.")
        provider = st.selectbox(
            "Select LLM Provider",
            ["gemini", "openai"],
            key="_provider_select",
        )
        config["llm_provider"] = provider

        if provider == "gemini":
            key = st.text_input(
                "Gemini API Key",
                type="password",
                key="_gemini_key_input",
                placeholder="AIza...",
            )
            config["gemini_api_key"] = key
        else:
            key = st.text_input(
                "OpenAI API Key",
                type="password",
                key="_openai_key_input",
                placeholder="sk-...",
            )
            config["openai_api_key"] = key


def get_active_api_key(config: dict) -> str:
    """Return the active API key based on the selected provider."""
    if config["llm_provider"] == "gemini":
        return config["gemini_api_key"]
    return config["openai_api_key"]


def is_configured(config: dict) -> bool:
    """Return True if the active provider has a non-empty API key."""
    return bool(get_active_api_key(config))
