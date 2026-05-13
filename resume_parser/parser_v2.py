from pypdf import PdfReader
import re

SKILLS_DB = [
    "python",
    "machine learning",
    "nlp",
    "streamlit",
    "langchain",
    "sql",
    "pytorch",
    "tensorflow"
]

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text

def extract_email(text):
    match = re.findall(r'\\S+@\\S+', text)
    return match[0] if match else None

def extract_phone(text):
    match = re.findall(r'\\+?\\d[\\d -]{8,12}\\d', text)
    return match[0] if match else None

def extract_skills(text):
    found_skills = []

    text = text.lower()

    for skill in SKILLS_DB:
        if skill in text:
            found_skills.append(skill)

    return found_skills

def parse_resume(pdf_file):

    text = extract_text_from_pdf(pdf_file)

    data = {
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "raw_text": text[:1000]
    }

    return data