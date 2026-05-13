"""
utils/session_state.py
Centralised Streamlit session-state initialisation.
Call init_session_state() once at app startup.
"""

import streamlit as st


def init_session_state() -> None:
    """
    Initialise all session-state keys with sensible defaults.
    Idempotent — safe to call on every rerun.
    """
    defaults = {
        # ── Uploaded resume data ────────────────────────────────────────────
        "resume_text":         None,   # raw extracted text
        "resume_filename":     None,   # original PDF filename
        "resume_chunks":       None,   # chunked text for RAG

        # ── Analysis results ────────────────────────────────────────────────
        "analysis_result":     None,   # full analysis dict
        "ats_score":           None,   # 0-100 integer
        "skills_found":        [],     # list of detected skills
        "missing_skills":      [],     # skills in JD but not in resume
        "improvement_tips":    [],     # list of suggestion strings

        # ── Job description ─────────────────────────────────────────────────
        "job_description":     "",
        "jd_skills":           [],

        # ── Interview questions ─────────────────────────────────────────────
        "hr_questions":        [],
        "technical_questions": [],
        "project_questions":   [],
        "behavioral_questions":[],

        # ── Chat history ────────────────────────────────────────────────────
        "chat_history":        [],     # list of {"role": ..., "content": ...}
        "vector_store":        None,   # FAISS / Chroma index

        # ── Career suggestions ───────────────────────────────────────────────
        "career_suggestions":  None,

        # ── UI state ────────────────────────────────────────────────────────
        "active_page":         "🏠 Home",
        "analysis_done":       False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
