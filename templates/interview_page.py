"""
templates/interview_page.py
Interview Preparation page — HR, technical, project, and situational questions.
"""

import streamlit as st
from utils.config import is_configured
from interview_engine.question_generator import (
    generate_hr_questions,
    generate_technical_questions,
    generate_project_questions,
    generate_situational_questions,
)
from models.llm_client import get_llm_client


def render_interview(config: dict) -> None:
    """Render the Interview Preparation page."""
    st.markdown("## 🎤 Interview Preparation")

    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Please upload your resume on the Home page first.")
        if st.button("← Go to Home"):
            st.session_state["active_page"] = "🏠 Home"
            st.rerun()
        return

    if not is_configured(config):
        st.error("❌ No API key configured.")
        return

    resume_text = st.session_state["resume_text"]

    # ── Configuration bar ─────────────────────────────────────────────────────
    st.markdown("### ⚙️ Configuration")
    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)

    with cfg_col1:
        job_role = st.text_input(
            "Target Job Role",
            value="Software Engineer",
            placeholder="e.g. Data Scientist, Backend Engineer",
        )

    with cfg_col2:
        q_count = st.slider("Questions per category", min_value=3, max_value=12, value=6)

    with cfg_col3:
        categories = st.multiselect(
            "Select Categories",
            ["HR / Behavioral", "Technical", "Project-Based", "Situational (STAR)"],
            default=["HR / Behavioral", "Technical", "Project-Based", "Situational (STAR)"],
        )

    st.markdown("---")

    # ── Generate button ───────────────────────────────────────────────────────
    gen_col, _ = st.columns([2, 3])
    with gen_col:
        generate = st.button(
            "⚡ Generate Interview Questions",
            use_container_width=True,
            type="primary",
        )

    if generate:
        _generate_questions(config, resume_text, job_role, q_count, categories)

    # ── Display stored questions ──────────────────────────────────────────────
    _render_questions(categories)


# ── Generator ─────────────────────────────────────────────────────────────────

def _generate_questions(config, resume_text, job_role, count, categories):
    """Call generators for selected categories and store in session state."""
    try:
        llm = get_llm_client(config)
    except Exception as exc:
        st.error(f"Failed to initialise LLM: {exc}")
        return

    progress = st.progress(0, text="Generating questions…")
    step = 1 / max(len(categories), 1)

    for i, cat in enumerate(categories):
        progress.progress(step * i, text=f"Generating {cat} questions…")

        if cat == "HR / Behavioral":
            with st.spinner("Generating HR questions…"):
                st.session_state["hr_questions"] = generate_hr_questions(
                    llm, resume_text, job_role, count
                )

        elif cat == "Technical":
            with st.spinner("Generating Technical questions…"):
                st.session_state["technical_questions"] = generate_technical_questions(
                    llm, resume_text, job_role, count
                )

        elif cat == "Project-Based":
            with st.spinner("Generating Project questions…"):
                st.session_state["project_questions"] = generate_project_questions(
                    llm, resume_text, job_role, count
                )

        elif cat == "Situational (STAR)":
            with st.spinner("Generating Situational questions…"):
                st.session_state["behavioral_questions"] = generate_situational_questions(
                    llm, resume_text, job_role, count
                )

    progress.progress(1.0, text="Done!")
    st.success("✅ Interview questions generated!")


# ── Renderer ──────────────────────────────────────────────────────────────────

def _render_questions(categories: list[str]) -> None:
    """Render generated questions in expandable cards with difficulty badges."""

    tab_labels = [c for c in [
        "HR / Behavioral",
        "Technical",
        "Project-Based",
        "Situational (STAR)",
    ] if c in categories]

    if not tab_labels:
        return

    session_map = {
        "HR / Behavioral":     "hr_questions",
        "Technical":           "technical_questions",
        "Project-Based":       "project_questions",
        "Situational (STAR)":  "behavioral_questions",
    }

    category_icons = {
        "HR / Behavioral":    "👥",
        "Technical":          "⚙️",
        "Project-Based":      "🏗️",
        "Situational (STAR)": "🎭",
    }

    tabs = st.tabs([f"{category_icons.get(t,'')} {t}" for t in tab_labels])

    for tab, label in zip(tabs, tab_labels):
        with tab:
            key = session_map[label]
            questions = st.session_state.get(key, [])

            if not questions:
                st.info(f"Click 'Generate' to create {label} questions.")
                continue

            st.markdown(f"**{len(questions)} questions generated**")

            # Download as markdown
            md_content = _questions_to_markdown(label, questions)
            st.download_button(
                f"⬇️ Download {label} Questions",
                data=md_content,
                file_name=f"{label.lower().replace('/', '_').replace(' ', '_')}_questions.md",
                mime="text/markdown",
                key=f"dl_{key}",
            )

            st.markdown("---")

            for i, q in enumerate(questions, 1):
                if not isinstance(q, dict):
                    continue

                difficulty = q.get("difficulty", "Medium")
                diff_color = {
                    "Easy":   "diff-easy",
                    "Medium": "diff-medium",
                    "Hard":   "diff-hard",
                }.get(difficulty, "diff-medium")

                with st.expander(
                    f"Q{i}: {q.get('question', 'Question')[:90]}…"
                    if len(q.get('question', '')) > 90
                    else f"Q{i}: {q.get('question', 'Question')}",
                    expanded=i <= 2,
                ):
                    st.markdown(
                        f'<span class="difficulty-badge {diff_color}">{difficulty}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Q:** {q.get('question', '')}")

                    if q.get("tip"):
                        st.markdown("---")
                        st.markdown(f"💡 **Interviewer Tip:** _{q['tip']}_")


def _questions_to_markdown(category: str, questions: list[dict]) -> str:
    """Convert question list to downloadable markdown."""
    lines = [f"# {category} Interview Questions\n"]
    for i, q in enumerate(questions, 1):
        lines.append(f"## Q{i}: {q.get('question', '')}")
        lines.append(f"- **Difficulty:** {q.get('difficulty', 'Medium')}")
        if q.get("tip"):
            lines.append(f"- **Tip:** {q['tip']}")
        lines.append("")
    return "\n".join(lines)
