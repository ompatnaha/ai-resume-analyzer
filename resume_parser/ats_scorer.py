"""
resume_parser/ats_scorer.py
ATS (Applicant Tracking System) scoring engine.

Scoring model (100 points total):
─────────────────────────────────────────────────────
 Factor                          Weight   Notes
─────────────────────────────────────────────────────
 Keyword / skill match vs JD      35 pts  Jaccard similarity
 Skill breadth (unique categories) 10 pts  # taxonomy categories
 Quantifiable achievements          10 pts  digits in bullet points
 Action verbs usage                  5 pts  strong verb count
 Section completeness               10 pts  expected sections present
 Education level                     5 pts  degree hierarchy bonus
 Experience years                    5 pts  scaled 0→5 for 0-10 yrs
 Contact info completeness           5 pts  email/phone/linkedin
 Resume length / density             5 pts  word count in ideal range
 Formatting signals                  10 pts  bullets, consistent dates
─────────────────────────────────────────────────────
"""

import re
import logging
from resume_parser.skill_extractor import (
    extract_skills,
    detect_sections,
    detect_education_level,
    estimate_experience_years,
    extract_contact_info,
    SKILL_TAXONOMY,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

ACTION_VERBS = {
    "achieved", "built", "created", "delivered", "designed", "developed",
    "engineered", "established", "executed", "generated", "implemented",
    "improved", "increased", "launched", "led", "managed", "mentored",
    "optimised", "optimized", "reduced", "refactored", "scaled", "shipped",
    "solved", "streamlined", "transformed",
}

EXPECTED_SECTIONS = ["experience", "education", "skills", "projects", "summary"]

EDUCATION_SCORE = {
    "phd":        5,
    "masters":    4,
    "bachelors":  3,
    "associate":  2,
    "diploma":    1,
    "high_school":0,
    "unknown":    0,
}


# ── Main scorer ──────────────────────────────────────────────────────────────

def calculate_ats_score(
    resume_text: str,
    job_description: str = "",
) -> dict:
    """
    Compute a multi-factor ATS score for a resume.

    Args:
        resume_text:     Full cleaned resume text.
        job_description: Optional JD text for keyword matching.

    Returns:
        dict with keys:
          total_score (int 0-100),
          breakdown (dict of factor→points),
          feedback (list of improvement hints),
          grade (str: A/B/C/D/F),
    """
    text_lower = resume_text.lower()
    breakdown: dict[str, int] = {}
    feedback:  list[str]      = []

    # ── 1. Keyword / skill match (35 pts) ────────────────────────────────────
    kw_score, kw_feedback = _score_keyword_match(text_lower, job_description)
    breakdown["Keyword Match"] = kw_score
    feedback.extend(kw_feedback)

    # ── 2. Skill breadth (10 pts) ────────────────────────────────────────────
    breadth_score, breadth_fb = _score_skill_breadth(text_lower)
    breakdown["Skill Breadth"] = breadth_score
    feedback.extend(breadth_fb)

    # ── 3. Quantifiable achievements (10 pts) ────────────────────────────────
    quant_score, quant_fb = _score_quantifiable(resume_text)
    breakdown["Quantifiable Achievements"] = quant_score
    feedback.extend(quant_fb)

    # ── 4. Action verbs (5 pts) ──────────────────────────────────────────────
    verb_score, verb_fb = _score_action_verbs(text_lower)
    breakdown["Action Verbs"] = verb_score
    feedback.extend(verb_fb)

    # ── 5. Section completeness (10 pts) ─────────────────────────────────────
    section_score, section_fb = _score_sections(resume_text)
    breakdown["Section Completeness"] = section_score
    feedback.extend(section_fb)

    # ── 6. Education (5 pts) ─────────────────────────────────────────────────
    edu_score = EDUCATION_SCORE.get(detect_education_level(text_lower), 0)
    breakdown["Education Level"] = edu_score

    # ── 7. Experience years (5 pts) ──────────────────────────────────────────
    exp_years  = estimate_experience_years(resume_text)
    exp_score  = min(5, int(exp_years * 0.5))   # 10 yrs → 5 pts
    breakdown["Experience Years"] = exp_score

    # ── 8. Contact completeness (5 pts) ──────────────────────────────────────
    contact_score, contact_fb = _score_contact(resume_text)
    breakdown["Contact Info"] = contact_score
    feedback.extend(contact_fb)

    # ── 9. Resume length / density (5 pts) ───────────────────────────────────
    length_score, length_fb = _score_length(resume_text)
    breakdown["Resume Length"] = length_score
    feedback.extend(length_fb)

    # ── 10. Formatting signals (10 pts) ──────────────────────────────────────
    fmt_score, fmt_fb = _score_formatting(resume_text)
    breakdown["Formatting"] = fmt_score
    feedback.extend(fmt_fb)

    # ── Aggregate ─────────────────────────────────────────────────────────────
    total = sum(breakdown.values())
    total = max(0, min(100, total))   # clamp

    return {
        "total_score": total,
        "breakdown":   breakdown,
        "feedback":    feedback,
        "grade":       _grade(total),
        "exp_years":   exp_years,
    }


# ── Factor helpers ────────────────────────────────────────────────────────────

def _score_keyword_match(text_lower: str, jd: str) -> tuple[int, list[str]]:
    """Jaccard-based keyword match, max 35 pts."""
    if not jd:
        return 20, ["Add a job description to get accurate keyword match scoring."]

    resume_skills = set(extract_skills(text_lower))
    jd_skills     = set(extract_skills(jd.lower()))

    if not jd_skills:
        return 20, ["Could not extract skills from the job description."]

    intersection = resume_skills & jd_skills
    union        = resume_skills | jd_skills
    jaccard      = len(intersection) / len(union) if union else 0

    score = min(35, int(jaccard * 60))   # scale: 0.58 Jaccard → 35 pts

    fb = []
    missing = jd_skills - resume_skills
    if missing:
        top_missing = sorted(missing)[:5]
        fb.append(f"Add these JD keywords to improve ATS match: {', '.join(top_missing)}.")
    return score, fb


def _score_skill_breadth(text_lower: str) -> tuple[int, list[str]]:
    """Award points for covering multiple skill categories, max 10 pts."""
    categories_found = sum(
        1
        for skills in SKILL_TAXONOMY.values()
        if any(skill in text_lower for skill in skills)
    )
    score = min(10, categories_found * 2)
    fb = []
    if categories_found < 3:
        fb.append("Broaden your skill set — include cloud, DevOps, or data tools.")
    return score, fb


def _score_quantifiable(text: str) -> tuple[int, list[str]]:
    """
    Award points for lines containing numbers/percentages (achievements).
    Up to 10 pts.
    """
    number_lines = sum(
        1
        for line in text.splitlines()
        if re.search(r"\d+[%x]?|\$[\d,]+", line) and len(line.strip()) > 20
    )
    score = min(10, number_lines * 2)
    fb = []
    if number_lines < 3:
        fb.append("Quantify achievements — add percentages, dollar amounts, or counts (e.g. 'reduced load time by 40%').")
    return score, fb


def _score_action_verbs(text_lower: str) -> tuple[int, list[str]]:
    """Award points for strong action-verb usage, max 5 pts."""
    words    = set(re.findall(r"\b\w+\b", text_lower))
    matches  = words & ACTION_VERBS
    score    = min(5, len(matches))
    fb = []
    if len(matches) < 3:
        fb.append("Start bullet points with strong action verbs: led, built, optimised, delivered.")
    return score, fb


def _score_sections(text: str) -> tuple[int, list[str]]:
    """Award 2 pts per expected section found, max 10 pts."""
    found   = detect_sections(text)
    score   = min(10, len(found) * 2)
    missing = [s for s in EXPECTED_SECTIONS if s not in found]
    fb = []
    if missing:
        fb.append(f"Add these missing sections: {', '.join(missing).title()}.")
    return score, fb


def _score_contact(text: str) -> tuple[int, list[str]]:
    """1 pt each for email, phone, LinkedIn, GitHub, name. Max 5 pts."""
    info  = extract_contact_info(text)
    score = sum([
        bool(info.get("email")),
        bool(info.get("phone")),
        bool(info.get("linkedin")),
        bool(info.get("github")),
        # Simple heuristic: if text starts with a non-URL capitalised word, assume name
        bool(re.match(r"[A-Z][a-z]+ [A-Z][a-z]+", text.strip())),
    ])
    fb = []
    if not info.get("linkedin"):
        fb.append("Add your LinkedIn profile URL to improve recruiter visibility.")
    if not info.get("github"):
        fb.append("Include your GitHub URL — it signals hands-on technical work.")
    return score, fb


def _score_length(text: str) -> tuple[int, list[str]]:
    """Ideal resume: 400-900 words. Max 5 pts."""
    word_count = len(text.split())
    fb = []
    if 400 <= word_count <= 900:
        return 5, []
    if word_count < 200:
        fb.append("Resume is too short — expand experience and project descriptions.")
        return 1, fb
    if word_count < 400:
        fb.append("Resume could be more detailed — aim for 400-900 words.")
        return 3, fb
    # > 900
    fb.append("Resume may be too long — consider trimming to 1-2 pages (400-900 words).")
    return 3, fb


def _score_formatting(text: str) -> tuple[int, list[str]]:
    """
    Heuristic formatting check — max 10 pts.
    Checks: bullet usage, consistent date format, all-caps sections.
    """
    score = 0
    fb    = []

    # Bullet points or hyphens used
    if re.search(r"^[\•\-\*▪►]", text, re.MULTILINE):
        score += 4
    else:
        fb.append("Use bullet points (•/-) for experience and project descriptions.")

    # At least one date / year reference
    if re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})\b", text, re.I):
        score += 3
    else:
        fb.append("Include dates for each role and education entry.")

    # Section headers are readable (not purely lower-case all text)
    caps_lines = sum(1 for l in text.splitlines() if l.isupper() and 3 < len(l) < 40)
    if caps_lines >= 2:
        score += 3
    else:
        score += 2   # partial credit

    return min(10, score), fb


# ── Grading ──────────────────────────────────────────────────────────────────

def _grade(score: int) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"
