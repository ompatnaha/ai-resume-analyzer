"""
interview_engine/question_generator.py
AI-powered interview question generation.

Generates four categories of questions tailored to the candidate's resume:
  1. HR / Behavioral    – culture fit, soft skills, motivation
  2. Technical          – stack-specific deep-dives
  3. Project-based      – questions derived from listed projects
  4. Situational/STAR   – scenario-based behavioural questions

Each generator returns a list of dicts with:
  { "question": str, "category": str, "difficulty": str, "tip": str }
"""

import logging
from models.llm_client import invoke_llm
from utils.helpers import parse_json_response

logger = logging.getLogger(__name__)


# ── Prompt templates ─────────────────────────────────────────────────────────

_HR_PROMPT = """
You are a senior HR manager conducting a job interview.
Based on the following resume, generate {count} HR and behavioural interview questions.

RESUME:
{resume_text}

JOB ROLE (if provided): {job_role}

Return ONLY a JSON array:
[
  {{
    "question": "Full interview question",
    "category": "HR",
    "difficulty": "Easy | Medium | Hard",
    "tip": "Short interviewer tip — what a great answer looks like"
  }},
  ...
]
""".strip()


_TECHNICAL_PROMPT = """
You are a senior technical interviewer for a {job_role} position.
Based on this resume, generate {count} technical interview questions that probe
the candidate's depth of knowledge in their stated skills.

RESUME:
{resume_text}

Focus on their strongest / most-mentioned technologies.
Include coding concepts, system design, and architecture questions.

Return ONLY a JSON array:
[
  {{
    "question": "Full technical question",
    "category": "Technical",
    "difficulty": "Easy | Medium | Hard",
    "tip": "What a strong answer should cover"
  }},
  ...
]
""".strip()


_PROJECT_PROMPT = """
You are a technical interviewer. Generate {count} project-based interview questions
derived specifically from the projects mentioned in this resume.

RESUME:
{resume_text}

Questions should probe:
- Technical decisions made
- Challenges faced and how they were solved
- Architecture and scalability considerations
- What the candidate would do differently

Return ONLY a JSON array:
[
  {{
    "question": "Full project-focused question",
    "category": "Project",
    "difficulty": "Easy | Medium | Hard",
    "tip": "What the interviewer is really probing for"
  }},
  ...
]
""".strip()


_SITUATIONAL_PROMPT = """
You are an experienced behavioural interviewer using the STAR method.
Generate {count} situational interview questions based on this candidate's background.

RESUME:
{resume_text}

Each question should start with "Tell me about a time..." or "Describe a situation..."
and relate to experiences or skills mentioned in the resume.

Return ONLY a JSON array:
[
  {{
    "question": "Full STAR-method question",
    "category": "Situational",
    "difficulty": "Easy | Medium | Hard",
    "tip": "STAR elements the interviewer is looking for"
  }},
  ...
]
""".strip()


_CAREER_PROMPT = """
You are an expert career counsellor and talent advisor.
Based on this resume, provide personalised career suggestions.

RESUME:
{resume_text}

Return ONLY a JSON object:
{{
  "current_level": "Entry | Junior | Mid | Senior | Lead | Principal",
  "recommended_roles": [
    {{"title": "Role title", "reason": "Why this fits", "salary_range": "Approximate range"}}
  ],
  "skill_gaps": ["skill 1", "skill 2"],
  "learning_roadmap": [
    {{"month": "Month 1-3", "focus": "What to learn / build"}}
  ],
  "industry_suggestions": ["industry 1", "industry 2"],
  "career_advice": "2-3 sentences of personalised career advice"
}}
""".strip()


# ── Public generators ─────────────────────────────────────────────────────────

def generate_hr_questions(
    llm,
    resume_text: str,
    job_role: str = "the applied position",
    count: int = 8,
) -> list[dict]:
    """Generate HR / behavioural interview questions."""
    return _generate(llm, _HR_PROMPT, resume_text, job_role, count)


def generate_technical_questions(
    llm,
    resume_text: str,
    job_role: str = "Software Engineer",
    count: int = 10,
) -> list[dict]:
    """Generate technical interview questions."""
    return _generate(llm, _TECHNICAL_PROMPT, resume_text, job_role, count)


def generate_project_questions(
    llm,
    resume_text: str,
    job_role: str = "the applied position",
    count: int = 6,
) -> list[dict]:
    """Generate project-based interview questions."""
    return _generate(llm, _PROJECT_PROMPT, resume_text, job_role, count)


def generate_situational_questions(
    llm,
    resume_text: str,
    job_role: str = "the applied position",
    count: int = 6,
) -> list[dict]:
    """Generate situational / STAR-method questions."""
    return _generate(llm, _SITUATIONAL_PROMPT, resume_text, job_role, count)


def generate_career_suggestions(llm, resume_text: str) -> dict:
    """
    Generate personalised career development suggestions.

    Returns:
        Career dict or {'error': '...'} on failure.
    """
    prompt = _CAREER_PROMPT.format(resume_text=resume_text[:4000])
    raw = invoke_llm(llm, prompt)
    if not raw:
        return {"error": "LLM returned no response."}
    result = parse_json_response(raw)
    if not result:
        return {"error": "Could not parse career suggestions.", "raw": raw[:400]}
    return result


# ── Internal helper ───────────────────────────────────────────────────────────

def _generate(
    llm,
    template: str,
    resume_text: str,
    job_role: str,
    count: int,
) -> list[dict]:
    """
    Fill a prompt template, invoke the LLM, and parse the JSON response.

    Returns a list of question dicts, or [] on failure.
    """
    prompt = template.format(
        resume_text=resume_text[:4000],
        job_role=job_role,
        count=count,
    )

    raw = invoke_llm(llm, prompt)
    if not raw:
        logger.error("LLM returned no response for question generation.")
        return []

    result = parse_json_response(raw)
    if isinstance(result, list):
        return result

    logger.warning("Could not parse question list. Raw snippet: %s", raw[:200])
    return []
