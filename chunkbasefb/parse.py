from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from docx import Document

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
except ImportError:  # paddle optional
    PaddleOCR = None


_text_exts = {".txt", ".md", ".rst"}


def extract_text(path: Path, *, ocr_backend: Optional[str] = None) -> str:
    suffix = path.suffix.lower()

    if suffix in _text_exts:
        return _read_text_file(path)

    if suffix == ".docx":
        return _read_docx(path)

    if suffix == ".pdf":
        return _read_pdf(path, ocr_backend=ocr_backend)

    logger.debug("Unsupported extension %s; returning empty text", suffix)
    return ""


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read text file %s: %s", path, exc)
        return ""


def _read_docx(path: Path) -> str:
    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to parse DOCX %s: %s", path, exc)
        return ""


def _read_pdf(path: Path, *, ocr_backend: Optional[str]) -> str:
    # Try native text extraction first
    try:
        with fitz.open(path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            if text.strip():
                return text
    except Exception as exc:  # noqa: BLE001
        logger.info("PyMuPDF struggled with %s: %s", path, exc)

    # Fallback to OCR if requested
    if ocr_backend == "paddle":
        return _ocr_pdf_with_paddle(path)

    logger.debug("No OCR backend configured; returning empty text for %s", path)
    return ""


def _ocr_pdf_with_paddle(path: Path) -> str:
    if not PaddleOCR:
        logger.error(
            "PaddleOCR not available. Install paddleocr or run `pip install paddleocr`."
        )
        return ""

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        result = ocr.ocr(str(path))
    except Exception as exc:  # noqa: BLE001
        logger.error("PaddleOCR failed on %s: %s", path, exc)
        return ""

    lines: list[str] = []
    for page in result:
        if not page:
            continue
        for line in page:
            text = line[1][0]
            if text:
                lines.append(text)
    return "\n".join(lines)