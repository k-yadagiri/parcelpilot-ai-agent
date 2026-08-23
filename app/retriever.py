"""
Lightweight, dependency-light document retriever.

Design choice: we use a TF-IDF + cosine-similarity retriever (scikit-learn)
instead of an embeddings API. This keeps the whole system runnable fully
offline aside from the Anthropic chat completion calls themselves - no
extra API keys, no model downloads, and fully deterministic for testing.
For a corpus of ~6 short policy PDFs this retrieves accurately; a swap to a
vector DB / embeddings retriever would be a drop-in replacement behind the
same `search()` interface if the corpus grew much larger.
"""
from __future__ import annotations

import pickle
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import DOCUMENTS, RAW_PDF_DIR, INDEX_PATH


@dataclass
class Chunk:
    chunk_id: str
    source_file: str
    title: str
    doc_type: str
    status: str
    reliability_rank: int
    effective_date: str
    account_id: Optional[str]
    notes: str
    text: str


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _chunk_text(text: str, max_chars: int = 700, overlap: int = 100) -> List[str]:
    """Chunk on paragraph/section boundaries, falling back to a sliding window."""
    text = re.sub(r"\n{2,}", "\n\n", text.strip())
    # Split on numbered sections ("1. ", "2. ") or blank lines as natural boundaries
    paragraphs = re.split(r"\n(?=\d\.\s)|\n\n", text)
    chunks: List[str] = []
    buf = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(buf) + len(para) + 1 <= max_chars:
            buf = (buf + "\n" + para).strip()
        else:
            if buf:
                chunks.append(buf)
            if len(para) <= max_chars:
                buf = para
            else:
                # hard-wrap very long paragraphs with overlap
                start = 0
                while start < len(para):
                    piece = para[start:start + max_chars]
                    chunks.append(piece)
                    start += max_chars - overlap
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks if chunks else [text]


def build_chunks() -> List[Chunk]:
    chunks: List[Chunk] = []
    for filename, meta in DOCUMENTS.items():
        path = RAW_PDF_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Expected source PDF not found: {path}")
        text = _extract_pdf_text(path)
        pieces = _chunk_text(text)
        for i, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    chunk_id=f"{filename}::{i}",
                    source_file=filename,
                    title=meta["title"],
                    doc_type=meta["doc_type"],
                    status=meta["status"],
                    reliability_rank=meta["reliability_rank"],
                    effective_date=meta["effective_date"],
                    account_id=meta["account_id"],
                    notes=meta["notes"],
                    text=piece,
                )
            )
    return chunks


class DocumentIndex:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self._vectorizer = TfidfVectorizer(stop_words="english")
        corpus = [c.text for c in chunks]
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(
        self,
        query: str,
        k: int = 5,
        allowed_account_id: Optional[str] = "__ANY__",
    ) -> List[Chunk]:
        """
        Return the top-k most relevant chunks for `query`.

        allowed_account_id:
          - "__ANY__" (default): internal/staff context, no account filter.
          - a specific account_id string: customer-facing context. Only
            account-agnostic documents (account_id is None) and that
            customer's own agreement are eligible - other customers'
            agreements are excluded before scoring, so they can never leak
            even if they'd otherwise score highly.
          - None: no customer agreements at all should be shown (defensive
            default if no account context is known yet).
        """
        eligible = self.chunks
        if allowed_account_id != "__ANY__":
            eligible = [
                c for c in self.chunks
                if c.account_id is None or c.account_id == allowed_account_id
            ]
        if not eligible:
            return []

        idxs = [self.chunks.index(c) for c in eligible]
        sub_matrix = self._matrix[idxs]
        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, sub_matrix)[0]
        ranked = sorted(zip(eligible, sims), key=lambda pair: pair[1], reverse=True)
        top = [c for c, score in ranked[:k] if score > 0]
        if not top:
            top = [c for c, _ in ranked[:k]]  # fall back to best-effort if all zero
        return top


_INDEX_CACHE: Optional[DocumentIndex] = None


def get_index(force_rebuild: bool = False) -> DocumentIndex:
    global _INDEX_CACHE
    if _INDEX_CACHE is not None and not force_rebuild:
        return _INDEX_CACHE
    chunks = build_chunks()
    _INDEX_CACHE = DocumentIndex(chunks)
    return _INDEX_CACHE


def format_chunks_for_agent(chunks: List[Chunk]) -> str:
    """Render retrieved chunks with reliability metadata so the model can
    reason about precedence explicitly, instead of treating all text as
    equally authoritative."""
    if not chunks:
        return "No relevant document passages were found."
    blocks = []
    for c in chunks:
        status_flag = "DEPRECATED - DO NOT USE AS CURRENT GUIDANCE" if c.status == "deprecated" else "CURRENT"
        scope = f"account-specific ({c.account_id})" if c.account_id else "applies to all accounts"
        blocks.append(
            f"[Source: {c.title} | type={c.doc_type} | status={status_flag} | "
            f"reliability_rank={c.reliability_rank} (1=highest authority) | "
            f"effective={c.effective_date} | scope={scope}]\n{c.text}"
        )
    return "\n\n---\n\n".join(blocks)
