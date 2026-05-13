"""
resume_parser/skill_extractor.py
NLP pipeline for extracting structured information from resume text.

Pipeline:
  1. Section detection (regex + heuristics)
  2. Skill extraction  (keyword matching against curated taxonomy + spaCy NER)
  3. Experience duration calculation
  4. Education level detection
  5. Contact info extraction
"""

import re
import logging
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Curated skill taxonomy ───────────────────────────────────────────────────
SKILL_TAXONOMY = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "go",
        "rust", "scala", "kotlin", "swift", "r", "matlab", "perl", "ruby",
        "php", "bash", "shell", "powershell", "dart", "elixir", "haskell",
    ],
    "web_frameworks": [
        "react", "angular", "vue", "next.js", "nuxt", "svelte", "django",
        "flask", "fastapi", "spring", "spring boot", "express", "node.js",
        "nestjs", "laravel", "rails", "asp.net", "blazor",
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis",
        "elasticsearch", "cassandra", "dynamodb", "oracle", "sql server",
        "mssql", "neo4j", "firebase", "supabase", "cockroachdb",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
        "circleci", "helm", "prometheus", "grafana", "nginx", "apache",
        "linux", "unix",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
        "sklearn", "pandas", "numpy", "scipy", "hugging face", "transformers",
        "langchain", "openai", "llm", "rag", "faiss", "chromadb",
        "xgboost", "lightgbm", "random forest", "neural network",
        "reinforcement learning", "generative ai",
    ],
    "data_tools": [
        "spark", "hadoop", "kafka", "airflow", "dbt", "tableau", "power bi",
        "looker", "jupyter", "databricks", "snowflake", "bigquery", "redshift",
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "critical thinking", "project management", "agile", "scrum",
        "kanban", "time management", "mentoring", "collaboration",
    ],
    "other_tech": [
        "git", "github", "gitlab", "jira", "confluence", "rest api",
        "graphql", "microservices", "ci/cd", "tdd", "bdd", "oop",
        "functional programming", "design patterns", "system design",
    ],
}

# Flattened skill list for quick lookup
ALL_SKILLS: list[str] = [
    skill
    for skills in SKILL_TAXONOMY.values()
    for skill in skills
]

# Regex pattern for a single year (1970–2099)
_YEAR_RE = re.compile(r"\b(19[7-9]\d|20[0-2]\d)\b")

# Section header detection patterns
_SECTION_HEADERS = {
    "experience":  re.compile(r"\b(experience|employment|work history|career)\b", re.I),
    "education":   re.compile(r"\b(education|academic|qualification|degree)\b", re.I),
    "skills":      re.compile(r"\b(skills|technologies|competencies|expertise)\b", re.I),
    "projects":    re.compile(r"\b(projects|portfolio|open.?source)\b", re.I),
    "summary":     re.compile(r"\b(summary|profile|objective|about)\b", re.I),
    "certifications": re.compile(r"\b(certif|license|award|achievement)\b", re.I),
}

EDUCATION_LEVELS = {
    "phd":      re.compile(r"\b(ph\.?d|doctorate|doctor of)\b", re.I),
    "masters":  re.compile(r"\b(master|m\.?s\.?c?|m\.?eng|mba)\b", re.I),
    "bachelors":re.compile(r"\b(bachelor|b\.?s\.?c?|b\.?e\.?|b\.?tech|b\.?a\.?)\b", re.I),
    "associate":re.compile(r"\b(associate|a\.?a\.?|a\.?s\.?)\b", re.I),
    "diploma":  re.compile(r"\b(diploma|certificate program)\b", re.I),
}


# ── Public API ───────────────────────────────────────────────────────────────

def extract_resume_info(text: str) -> dict:
    """
    Run the full NLP pipeline on resume text.

    Args:
        text: Cleaned resume text string.

    Returns:
        dict with keys: skills, skills_by_category, years_experience,
        education_level, contact_info, sections, word_count.
    """
    lower = text.lower()

    return {
        "skills":             extract_skills(lower),
        "skills_by_category": extract_skills_by_category(lower),
        "years_experience":   estimate_experience_years(text),
        "education_level":    detect_education_level(lower),
        "contact_info":       extract_contact_info(text),
        "sections":           detect_sections(text),
        "word_count":         len(text.split()),
    }


def extract_skills(text_lower: str) -> list[str]:
    """
    Return a deduplicated list of skills found in the resume text.
    Uses exact substring matching against the skill taxonomy.

    Args:
        text_lower: Lowercase resume text.
    """
    found = set()
    for skill in ALL_SKILLS:
        # Match whole-word occurrences only (handles 'c' vs 'c++' etc.)
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.add(skill)
    return sorted(found)


def extract_skills_by_category(text_lower: str) -> dict[str, list[str]]:
    """Return skills grouped by taxonomy category."""
    result = defaultdict(list)
    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
            if re.search(pattern, text_lower):
                result[category].append(skill)
    return dict(result)


def extract_skills_from_text(text: str) -> list[str]:
    """
    Convenience wrapper that accepts mixed-case text.
    """
    return extract_skills(text.lower())


def estimate_experience_years(text: str) -> int:
    """
    Heuristically estimate total years of professional experience.

    Strategy:
    - Find all 4-digit years mentioned in the text.
    - Compute the span from the earliest to latest year found.
    - Cap at 40 years (sanity check).
    """
    years = [int(y) for y in _YEAR_RE.findall(text)]
    if len(years) < 2:
        return 0
    span = max(years) - min(years)
    return min(span, 40)


def detect_education_level(text_lower: str) -> str:
    """
    Detect the highest education level mentioned in the text.
    Returns one of: 'phd', 'masters', 'bachelors', 'associate',
                    'diploma', 'high_school', or 'unknown'.
    """
    hierarchy = ["phd", "masters", "bachelors", "associate", "diploma"]
    for level in hierarchy:
        if EDUCATION_LEVELS[level].search(text_lower):
            return level
    if re.search(r"\b(high school|secondary|12th|hsc|ssc)\b", text_lower):
        return "high_school"
    return "unknown"


def extract_contact_info(text: str) -> dict:
    """
    Extract email, phone, LinkedIn and GitHub handles from resume text.
    """
    email_match = re.search(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text
    )
    phone_match = re.search(
        r"(?:\+?\d[\d\s\-().]{7,}\d)", text
    )
    linkedin_match = re.search(
        r"linkedin\.com/in/([a-zA-Z0-9\-_]+)", text
    )
    github_match = re.search(
        r"github\.com/([a-zA-Z0-9\-_]+)", text
    )

    return {
        "email":    email_match.group() if email_match else None,
        "phone":    phone_match.group().strip() if phone_match else None,
        "linkedin": linkedin_match.group(1) if linkedin_match else None,
        "github":   github_match.group(1) if github_match else None,
    }


def detect_sections(text: str) -> list[str]:
    """Return a list of section names detected in the resume."""
    detected = []
    for section, pattern in _SECTION_HEADERS.items():
        if pattern.search(text):
            detected.append(section)
    return detected


def get_missing_skills(resume_skills: list[str], jd_skills: list[str]) -> list[str]:
    """
    Return skills present in the JD but absent from the resume.

    Args:
        resume_skills: Skills extracted from the resume.
        jd_skills:     Skills extracted from the job description.
    """
    resume_set = {s.lower() for s in resume_skills}
    return [s for s in jd_skills if s.lower() not in resume_set]
