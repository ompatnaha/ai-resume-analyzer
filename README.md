# 🎯 ResumeAI Pro

> **AI-powered Resume Analyzer & Interview Preparation Assistant**
> Built with Python · Streamlit · LangChain · Gemini/OpenAI · FAISS · Sentence Transformers

---

## 📸 Features

| Feature | Description |
|---|---|
| 📄 **PDF Parsing** | Multi-engine PDF extraction (pdfplumber → PyMuPDF → pdfminer fallback chain) |
| 🔬 **NLP Analysis** | Skill taxonomy matching, experience estimation, education detection |
| 📊 **ATS Scoring** | 10-factor scoring algorithm with detailed breakdown (0–100) |
| 🔍 **JD Comparison** | Keyword gap analysis between resume and job description |
| 🤖 **AI Analysis** | Deep LLM-powered insights, strengths, weaknesses, impressions |
| ✍️ **Improvements** | 7 prioritised, actionable resume suggestions with examples |
| 🎤 **Interview Prep** | HR, Technical, Project, and Situational (STAR) question generation |
| 💬 **RAG Chat** | FAISS/ChromaDB-powered chat assistant grounded in your resume |
| 🚀 **Career Advice** | Role recommendations, salary estimates, learning roadmap |
| 💾 **History** | Full chat history with rolling context window (20 turns) |

---

## 🏗️ Project Architecture

```
ai_resume_analyzer/
│
├── app.py                          # Entry point — Streamlit page router
│
├── utils/
│   ├── config.py                   # Env vars + API key management
│   ├── session_state.py            # Centralised state initialisation
│   ├── sidebar.py                  # Navigation + status badges
│   └── helpers.py                  # Text cleaning, chunking, JSON parsing
│
├── resume_parser/
│   ├── pdf_extractor.py            # 3-engine PDF text extraction
│   ├── skill_extractor.py          # NLP pipeline: skills, exp, education
│   └── ats_scorer.py               # Multi-factor ATS scoring engine
│
├── models/
│   ├── llm_client.py               # LangChain Gemini/OpenAI wrapper
│   └── vector_store.py             # FAISS / ChromaDB builder + retriever
│
├── interview_engine/
│   ├── resume_analyzer.py          # LLM deep analysis + JD comparison
│   ├── question_generator.py       # HR/Tech/Project/Situational generators
│   └── chat_assistant.py           # RAG chat with history management
│
├── templates/
│   ├── home_page.py                # Upload + quick-start page
│   ├── analysis_page.py            # ATS score + AI insights
│   ├── interview_page.py           # Interview question tabs
│   ├── chat_page.py                # Chat interface
│   └── career_page.py              # Career advisor
│
├── assets/
│   └── styles.css                  # Custom Streamlit CSS
│
├── .env.example                    # Environment variable template
├── requirements.txt
└── README.md
```

---

## 📐 System Architecture Diagram

```
User (Browser)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit App (app.py)                    │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Home     │  │ Analysis   │  │Interview │  │  Chat    │  │
│  │ (Upload) │  │ (ATS+AI)   │  │  (Gen)   │  │  (RAG)   │  │
│  └────┬─────┘  └─────┬──────┘  └────┬─────┘  └────┬─────┘  │
└───────┼──────────────┼──────────────┼──────────────┼────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PDF Parser   │ │ ATS Scorer   │ │ Q Generator  │ │ Chat Engine  │
│ pdfplumber   │ │ 10 factors   │ │ 4 categories │ │ RAG + hist.  │
│ PyMuPDF      │ │ 0-100 score  │ │ JSON output  │ │ rolling ctx  │
│ pdfminer     │ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
└──────┬───────┘        │                │                │
       │                └────────────────┴────────────────┘
       ▼                                 │
┌──────────────┐                         ▼
│ NLP Pipeline │                ┌──────────────────┐
│ Skills +350  │                │   LLM Client     │
│ Exp years    │                │ LangChain wrapper│
│ Education    │                │ Gemini / OpenAI  │
│ Contact info │                └──────────────────┘
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Vector Store │
│ FAISS/Chroma │
│ all-MiniLM   │
│ Sentence-T.  │
└──────────────┘
```

---

## 📊 ATS Scoring Logic

The ATS score is calculated locally (no API call needed) across **10 weighted factors**:

| # | Factor | Max Points | Method |
|---|--------|-----------|--------|
| 1 | **Keyword/JD Match** | 35 | Jaccard similarity of skill sets |
| 2 | **Skill Breadth** | 10 | # taxonomy categories covered |
| 3 | **Quantifiable Achievements** | 10 | Lines with numbers/% |
| 4 | **Action Verbs** | 5 | Matches against 26-verb list |
| 5 | **Section Completeness** | 10 | 5 expected sections (2 pts each) |
| 6 | **Education Level** | 5 | PhD→5, Masters→4, Bachelor→3 |
| 7 | **Experience Years** | 5 | Year span × 0.5, capped at 5 |
| 8 | **Contact Info** | 5 | Email, phone, LinkedIn, GitHub |
| 9 | **Resume Length** | 5 | 400–900 words = full score |
| 10 | **Formatting** | 10 | Bullets, dates, section headers |

