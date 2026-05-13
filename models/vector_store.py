"""
models/vector_store.py
Builds and queries a vector store (FAISS or ChromaDB) over resume chunks.

Used by the chat assistant to perform Retrieval-Augmented Generation (RAG):
  1. Embed resume text chunks with Sentence Transformers.
  2. Store vectors in FAISS or ChromaDB.
  3. At query time, retrieve the top-k most relevant chunks.
  4. Feed those chunks as context to the LLM.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def build_vector_store(chunks: list[str], config: dict):
    """
    Embed text chunks and build an in-memory vector store.

    Args:
        chunks: List of text chunk strings (from utils/helpers.chunk_text).
        config: App config dict (contains embedding_model, vector_store preference).

    Returns:
        A retriever object exposing a .get_relevant_documents(query) method,
        or None if building fails.
    """
    backend = config.get("vector_store", "faiss").lower()

    try:
        embeddings = _get_embeddings(config)
        if embeddings is None:
            return None

        if backend == "faiss":
            return _build_faiss(chunks, embeddings)
        else:
            return _build_chroma(chunks, embeddings)

    except Exception as exc:
        logger.error("Vector store build failed: %s", exc)
        return None


def _get_embeddings(config: dict):
    """
    Load the Sentence Transformers embedding model via LangChain.
    Returns a HuggingFaceEmbeddings instance.
    """
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        model_name = config.get("embedding_model", "all-MiniLM-L6-v2")
        logger.info("Loading embedding model: %s", model_name)

        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except ImportError:
        logger.error(
            "langchain-community or sentence-transformers not installed. "
            "Run: pip install langchain-community sentence-transformers"
        )
        return None
    except Exception as exc:
        logger.error("Embedding model load failed: %s", exc)
        return None


def _build_faiss(chunks: list[str], embeddings) -> Optional[object]:
    """Build a FAISS vector store and return a retriever."""
    try:
        from langchain_community.vectorstores import FAISS

        store = FAISS.from_texts(chunks, embedding=embeddings)
        retriever = store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4},
        )
        logger.info("FAISS vector store built with %d chunks.", len(chunks))
        return retriever

    except ImportError:
        logger.error("faiss-cpu not installed. Run: pip install faiss-cpu")
        return None
    except Exception as exc:
        logger.error("FAISS build failed: %s", exc)
        return None


def _build_chroma(chunks: list[str], embeddings) -> Optional[object]:
    """Build an in-memory Chroma vector store and return a retriever."""
    try:
        from langchain_community.vectorstores import Chroma

        store = Chroma.from_texts(
            chunks,
            embedding=embeddings,
            collection_name="resume_chunks",
        )
        retriever = store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4},
        )
        logger.info("Chroma vector store built with %d chunks.", len(chunks))
        return retriever

    except ImportError:
        logger.error("chromadb not installed. Run: pip install chromadb")
        return None
    except Exception as exc:
        logger.error("Chroma build failed: %s", exc)
        return None


def retrieve_context(retriever, query: str) -> str:
    """
    Retrieve relevant resume chunks for a given query.

    Args:
        retriever: LangChain retriever from build_vector_store().
        query:     User question string.

    Returns:
        Concatenated context string to inject into LLM prompt.
    """
    if retriever is None:
        return ""
    try:
        docs = retriever.get_relevant_documents(query)
        return "\n\n".join(doc.page_content for doc in docs)
    except Exception as exc:
        logger.warning("Retrieval failed: %s", exc)
        return ""
