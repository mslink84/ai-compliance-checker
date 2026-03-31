"""Plain-text extraction from PDF, DOCX and TXT bytes.

This module has no Streamlit dependency so it can be imported in tests.
"""

import io


def extract_text(file_bytes: bytes, file_name: str) -> str:
    """Extract plain text from PDF, DOCX or TXT bytes."""
    name = file_name.lower()

    if name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")

    if name.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except Exception as e:
            return f"[PDF extraction error: {e}]"

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(para.text for para in doc.paragraphs)
        except Exception as e:
            return f"[DOCX extraction error: {e}]"

    return ""
