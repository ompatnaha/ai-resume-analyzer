"""
templates/chat_page.py
AI Chat Assistant page — RAG-powered conversational interface with history.
"""

import streamlit as st
from utils.config import is_configured
from interview_engine.chat_assistant import (
    chat,
    append_to_history,
    get_suggested_questions,
)
from models.llm_client import get_llm_client


def render_chat(config: dict) -> None:
    """Render the AI Chat Assistant page."""
    st.markdown("## 💬 AI Interview Chat Assistant")

    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Upload your resume first so the assistant can reference it.")
        if st.button("← Upload Resume"):
            st.session_state["active_page"] = "🏠 Home"
            st.rerun()
        return

    if not is_configured(config):
        st.error("❌ Please configure your API key in the sidebar.")
        return

    # ── Top bar: clear history ────────────────────────────────────────────────
    top_col1, top_col2 = st.columns([4, 1])
    with top_col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()

    with top_col1:
        rag_status = (
            "🟢 Resume knowledge base active"
            if st.session_state.get("vector_store")
            else "🟡 No knowledge base — upload resume for best results"
        )
        st.markdown(
            f'<div class="rag-status">{rag_status}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Suggested starter questions ───────────────────────────────────────────
    if not st.session_state.get("chat_history"):
        st.markdown("**💡 Try asking:**")
        suggestions = get_suggested_questions(st.session_state.get("resume_text", ""))
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions[:6]):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                    _process_message(config, suggestion)
                    st.rerun()
        st.markdown("---")

    # ── Chat history display ──────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.get("chat_history", []):
            role    = message["role"]
            content = message["content"]

            if role == "user":
                st.markdown(
                    f"""
                    <div class="chat-message user-message">
                        <div class="chat-avatar">👤</div>
                        <div class="chat-bubble user-bubble">{content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="chat-message assistant-message">
                        <div class="chat-avatar">🎯</div>
                        <div class="chat-bubble assistant-bubble">{content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Input area ────────────────────────────────────────────────────────────
    st.markdown("---")
    input_col, send_col = st.columns([6, 1])

    with input_col:
        user_input = st.text_input(
            "Ask anything about your resume or interview preparation…",
            key="chat_input",
            placeholder="e.g. What are my strongest skills? Give me mock interview questions.",
            label_visibility="collapsed",
        )

    with send_col:
        send = st.button("Send ➤", use_container_width=True, type="primary")

    if send and user_input.strip():
        _process_message(config, user_input.strip())
        st.rerun()

    # ── Chat statistics ───────────────────────────────────────────────────────
    history = st.session_state.get("chat_history", [])
    if history:
        num_turns = len([m for m in history if m["role"] == "user"])
        st.caption(f"💬 {num_turns} message{'s' if num_turns != 1 else ''} in this session")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _process_message(config: dict, user_input: str) -> None:
    """Process a user message: invoke LLM and update chat history."""
    try:
        llm = get_llm_client(config)
    except Exception as exc:
        st.error(f"LLM init failed: {exc}")
        return

    # Append user message to history
    st.session_state["chat_history"] = append_to_history(
        st.session_state.get("chat_history", []),
        "user",
        user_input,
    )

    # Get assistant response
    with st.spinner("🤖 Thinking…"):
        response = chat(
            llm=llm,
            user_message=user_input,
            retriever=st.session_state.get("vector_store"),
            chat_history=st.session_state.get("chat_history", []),
            stream=False,
        )

    # Append assistant response
    st.session_state["chat_history"] = append_to_history(
        st.session_state.get("chat_history", []),
        "assistant",
        response or "I'm sorry, I couldn't generate a response.",
    )
