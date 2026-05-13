"""
resume_parser/pdf_extractor.py
Extracts text from uploaded PDF resumes.

Strategy:
1. Try pdfplumber  (best for text-based PDFs — preserves layout well)
2. Fallback to PyMuPDF / fitz  (faster, good for mixed PDFs)
3. Fallback to pdfminer  (pure-python, no binary dependency)

The function returns raw text; cleaning is handled by utils/helpers.py.
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> Optional[str]:
    """
    Extract plain text from a PDF given its raw bytes.

    Args:
        file_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Extracted text string, or None if all extractors fail.
    """
    text = _extract_with_pdfplumber(file_bytes)
    if text and len(text.strip()) > 100:
        logger.info("PDF extracted via pdfplumber (%d chars)", len(text))
        return text

    text = _extract_with_pymupdf(file_bytes)
    if text and len(text.strip()) > 100:
        logger.info("PDF extracted via PyMuPDF (%d chars)", len(text))
        return text

    text = _extract_with_pdfminer(file_bytes)
    if text and len(text.strip()) > 100:
        logger.info("PDF extracted via pdfminer (%d chars)", len(text))
        return text

    logger.error("All PDF extractors failed or returned empty text.")
    return None


# ── Individual extractor implementations ────────────────────────────────────

def _extract_with_pdfplumber(file_bytes: bytes) -> Optional[str]:
    """Use pdfplumber to extract text page-by-page."""
    try:
        import pdfplumber

        pages_text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
        return "\n\n".join(pages_text)

    except ImportError:
        logger.warning("pdfplumber not installed — skipping.")
        return None
    except Exception as exc:
        logger.warning("pdfplumber extraction failed: %s", exc)
        return None


def _extract_with_pymupdf(file_bytes: bytes) -> Optional[str]:
    """Use PyMuPDF (fitz) to extract text."""
    try:
        import fitz  # PyMuPDF

        pages_text = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                pages_text.append(page.get_text())
        return "\n\n".join(pages_text)

    except ImportError:
        logger.warning("PyMuPDF not installed — skipping.")
        return None
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed: %s", exc)
        return None


def _extract_with_pdfminer(file_bytes: bytes) -> Optional[str]:
    """Use pdfminer.six as a pure-python fallback."""
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract

        return pdfminer_extract(io.BytesIO(file_bytes))

    except ImportError:
        logger.warning("pdfminer.six not installed — skipping.")
        return None
    except Exception as exc:
        logger.warning("pdfminer extraction failed: %s", exc)
        return None
