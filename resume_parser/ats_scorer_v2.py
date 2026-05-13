from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import re

SKILLS_DB = [
    "python",
    "machine learning",
    "deep learning",
    "nlp",
    "streamlit",
    "langchain",
    "tensorflow",
    "pytorch",
    "sql",
    "django",
    "javascript",
    "data analysis",
]

model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_keywords(text):
    text = text.lower()

    found_keywords = []

    for skill in SKILLS_DB:
        if skill in text:
            found_keywords.append(skill)

    return list(set(found_keywords))


def calculate_tfidf_similarity(resume_text, jd_text):

    documents = [resume_text, jd_text]

    tfidf = TfidfVectorizer()

    tfidf_matrix = tfidf.fit_transform(documents)

    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:2]
    )[0][0]

    return round(similarity * 100, 2)


def calculate_embedding_similarity(resume_text, jd_text):

    embeddings = model.encode(
        [resume_text, jd_text],
        convert_to_tensor=True
    )

    similarity = util.cos_sim(
        embeddings[0],
        embeddings[1]
    )

    return round(float(similarity[0][0]) * 100, 2)


def calculate_ats_score(resume_text, jd_text):

    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)

    matching_skills = list(
        set(resume_keywords).intersection(set(jd_keywords))
    )

    missing_skills = list(
        set(jd_keywords).difference(set(resume_keywords))
    )

    keyword_score = (
        len(matching_skills) / len(jd_keywords) * 100
        if jd_keywords else 0
    )

    tfidf_score = calculate_tfidf_similarity(
        resume_text,
        jd_text
    )

    embedding_score = calculate_embedding_similarity(
        resume_text,
        jd_text
    )

    final_score = round(
        (keyword_score * 0.4) +
        (tfidf_score * 0.3) +
        (embedding_score * 0.3),
        2
    )

    suggestions = []

    if missing_skills:
        suggestions.append(
            f"Add missing skills: {', '.join(missing_skills)}"
        )

    if final_score < 60:
        suggestions.append(
            "Improve resume relevance for this job description."
        )

    return {
        "ATS Score": final_score,
        "Matching Skills": matching_skills,
        "Missing Skills": missing_skills,
        "TF-IDF Similarity": tfidf_score,
        "Embedding Similarity": embedding_score,
        "Suggestions": suggestions
    }