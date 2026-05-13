"""
templates/home_page.py
Landing / home page — upload resume, enter JD, kick off analysis.
"""

import streamlit as st
from resume_parser.pdf_extractor import extract_text_from_pdf
from resume_parser.parser_v2 import parse_resume
from utils.helpers import clean_text, chunk_text
from utils.config import is_configured
from models.vector_store import build_vector_store


def render_home(config: dict) -> None:
    """Render the Home / Upload page."""

    # ── Hero section ─────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-section">
            <h1 class="hero-title">🎯 ResumeAI <span class="accent">Pro</span></h1>
            <p class="hero-subtitle">
                AI-powered resume analysis, ATS scoring, and interview preparation
                — tailored to your unique profile.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Feature cards ─────────────────────────────────────────────────────────
    cols = st.columns(4)
    features = [
        ("📊", "ATS Scoring",     "Multi-factor scoring against real ATS criteria"),
        ("🔍", "Skill Gap Analysis", "Compare your skills with the job description"),
        ("🎤", "Interview Prep",  "AI-generated HR, technical & project questions"),
        ("💬", "AI Chat",         "RAG-powered assistant trained on your resume"),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div class="feature-icon">{icon}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Upload + JD columns ───────────────────────────────────────────────────
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("### 📄 Upload Your Resume")
        st.markdown("_Supported format: PDF_")

        uploaded_file = st.file_uploader(
            "Drop your resume PDF here",
            type=["pdf"],
            key="resume_uploader",
            help="Your file is processed locally and never stored on our servers.",
        )

        if uploaded_file:
            with st.spinner("Extracting text from PDF…"):
                raw_bytes = uploaded_file.read()
                raw_text  = extract_text_from_pdf(raw_bytes)

            if raw_text:
                cleaned = clean_text(raw_text)
                parsed_data = parse_resume(uploaded_file)

                st.subheader("📌 Parsed Resume Information")
                st.write(parsed_data)
                chunks  = chunk_text(cleaned)

                st.session_state["resume_text"]     = cleaned
                st.session_state["resume_filename"] = uploaded_file.name
                st.session_state["resume_chunks"]   = chunks
                st.session_state["analysis_done"]   = False

                # Build vector store for RAG chat
                with st.spinner("Building knowledge index…"):
                    retriever = build_vector_store(chunks, config)
                    st.session_state["vector_store"] = retriever

                st.success(
                    f"✅ Resume loaded — {len(cleaned.split())} words, "
                    f"{len(chunks)} chunks indexed."
                )

                with st.expander("👁️ Preview extracted text", expanded=False):
                    st.text_area(
                        "Extracted Text",
                        value=cleaned[:2000] + ("…" if len(cleaned) > 2000 else ""),
                        height=250,
                        disabled=True,
                    )
            else:
                st.error(
                    "❌ Could not extract text from this PDF. "
                    "Ensure it is a text-based (not scanned) PDF."
                )

    with right:
        st.markdown("### 💼 Job Description (Optional)")
        st.markdown("_Paste the JD for keyword matching and gap analysis._")

        jd = st.text_area(
            "Paste job description here",
            value=st.session_state.get("job_description", ""),
            height=280,
            placeholder="Paste the full job description here for the best results…",
            key="jd_input",
        )
        st.session_state["job_description"] = jd

        if jd.strip():
            word_count = len(jd.split())
            st.caption(f"📝 {word_count} words in JD")

    st.markdown("---")

    # ── Quick action buttons ──────────────────────────────────────────────────
    if st.session_state.get("resume_text"):
        st.markdown("### 🚀 Ready to Analyse")
        btn_cols = st.columns(4)

        actions = [
            ("📊 Analyse Resume",     "📄 Resume Analysis"),
            ("🎤 Prep Interviews",    "🎤 Interview Prep"),
            ("💬 Chat with AI",       "💬 AI Chat Assistant"),
            ("🚀 Career Suggestions", "🚀 Career Advisor"),
        ]

        for col, (label, target_page) in zip(btn_cols, actions):
            with col:
                if st.button(label, use_container_width=True):
                    if not is_configured(config):
                        st.error("Please set your API key in the sidebar first.")
                    else:
                        st.session_state["active_page"] = target_page
                        st.rerun()
    else:
        st.info("⬆️ Upload your resume PDF above to get started.")

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚙️ How It Works")

    steps = st.columns(5)
    step_data = [
        ("1️⃣", "Upload PDF",     "Your resume PDF is parsed with pdfplumber/PyMuPDF"),
        ("2️⃣", "NLP Extraction", "Skills, experience & education extracted via NLP"),
        ("3️⃣", "ATS Scoring",    "10-factor ATS score calculated instantly"),
        ("4️⃣", "AI Analysis",    "Gemini/GPT provides deep insights & suggestions"),
        ("5️⃣", "Interview Prep", "Personalised questions across 4 question types"),
    ]
    for col, (num, title, desc) in zip(steps, step_data):
        with col:
            st.markdown(
                f"""
                <div class="step-card">
                    <div class="step-num">{num}</div>
                    <div class="step-title">{title}</div>
                    <div class="step-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
