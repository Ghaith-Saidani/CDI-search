"""Local PDF text extraction and future-parser input structures."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MINIMUM_EXTRACTED_CHARACTERS = 40


class PdfExtractionError(ValueError):
    """Raised when a path cannot be read as a PDF."""


@dataclass
class ExtractedPdfPage:
    page_number: int
    text: str
    section_candidates: list[str]


@dataclass
class PdfExtractionResult:
    source_path: str
    page_count: int
    pages: list[ExtractedPdfPage]
    combined_text: str
    quality: str
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PdfIngestionBundle:
    """Extraction-only handoff for a future CV or job-offer parser."""

    documents: dict[str, PdfExtractionResult]

    def to_dict(self) -> dict:
        return {"mode": "pdf_ingestion", "documents": {kind: result.to_dict() for kind, result in self.documents.items()}}


def _section_candidates(text: str) -> list[str]:
    """Keep likely headings without attempting semantic document parsing."""
    candidates = []
    for line in text.splitlines():
        stripped = " ".join(line.split())
        if not stripped or len(stripped) > 100 or stripped.endswith((".", ",", ";", ":")):
            continue
        is_uppercase = stripped.upper() == stripped and any(character.isalpha() for character in stripped)
        is_numbered = bool(re.match(r"^\d+(?:\.\d+)*\s+\S+", stripped))
        if is_uppercase or is_numbered:
            candidates.append(stripped)
    return candidates


def extract_pdf(path: Path) -> PdfExtractionResult:
    """Extract text page by page without OCR or semantic interpretation."""
    if not path.exists() or not path.is_file():
        raise PdfExtractionError(f"PDF file does not exist: {path}")
    try:
        reader = PdfReader(str(path))
    except (PdfReadError, OSError) as error:
        raise PdfExtractionError(f"Unable to read PDF: {path}") from error

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text(extraction_mode="layout") or ""
        except TypeError:  # Compatibility with older pypdf versions.
            text = page.extract_text() or ""
        text = text.strip()
        pages.append(ExtractedPdfPage(page_number, text, _section_candidates(text)))

    combined_text = "\n\n".join(f"--- PAGE {page.page_number} ---\n{page.text}" for page in pages)
    nonempty_pages = [page for page in pages if page.text]
    character_count = sum(len(page.text) for page in nonempty_pages)
    warnings = []
    if not pages:
        warnings.append("PDF has no pages.")
    empty_pages = len(pages) - len(nonempty_pages)
    if empty_pages:
        warnings.append(f"{empty_pages} page(s) produced no extractable text.")
    if character_count < MINIMUM_EXTRACTED_CHARACTERS:
        warnings.append(f"Extracted text is insufficient ({character_count} characters; minimum is {MINIMUM_EXTRACTED_CHARACTERS}).")
    quality = "sufficient" if not warnings else "insufficient"
    return PdfExtractionResult(str(path), len(pages), pages, combined_text, quality, warnings)


def ingest_pdf_documents(cv_path: Path | None = None, job_path: Path | None = None) -> PdfIngestionBundle:
    documents = {}
    if cv_path is not None:
        documents["cv"] = extract_pdf(cv_path)
    if job_path is not None:
        documents["job"] = extract_pdf(job_path)
    return PdfIngestionBundle(documents)
