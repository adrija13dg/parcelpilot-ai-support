"""FAISS vector search over document chunks."""

from __future__ import annotations

import pickle
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.access import SessionContext, filter_document_metadata
from src.config import CHUNKS_PATH, EMBEDDING_MODEL, FAISS_INDEX_PATH, INDEX_DIR
from src.documents import build_document_chunks


class DocumentIndex:
    def __init__(self) -> None:
        self.model: SentenceTransformer | None = None
        self.index: faiss.Index | None = None
        self.chunks: list[dict] = []

    def _ensure_model(self) -> SentenceTransformer:
        if self.model is None:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        return self.model

    def build(self) -> None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self.chunks = build_document_chunks()
        if not self.chunks:
            raise RuntimeError("No PDF chunks found. Add PDFs to data/ and rebuild the index.")

        model = self._ensure_model()
        texts = [c["text"] for c in self.chunks]
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        faiss.write_index(index, str(FAISS_INDEX_PATH))
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

        self.index = index

    def load(self) -> bool:
        if not FAISS_INDEX_PATH.exists() or not CHUNKS_PATH.exists():
            return False
        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        with open(CHUNKS_PATH, "rb") as f:
            self.chunks = pickle.load(f)
        return True

    def ensure_ready(self) -> None:
        if self.index is not None and self.chunks:
            return
        if not self.load():
            self.build()

    def search(self, query: str, ctx: SessionContext, top_k: int = 5) -> list[dict]:
        self.ensure_ready()
        assert self.index is not None

        model = self._ensure_model()
        q = model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(q)

        scores, indices = self.index.search(q, min(top_k * 3, len(self.chunks)))
        results: list[dict] = []
        seen_sources: set[str] = set()

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self.chunks[idx]
            if not filter_document_metadata(ctx, chunk):
                continue
            source_key = chunk["source_file"]
            if source_key in seen_sources and len(results) >= top_k:
                continue
            seen_sources.add(source_key)
            results.append(
                {
                    "text": chunk["text"],
                    "source_file": chunk["source_file"],
                    "title": chunk["title"],
                    "doc_type": chunk["doc_type"],
                    "status": chunk["status"],
                    "reliability_rank": chunk["reliability_rank"],
                    "page": chunk["page"],
                    "score": float(score),
                }
            )
            if len(results) >= top_k:
                break

        results.sort(key=lambda r: (r["reliability_rank"], -r["score"]))
        return results


@lru_cache(maxsize=1)
def get_document_index() -> DocumentIndex:
    idx = DocumentIndex()
    idx.ensure_ready()
    return idx
