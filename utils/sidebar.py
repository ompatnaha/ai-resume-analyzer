"""
utils/sidebar.py
Renders the Streamlit sidebar: logo, navigation, resume status indicator.
"""

import streamlit as st
from utils.config import is_configured


def render_sidebar(config: dict) -> str:
    """
    Render the sidebar and return the name of the selected page.

    Args:
        config: Application configuration dict.

    Returns:
        str: Selected page name.
    """
    with st.sidebar:
        # ── Branding ────────────────────────────────────────────────────────
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="brand-icon">🎯</div>
                <div class="brand-text">
                    <span class="brand-title">ResumeAI</span>
                    <span class="brand-sub">Pro</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── API status badge ─────────────────────────────────────────────────
        if is_configured(config):
            provider = config["llm_provider"].capitalize()
            st.markdown(
                f'<div class="status-badge status-ok">✅ {provider} connected</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-badge status-warn">⚠️ No API key set</div>',
                unsafe_allow_html=True,
            )

        # ── Resume status ────────────────────────────────────────────────────
        if st.session_state.get("resume_text"):
            fname = st.session_state.get("resume_filename", "resume.pdf")
            st.markdown(
                f'<div class="status-badge status-ok">📄 {fname[:28]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-badge status-warn">📄 No resume uploaded</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ── Navigation ───────────────────────────────────────────────────────
        pages = [
            "🏠 Home",
            "📄 Resume Analysis",
            "🎤 Interview Prep",
            "💬 AI Chat Assistant",
            "🚀 Career Advisor",
        ]

        selected = st.radio(
            "Navigation",
            pages,
            index=pages.index(st.session_state.get("active_page", "🏠 Home")),
            key="nav_radio",
            label_visibility="collapsed",
        )
        st.session_state["active_page"] = selected

        st.markdown("---")

        # ── Quick reset button ───────────────────────────────────────────────
        if st.button("🔄 Reset Session", use_container_width=True):
            keys_to_clear = [
                "resume_text", "resume_filename", "resume_chunks",
                "analysis_result", "ats_score", "skills_found",
                "missing_skills", "improvement_tips", "job_description",
                "jd_skills", "hr_questions", "technical_questions",
                "project_questions", "behavioral_questions",
                "chat_history", "vector_store", "career_suggestions",
                "analysis_done",
            ]
            for k in keys_to_clear:
                st.session_state[k] = None if k not in (
                    "skills_found", "missing_skills", "improvement_tips",
                    "jd_skills", "hr_questions", "technical_questions",
                    "project_questions", "behavioral_questions", "chat_history"
                ) else []
            st.session_state["analysis_done"] = False
            st.rerun()

        # ── Footer ───────────────────────────────────────────────────────────
        st.markdown(
            """
            <div class="sidebar-footer">
                Built with ❤️ using LangChain + Gemini<br>
                <small>v1.0.0</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected
