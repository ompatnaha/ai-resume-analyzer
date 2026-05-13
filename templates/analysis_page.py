"""
templates/analysis_page.py
Resume Analysis page — ATS score, skills, JD comparison, suggestions.
"""

import streamlit as st
from utils.config import is_configured
from utils.helpers import score_color, score_label
from resume_parser.skill_extractor import (
    extract_resume_info,
    get_missing_skills,
    extract_skills,
)
from resume_parser.ats_scorer_v2 import calculate_ats_score
from interview_engine.resume_analyzer import (
    analyse_resume,
    get_improvement_suggestions,
    compare_with_jd,
)
from models.llm_client import get_llm_client


def render_analysis(config: dict) -> None:
    """Render the Resume Analysis page."""

    st.markdown("## 📄 Resume Analysis")

    # ── Guard: resume required ────────────────────────────────────────────────
    if not st.session_state.get("resume_text"):
        st.warning("⚠️ Please upload a resume on the Home page first.")
        if st.button("← Go to Home"):
            st.session_state["active_page"] = "🏠 Home"
            st.rerun()
        return

    if not is_configured(config):
        st.error("❌ No API key configured. Please add it in the sidebar.")
        return

    resume_text = st.session_state["resume_text"]
    jd_text     = st.session_state.get("job_description", "")
    if resume_text and jd_text:

        ats_result = calculate_ats_score(
            resume_text,
            jd_text
    )

    st.subheader("📊 ATS Score")

    st.metric(
        "ATS Match Score",
        f"{ats_result['ATS Score']}%"
    )

    st.write("### ✅ Matching Skills")
    st.write(ats_result["Matching Skills"])

    st.write("### ❌ Missing Skills")
    st.write(ats_result["Missing Skills"])

    st.write("### 💡 Suggestions")
    st.write(ats_result["Suggestions"])
    
    # ── Run analysis button ───────────────────────────────────────────────────
    run_col, _ = st.columns([2, 3])
    with run_col:
        run_analysis = st.button(
            "🔍 Run Full Analysis",
            use_container_width=True,
            type="primary",
        )

    if run_analysis or st.session_state.get("analysis_done"):
        if run_analysis:
            _run_and_store_analysis(config, resume_text, jd_text)

        if st.session_state.get("ats_score") is not None:
            _render_results(jd_text)
    else:
        st.info("Click **Run Full Analysis** to generate insights.")


# ── Analysis runner ───────────────────────────────────────────────────────────

def _run_and_store_analysis(config, resume_text, jd_text):
    """Run all analysis steps and persist results in session state."""
    try:
        llm = get_llm_client(config)
    except Exception as exc:
        st.error(f"Failed to initialise LLM: {exc}")
        return

    # 1. NLP extraction (fast, local)
    with st.spinner("🔬 Extracting skills and information…"):
        info = extract_resume_info(resume_text)
        st.session_state["skills_found"] = info["skills"]

        if jd_text:
            jd_skills = extract_skills(jd_text.lower())
            st.session_state["jd_skills"]      = jd_skills
            st.session_state["missing_skills"] = get_missing_skills(
                info["skills"], jd_skills
            )

    # 2. ATS score (fast, local)
    with st.spinner("📊 Calculating ATS score…"):
        ats_result = calculate_ats_score(resume_text, jd_text)
        st.session_state["ats_score"]   = ats_result["total_score"]
        st.session_state["ats_details"] = ats_result

    # 3. LLM deep analysis
    with st.spinner("🤖 Running AI analysis (this may take 15-30s)…"):
        analysis = analyse_resume(llm, resume_text, jd_text)
        st.session_state["analysis_result"] = analysis

        suggestions = get_improvement_suggestions(llm, resume_text)
        st.session_state["improvement_tips"] = suggestions

    st.session_state["analysis_done"] = True
    st.success("✅ Analysis complete!")


# ── Results renderer ──────────────────────────────────────────────────────────

def _render_results(jd_text: str) -> None:
    """Render all analysis result sections."""
    score   = st.session_state.get("ats_score", 0)
    details = st.session_state.get("ats_details", {})
    analysis = st.session_state.get("analysis_result", {})

    # ── ATS Score hero ────────────────────────────────────────────────────────
    st.markdown("### 📊 ATS Score")
    s_col, g_col, e_col = st.columns(3)

    with s_col:
        color_class = score_color(score)
        st.markdown(
            f"""
            <div class="score-hero {color_class}">
                <div class="score-number">{score}</div>
                <div class="score-label">/ 100</div>
                <div class="score-grade">{details.get('grade', 'N/A')}</div>
                <div class="score-sublabel">{score_label(score)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with g_col:
        if details.get("breakdown"):
            st.markdown("**Score Breakdown**")
            for factor, pts in details["breakdown"].items():
                max_pt = _factor_max(factor)
                pct    = int((pts / max_pt) * 100) if max_pt else 0
                st.markdown(
                    f"<small>{factor}</small>",
                    unsafe_allow_html=True,
                )
                st.progress(pct / 100, text=f"{pts}/{max_pt} pts")

    with e_col:
        st.markdown("**Experience & Education**")
        exp = details.get("exp_years", 0)
        st.metric("Years of Experience", f"{exp} yrs")
        st.metric("Resume Words", len(st.session_state["resume_text"].split()))
        st.metric("Skills Detected", len(st.session_state.get("skills_found", [])))

    st.markdown("---")

    # ── Tabs for detailed results ─────────────────────────────────────────────
    tabs = st.tabs([
        "🧠 AI Insights",
        "🛠️ Skills",
        "📋 JD Match",
        "✍️ Improvements",
        "⚠️ ATS Tips",
    ])

    # ─ Tab 1: AI Insights ──────────────────────────────────────────────────────
    with tabs[0]:
        if analysis and "error" not in analysis:
            if analysis.get("summary"):
                st.markdown("**Profile Summary**")
                st.info(analysis["summary"])

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**💪 Strengths**")
                for s in analysis.get("strengths", []):
                    st.markdown(f"✅ {s}")

            with col_b:
                st.markdown("**⚠️ Weaknesses**")
                for w in analysis.get("weaknesses", []):
                    st.markdown(f"🔸 {w}")

            if analysis.get("overall_impression"):
                st.markdown("**🎯 Overall Impression**")
                st.markdown(f"> {analysis['overall_impression']}")
        elif analysis and "error" in analysis:
            st.error(analysis["error"])
        else:
            st.info("Run analysis to see AI insights.")

    # ─ Tab 2: Skills ──────────────────────────────────────────────────────────
    with tabs[1]:
        skills = st.session_state.get("skills_found", [])
        missing = st.session_state.get("missing_skills", [])

        if skills:
            st.markdown(f"**Found {len(skills)} skills in your resume:**")
            # Render skills as chips
            chips_html = " ".join(
                f'<span class="skill-chip skill-found">{s}</span>' for s in skills
            )
            st.markdown(
                f'<div class="skills-container">{chips_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No specific technical skills detected.")

        if missing:
            st.markdown(f"**❌ {len(missing)} skills from JD missing in your resume:**")
            missing_html = " ".join(
                f'<span class="skill-chip skill-missing">{s}</span>' for s in missing
            )
            st.markdown(
                f'<div class="skills-container">{missing_html}</div>',
                unsafe_allow_html=True,
            )

    # ─ Tab 3: JD Match ────────────────────────────────────────────────────────
    with tabs[2]:
        if not jd_text:
            st.info("Add a Job Description on the Home page to see JD comparison.")
        else:
            analysis_jd = analysis or {}
            if analysis_jd.get("jd_match_analysis"):
                st.markdown("**🔗 JD Match Analysis**")
                st.markdown(analysis_jd["jd_match_analysis"])

            # Show matched vs unmatched JD skills
            resume_skills_set = {s.lower() for s in st.session_state.get("skills_found", [])}
            jd_skills = st.session_state.get("jd_skills", [])

            if jd_skills:
                matched   = [s for s in jd_skills if s.lower() in resume_skills_set]
                unmatched = [s for s in jd_skills if s.lower() not in resume_skills_set]

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**✅ Matched ({len(matched)})**")
                    for s in matched[:10]:
                        st.markdown(f"✅ {s}")
                with c2:
                    st.markdown(f"**❌ Missing ({len(unmatched)})**")
                    for s in unmatched[:10]:
                        st.markdown(f"❌ {s}")

    # ─ Tab 4: Improvements ────────────────────────────────────────────────────
    with tabs[3]:
        suggestions = st.session_state.get("improvement_tips", [])
        ats_fb      = st.session_state.get("ats_details", {}).get("feedback", [])

        if suggestions:
            for i, tip in enumerate(suggestions, 1):
                priority = tip.get("priority", "Medium")
                icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "🔵")

                with st.expander(
                    f"{icon} [{priority}] {tip.get('area', f'Tip {i}')}",
                    expanded=i == 1,
                ):
                    st.markdown(tip.get("suggestion", ""))
                    if tip.get("example"):
                        st.markdown(f"**Example:** _{tip['example']}_")
        else:
            if ats_fb:
                st.markdown("**Quick ATS Feedback:**")
                for fb in ats_fb:
                    st.markdown(f"- {fb}")
            else:
                st.info("Run analysis to see improvement suggestions.")

    # ─ Tab 5: ATS Tips ────────────────────────────────────────────────────────
    with tabs[4]:
        ats_tips = (analysis or {}).get("ats_tips", [])
        ats_fb   = st.session_state.get("ats_details", {}).get("feedback", [])
        all_tips = ats_tips + ats_fb

        if all_tips:
            for tip in all_tips:
                st.markdown(f"💡 {tip}")
        else:
            st.info("Run analysis to see ATS optimisation tips.")


def _factor_max(factor: str) -> int:
    """Return the maximum possible points for a scoring factor."""
    maxes = {
        "Keyword Match": 35,
        "Skill Breadth": 10,
        "Quantifiable Achievements": 10,
        "Action Verbs": 5,
        "Section Completeness": 10,
        "Education Level": 5,
        "Experience Years": 5,
        "Contact Info": 5,
        "Resume Length": 5,
        "Formatting": 10,
    }
    return maxes.get(factor, 10)
