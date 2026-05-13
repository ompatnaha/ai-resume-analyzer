"""
utils/helpers.py
Miscellaneous helper functions used across the application.
"""

import re
import json
import streamlit as st
from typing import Any


def clean_text(text: str) -> str:
    """
    Normalise extracted PDF text:
    - Collapse excessive whitespace
    - Remove non-printable control characters
    - Preserve paragraph breaks (double newline)
    """
    # Remove control characters except newlines and tabs
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", text)
    # Collapse runs of spaces/tabs (but not newlines)
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ consecutive newlines → 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks suitable for embedding / RAG.

    Args:
        text:       Full document text.
        chunk_size: Target characters per chunk.
        overlap:    Character overlap between adjacent chunks.

    Returns:
        List of text chunk strings.
    """
    words = text.split()
    chunks, current, current_len = [], [], 0

    for word in words:
        word_len = len(word) + 1  # +1 for space
        if current_len + word_len > chunk_size and current:
            chunks.append(" ".join(current))
            # Keep overlap words
            overlap_words = current[-max(1, overlap // 6):]
            current = overlap_words
            current_len = sum(len(w) + 1 for w in current)
        current.append(word)
        current_len += word_len

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if len(c.strip()) > 20]


def parse_json_response(text: str) -> Any:
    """
    Safely extract and parse a JSON object from an LLM response string.
    Handles markdown code fences and stray surrounding text.

    Returns parsed object or None on failure.
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract first {...} or [...] block
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    return None


def score_color(score: int) -> str:
    """Return a CSS colour class name based on an ATS score (0-100)."""
    if score >= 80:
        return "score-excellent"
    if score >= 60:
        return "score-good"
    if score >= 40:
        return "score-fair"
    return "score-poor"


def score_label(score: int) -> str:
    """Human-readable label for an ATS score."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Needs Work"


def display_metric_card(label: str, value: Any, delta: str = "") -> None:
    """Render a styled metric card using st.metric."""
    st.metric(label=label, value=value, delta=delta or None)


def show_spinner_message(msg: str) -> st.spinner:
    """Return a spinner context manager with a custom message."""
    return st.spinner(msg)


def format_bullet_list(items: list[str]) -> str:
    """Convert a Python list to a markdown bullet list string."""
    return "\n".join(f"- {item}" for item in items)


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text with ellipsis if it exceeds max_len characters."""
    return text if len(text) <= max_len else text[:max_len].rstrip() + "…"
