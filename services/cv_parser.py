"""
CV/Resume and Job Description parser.
Extracts text from PDF and DOCX files.
"""

import io
import logging

logger = logging.getLogger(__name__)


def extract_text(file_storage, filename):
    """
    Extract text from an uploaded file based on its extension.
    Supports PDF and DOCX formats.
    Returns the extracted text string.
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        return _parse_pdf(file_storage)
    elif filename_lower.endswith(".docx"):
        return _parse_docx(file_storage)
    elif filename_lower.endswith(".txt"):
        return file_storage.read().decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file format: {filename}. Please upload PDF, DOCX, or TXT.")


def _parse_pdf(file_storage):
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_storage.read()))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        text = "\n".join(text_parts).strip()
        if not text:
            raise ValueError("Could not extract text from PDF. The file may be image-based.")
        
        logger.info("Extracted %d characters from PDF (%d pages)", len(text), len(reader.pages))
        return text
    except ImportError:
        raise RuntimeError("PyPDF2 is required for PDF parsing. Install it with: pip install PyPDF2")


def _parse_docx(file_storage):
    """Extract text from a DOCX file."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_storage.read()))
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        text = "\n".join(text_parts).strip()
        if not text:
            raise ValueError("Could not extract text from DOCX. The file may be empty.")

        logger.info("Extracted %d characters from DOCX", len(text))
        return text
    except ImportError:
        raise RuntimeError("python-docx is required for DOCX parsing. Install it with: pip install python-docx")
