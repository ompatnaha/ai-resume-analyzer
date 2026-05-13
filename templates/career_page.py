"""
templates/career_page.py
Career Advisor page — personalised role recommendations, learning roadmap,
industry fit, and salary guidance.
"""

import streamlit as st
from utils.config import is_configured
from interview_engine.question_generator import generate_career_suggestions
from models.llm_client import get_llm_client


def render_career(config: dict) -> None:
    """Render the Career Advisor page."""
    st.markdown("## 🚀 Career Advisor")
    st.markdown(
        "_Personalised career development plan based on your resume._"
    )

    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Please upload your resume on the Home page first.")
        if st.button("← Go to Home"):
            st.session_state["active_page"] = "🏠 Home"
            st.rerun()
        return

    if not is_configured(config):
        st.error("❌ Please configure your API key in the sidebar.")
        return

    # ── Generate button ───────────────────────────────────────────────────────
    gen_col, _ = st.columns([2, 3])
    with gen_col:
        generate = st.button(
            "🔮 Generate Career Plan",
            use_container_width=True,
            type="primary",
        )

    if generate:
        with st.spinner("🤖 Crafting your personalised career plan…"):
            try:
                llm = get_llm_client(config)
                suggestions = generate_career_suggestions(
                    llm,
                    st.session_state["resume_text"],
                )
                st.session_state["career_suggestions"] = suggestions
            except Exception as exc:
                st.error(f"Career plan generation failed: {exc}")
                return

    # ── Render stored plan ────────────────────────────────────────────────────
    data = st.session_state.get("career_suggestions")
    if not data:
        st.info("Click **Generate Career Plan** to get your personalised report.")
        return

    if "error" in data:
        st.error(f"Error: {data['error']}")
        if data.get("raw"):
            st.text_area("Raw response", data["raw"], height=200)
        return

    # ── Current level badge ───────────────────────────────────────────────────
    level = data.get("current_level", "Unknown")
    st.markdown(
        f"""
        <div class="level-badge">
            <span class="level-label">Current Level Assessment</span>
            <span class="level-value">{level}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Recommended roles ─────────────────────────────────────────────────────
    st.markdown("### 💼 Recommended Roles")
    roles = data.get("recommended_roles", [])
    if roles:
        for role in roles:
            if not isinstance(role, dict):
                continue
            with st.expander(
                f"🎯 {role.get('title', 'Role')} "
                f"— {role.get('salary_range', '')}",
                expanded=True,
            ):
                st.markdown(f"**Why it fits:** {role.get('reason', '')}")
                if role.get("salary_range"):
                    st.markdown(f"💰 **Salary Range:** {role['salary_range']}")
    else:
        st.info("No role recommendations available.")

    st.markdown("---")

    # ── Two-column layout: Skill Gaps + Industries ────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown("### 🛠️ Skill Gaps to Address")
        gaps = data.get("skill_gaps", [])
        if gaps:
            for gap in gaps:
                st.markdown(
                    f'<span class="skill-chip skill-missing">{gap}</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("No critical skill gaps identified!")

    with right:
        st.markdown("### 🏭 Best-Fit Industries")
        industries = data.get("industry_suggestions", [])
        if industries:
            for ind in industries:
                st.markdown(
                    f'<span class="skill-chip skill-found">{ind}</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No industry suggestions available.")

    st.markdown("---")

    # ── Learning roadmap ──────────────────────────────────────────────────────
    st.markdown("### 📅 Learning Roadmap")
    roadmap = data.get("learning_roadmap", [])
    if roadmap:
        cols = st.columns(min(len(roadmap), 4))
        for col, milestone in zip(cols, roadmap):
            if not isinstance(milestone, dict):
                continue
            with col:
                st.markdown(
                    f"""
                    <div class="roadmap-card">
                        <div class="roadmap-month">{milestone.get('month', '')}</div>
                        <div class="roadmap-focus">{milestone.get('focus', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No learning roadmap generated.")

    st.markdown("---")

    # ── Personalised advice ───────────────────────────────────────────────────
    advice = data.get("career_advice", "")
    if advice:
        st.markdown("### 💡 Personalised Career Advice")
        st.info(advice)

    # ── Download career report ────────────────────────────────────────────────
    report_md = _build_career_report(data)
    st.download_button(
        "⬇️ Download Career Report",
        data=report_md,
        file_name="career_plan.md",
        mime="text/markdown",
    )


def _build_career_report(data: dict) -> str:
    """Build a downloadable markdown career report."""
    lines = ["# 🚀 Career Development Plan\n"]

    lines.append(f"## Current Level\n{data.get('current_level', 'Unknown')}\n")

    lines.append("## Recommended Roles")
    for role in data.get("recommended_roles", []):
        lines.append(f"### {role.get('title', '')}")
        lines.append(f"- **Why it fits:** {role.get('reason', '')}")
        lines.append(f"- **Salary:** {role.get('salary_range', 'N/A')}\n")

    lines.append("## Skill Gaps")
    for gap in data.get("skill_gaps", []):
        lines.append(f"- {gap}")
    lines.append("")

    lines.append("## Industries")
    for ind in data.get("industry_suggestions", []):
        lines.append(f"- {ind}")
    lines.append("")

    lines.append("## Learning Roadmap")
    for m in data.get("learning_roadmap", []):
        lines.append(f"**{m.get('month', '')}:** {m.get('focus', '')}")
    lines.append("")

    if data.get("career_advice"):
        lines.append(f"## Career Advice\n{data['career_advice']}\n")

    return "\n".join(lines)
