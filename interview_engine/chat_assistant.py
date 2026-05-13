"""
interview_engine/chat_assistant.py
RAG-powered conversational interview assistant.

Workflow:
  1. Retrieve relevant resume chunks from the vector store.
  2. Build a grounded context-aware prompt including chat history.
  3. Stream or invoke the LLM and return the response.
  4. Maintain a rolling chat history (max 20 turns) in session state.
"""

import logging
from models.llm_client import invoke_llm, stream_llm
from models.vector_store import retrieve_context

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 20  # keep last N user+assistant pairs


SYSTEM_PROMPT = """
You are ResumeAI, an expert AI interview coach and career assistant.
You have access to the candidate's resume below.

CANDIDATE RESUME CONTEXT:
---
{resume_context}
---

Your responsibilities:
- Answer questions about the candidate's resume, skills, and experience.
- Help them prepare for interviews by generating questions, mock answers, and feedback.
- Provide career advice tailored to their background.
- If asked to mock-interview, role-play as the interviewer.
- Always be encouraging, professional, and specific to their resume.
- If you don't know something from the resume, say so clearly.

Keep responses concise and actionable. Use bullet points where appropriate.
""".strip()


def build_chat_prompt(
    user_message: str,
    resume_context: str,
    chat_history: list[dict],
) -> str:
    """
    Build a full conversation prompt including system instructions,
    retrieved resume context, and rolling chat history.

    Args:
        user_message:   Latest user input.
        resume_context: Retrieved RAG chunks relevant to the query.
        chat_history:   List of {"role": "user"|"assistant", "content": str}.

    Returns:
        Full prompt string ready for LLM invocation.
    """
    system = SYSTEM_PROMPT.format(resume_context=resume_context[:2000])

    # Format history as a conversation transcript
    history_lines = []
    for turn in chat_history[-MAX_HISTORY_TURNS:]:
        role = "You" if turn["role"] == "user" else "Assistant"
        history_lines.append(f"{role}: {turn['content']}")

    history_text = "\n".join(history_lines)

    prompt = f"""{system}

CONVERSATION HISTORY:
{history_text}

User: {user_message}
Assistant:"""

    return prompt


def chat(
    llm,
    user_message: str,
    retriever,
    chat_history: list[dict],
    stream: bool = False,
):
    """
    Process a user message and return the assistant's response.

    Args:
        llm:           LangChain LLM instance.
        user_message:  The user's latest message.
        retriever:     Vector store retriever (may be None if not built yet).
        chat_history:  Current chat history list.
        stream:        If True, return a generator; else return full string.

    Returns:
        str | Generator: Assistant response text or streaming generator.
    """
    # Retrieve relevant resume context
    context = retrieve_context(retriever, user_message) if retriever else ""

    # Build the full prompt
    prompt = build_chat_prompt(user_message, context, chat_history)

    if stream:
        return stream_llm(llm, prompt)

    response = invoke_llm(llm, prompt)
    return response or "I'm sorry, I couldn't generate a response. Please try again."


def append_to_history(
    chat_history: list[dict],
    role: str,
    content: str,
) -> list[dict]:
    """
    Append a message to the chat history and trim to MAX_HISTORY_TURNS.

    Args:
        chat_history: Existing history list.
        role:         "user" or "assistant".
        content:      Message content.

    Returns:
        Updated history list.
    """
    chat_history.append({"role": role, "content": content})

    # Keep only the last MAX_HISTORY_TURNS pairs (2 messages per turn)
    max_messages = MAX_HISTORY_TURNS * 2
    if len(chat_history) > max_messages:
        chat_history = chat_history[-max_messages:]

    return chat_history


def get_suggested_questions(resume_text: str) -> list[str]:
    """
    Return a static list of suggested starter questions for the chat UI.
    These appear as quick-tap buttons before the user types anything.
    """
    return [
        "What are my top 3 strongest technical skills?",
        "How can I improve my resume summary?",
        "What roles am I best suited for?",
        "Give me 5 mock interview questions for my profile.",
        "What skills should I learn next?",
        "Analyse my project section and suggest improvements.",
        "How does my experience compare to a Senior Engineer?",
        "Help me prepare for a system design interview.",
    ]
