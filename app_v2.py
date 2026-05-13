"""
AI Resume Analyzer & Interview Assistant
Main Streamlit Application Entry Point
"""

import streamlit as st
import os
from pathlib import Path
from resume_parser.parser_v2 import parse_resume
# ── Page configuration (must be first Streamlit call) ──────────────────────
st.set_page_config(
    page_title="ResumeAI Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/your-repo/ai-resume-analyzer",
        "About": "AI Resume Analyzer & Interview Assistant v1.0",
    },
)

# ── Load custom CSS ─────────────────────────────────────────────────────────
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── Local imports (after path setup) ───────────────────────────────────────
from utils.session_state import init_session_state
from utils.sidebar import render_sidebar
from utils.config import load_config

# Page modules
from templates.home_page import render_home
from templates.analysis_page import render_analysis
from templates.interview_page import render_interview
from templates.chat_page import render_chat
from templates.career_page import render_career

# ── Initialise session state ────────────────────────────────────────────────
init_session_state()

# ── Load configuration / validate API keys ─────────────────────────────────
config = load_config()

# ── Sidebar navigation ──────────────────────────────────────────────────────
page = render_sidebar(config)

# ── Route to the selected page ──────────────────────────────────────────────
PAGES = {
    "🏠 Home":               render_home,
    "📄 Resume Analysis":    render_analysis,
    "🎤 Interview Prep":     render_interview,
    "💬 AI Chat Assistant":  render_chat,
    "🚀 Career Advisor":     render_career,
}

if page in PAGES:
    PAGES[page](config)
else:
    render_home(config)