**Grade mapping:** A (≥85) · B (≥70) · C (≥55) · D (≥40) · F (<40)

---

## 🔬 NLP Pipeline

```
Raw PDF bytes
     │
     ▼  [resume_parser/pdf_extractor.py]
Text Extraction (pdfplumber → PyMuPDF → pdfminer)
     │
     ▼  [utils/helpers.py]
Text Cleaning (control chars, whitespace normalisation)
     │
     ▼  [resume_parser/skill_extractor.py]
┌────────────────────────────────────────────┐
│  Skill Extraction                          │
│  - 350+ skills across 8 taxonomy categories│
│  - Regex whole-word boundary matching      │
│  - Grouped by: languages, frameworks,      │
│    databases, cloud, AI/ML, data tools     │
├────────────────────────────────────────────┤
│  Experience Estimation                     │
│  - Extract all 4-digit years (1970-2099)   │
│  - Span = max_year − min_year              │
├────────────────────────────────────────────┤
│  Education Detection                       │
│  - Regex patterns for PhD, Masters,        │
│    Bachelor, Associate, Diploma            │
├────────────────────────────────────────────┤
│  Contact Info Extraction                   │
│  - Email, phone (regex), LinkedIn, GitHub  │
├────────────────────────────────────────────┤
│  Section Detection                         │
│  - experience / education / skills /       │
│    projects / summary / certifications     │
└────────────────────────────────────────────┘
     │
     ▼  [utils/helpers.py]
Text Chunking (500-char chunks, 50-char overlap)
     │
     ▼  [models/vector_store.py]
Embedding (all-MiniLM-L6-v2 via Sentence Transformers)
     │
     ▼
FAISS / ChromaDB Index (for RAG retrieval)
```

---

## 🎤 Interview Generation Workflow

```
Resume Text + Job Role
        │
        ▼
┌─────────────────────────────────────────────┐
│  Prompt Engineering (question_generator.py) │
│                                             │
│  Template fills:                            │
│  - {resume_text} (truncated to 4000 chars)  │
│  - {job_role}                               │
│  - {count} (user-selected)                  │
└─────────────────┬───────────────────────────┘
                  │
          ┌───────┼──────────┐
          ▼       ▼          ▼
      HR Prompt  Tech    Project   Situational
      Prompt     Prompt  Prompt    (STAR) Prompt
          │       │          │         │
          └───────┴──────────┴─────────┘
                  │
                  ▼
            LLM Invocation
                  │
                  ▼
        JSON Array Response
        [{ question, category,
           difficulty, tip }, ...]
                  │
                  ▼
     Rendered as expandable cards
     with difficulty badges + download
```

---

## 🚀 Quick Start

### 1. Clone and install
```bash
git clone https://github.com/your-repo/ai-resume-analyzer.git
cd ai-resume-analyzer
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY or OPENAI_API_KEY
```

### 3. Run
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

---

## 🐳 Deployment

### Streamlit Community Cloud (Free)
1. Push to a public GitHub repository.
2. Visit https://share.streamlit.io → New app.
3. Set **Secrets** in the dashboard (same keys as `.env`).
4. Deploy — done!

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
```bash
docker build -t resumeai-pro .
docker run -p 8501:8501 --env-file .env resumeai-pro
```

### Railway / Render
1. Connect GitHub repo.
2. Set env variables in the dashboard.
3. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

---

## 🔑 API Keys

| Provider | Where to get | Free tier |
|---|---|---|
| **Gemini** | https://aistudio.google.com/app/apikey | Yes (generous) |
| **OpenAI** | https://platform.openai.com/api-keys | Pay-as-you-go |

Set `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` in your `.env`.

---

## 📦 Tech Stack

- **Frontend:** Streamlit 1.35+ with custom CSS (Sora + DM Sans fonts)
- **LLM Orchestration:** LangChain (Gemini 1.5 Flash / GPT-4o-mini)
- **PDF Parsing:** pdfplumber + PyMuPDF + pdfminer (3-engine fallback chain)
- **NLP:** Custom regex + taxonomy matching (350+ skills)
- **Embeddings:** Sentence Transformers `all-MiniLM-L6-v2`
- **Vector Store:** FAISS (default) or ChromaDB
- **Config:** python-dotenv for environment variable management

---

## 📄 License

MIT License — free for personal and commercial use.
