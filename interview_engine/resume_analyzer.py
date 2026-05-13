"""
interview_engine/resume_analyzer.py
LLM-powered resume analysis: deep insights, improvement tips,
JD comparison, and missing skill identification.

All prompts are structured to return JSON so results can be
parsed and rendered as structured UI components.
"""

import logging
from models.llm_client import invoke_llm
from utils.helpers import parse_json_response

logger = logging.getLogger(__name__)


# ── Master analysis prompt ───────────────────────────────────────────────────

ANALYSIS_PROMPT = """
You are an expert ATS (Applicant Tracking System) analyst and career coach.
Analyse the following resume thoroughly and return a JSON object.

RESUME TEXT:
---
{resume_text}
---

JOB DESCRIPTION (if provided):
---
{job_description}
---

Return ONLY a valid JSON object with this exact structure:
{{
  "summary": "2-3 sentence professional summary of the candidate",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "skills_found": ["skill1", "skill2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "improvement_suggestions": [
    {{"area": "area name", "suggestion": "specific actionable suggestion"}},
    ...
  ],
  "jd_match_analysis": "detailed paragraph on how well the resume matches the JD",
  "ats_tips": ["tip 1", "tip 2", "tip 3"],
  "overall_impression": "recruiter-style overall impression paragraph"
}}

Be specific, actionable, and professional. Return ONLY the JSON, no other text.
""".strip()


IMPROVEMENT_PROMPT = """
You are a professional resume writer and career coach.
Review the following resume and provide 7 specific, actionable improvement suggestions.

RESUME:
{resume_text}

Return ONLY a JSON array of improvement objects:
[
  {{
    "area": "Short area label (e.g. Summary, Experience, Skills)",
    "priority": "High | Medium | Low",
    "suggestion": "Specific actionable suggestion in 1-2 sentences",
    "example": "Optional: brief example of improved wording"
  }},
  ...
]
Return ONLY the JSON array, no other text.
""".strip()


JD_COMPARE_PROMPT = """
You are an ATS expert. Compare the resume against the job description.

RESUME SKILLS / EXPERIENCE:
{resume_summary}

JOB DESCRIPTION:
{job_description}

Return ONLY a JSON object:
{{
  "match_score": <integer 0-100>,
  "matched_requirements": ["requirement 1", ...],
  "unmatched_requirements": ["requirement 1", ...],
  "transferable_skills": ["skill 1", ...],
  "recommended_additions": ["addition 1", ...],
  "tailoring_advice": "Paragraph of advice on tailoring this resume for this JD"
}}
""".strip()


# ── Public API ────────────────────────────────────────────────────────────────

def analyse_resume(
    llm,
    resume_text: str,
    job_description: str = "",
) -> dict:
    """
    Perform LLM-powered deep analysis of a resume.

    Args:
        llm:             LangChain LLM instance.
        resume_text:     Cleaned resume text.
        job_description: Optional JD text for comparison.

    Returns:
        Parsed analysis dict, or a dict with an 'error' key on failure.
    """
    prompt = ANALYSIS_PROMPT.format(
        resume_text=resume_text[:4000],        # token safety
        job_description=job_description[:2000] if job_description else "Not provided",
    )

    raw = invoke_llm(llm, prompt)
    if not raw:
        return {"error": "LLM returned no response. Check your API key."}

    result = parse_json_response(raw)
    if not result:
        logger.warning("Could not parse JSON from analysis response. Raw: %s", raw[:300])
        # Return raw text in a structured wrapper as fallback
        return {
            "summary": raw[:600],
            "strengths": [],
            "weaknesses": [],
            "skills_found": [],
            "missing_skills": [],
            "improvement_suggestions": [],
            "jd_match_analysis": "",
            "ats_tips": [],
            "overall_impression": "",
            "parse_warning": "Response could not be fully parsed.",
        }

    return result


def get_improvement_suggestions(llm, resume_text: str) -> list[dict]:
    """
    Generate targeted resume improvement suggestions.

    Returns:
        List of suggestion dicts with keys: area, priority, suggestion, example.
    """
    prompt = IMPROVEMENT_PROMPT.format(resume_text=resume_text[:4000])
    raw = invoke_llm(llm, prompt)

    if not raw:
        return []

    result = parse_json_response(raw)
    if isinstance(result, list):
        return result

    logger.warning("Could not parse improvement suggestions JSON.")
    return []


def compare_with_jd(
    llm,
    resume_text: str,
    job_description: str,
) -> dict:
    """
    Detailed JD-vs-resume comparison.

    Returns:
        Comparison dict or {'error': '...'} on failure.
    """
    if not job_description.strip():
        return {"error": "No job description provided."}

    # Build a condensed resume summary to save tokens
    resume_summary = resume_text[:2000]

    prompt = JD_COMPARE_PROMPT.format(
        resume_summary=resume_summary,
        job_description=job_description[:2000],
    )

    raw = invoke_llm(llm, prompt)
    if not raw:
        return {"error": "LLM returned no response."}

    result = parse_json_response(raw)
    if not result:
        return {"error": "Could not parse JD comparison response."}

    return result
