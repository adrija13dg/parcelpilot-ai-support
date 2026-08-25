"""PDF extraction and chunking."""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from src.config import DATA_DIR, DOCUMENT_REGISTRY


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_pdf_text(path: Path) -> list[tuple[int, str]]:
    doc = pymupdf.open(path)
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(doc, start=1):
        text = normalize_whitespace(page.get_text("text"))
        if text:
            pages.append((i, text))
    doc.close()
    return pages


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def discover_pdfs() -> list[Path]:
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    return pdfs


def build_document_chunks() -> list[dict]:
    chunks: list[dict] = []
    for pdf_path in discover_pdfs():
        filename = pdf_path.name
        registry = DOCUMENT_REGISTRY.get(filename)
        if not registry:
            registry = {
                "title": filename,
                "doc_type": "unknown",
                "version": "unknown",
                "status": "current",
                "customer_scope": "global",
                "reliability_rank": 99,
            }

        pages = extract_pdf_text(pdf_path)
        for page_num, page_text in pages:
            for idx, chunk in enumerate(chunk_text(page_text)):
                chunks.append(
                    {
                        "id": f"{filename}:p{page_num}:c{idx}",
                        "text": chunk,
                        "source_file": filename,
                        "title": registry["title"],
                        "doc_type": registry["doc_type"],
                        "version": registry["version"],
                        "status": registry["status"],
                        "customer_scope": registry["customer_scope"],
                        "reliability_rank": registry["reliability_rank"],
                        "page": page_num,
                    }
                )
    return chunks


def list_available_documents() -> list[dict]:
    available = {p.name for p in discover_pdfs()}
    docs = []
    for filename, meta in DOCUMENT_REGISTRY.items():
        docs.append({"filename": filename, "available": filename in available, **meta})
    return docs
