"""bm25_index.py — pure-Python BM25 retrieval over the corpus of real AI
policy/governance documents. Adapted from portfolio_rag's bm25_index.py
(same algorithm, same no-ONNX-dependency rationale as GhostTrace's
vector_store.py): this project needs precise, auditable retrieval over a
small, fixed corpus, not a general-purpose embedding model.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: int
    doc_id: str
    title: str
    section_id: str
    source_url: str
    status: str
    date: str
    text: str


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: list[Chunk] = []
        self._doc_tfs: list[Counter] = []
        self._term_df: dict[str, int] = defaultdict(int)
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0
        self._built: bool = False

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-z][a-z0-9]*\b", text.lower())

    def add_chunk(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)
        self._built = False

    def build(self) -> None:
        self._doc_tfs = []
        self._term_df = defaultdict(int)
        total_len = 0

        for chunk in self.chunks:
            combined = f"{chunk.title} {chunk.section_id} {chunk.text}"
            tokens = self._tokenize(combined)
            tf = Counter(tokens)
            self._doc_tfs.append(tf)
            total_len += len(tokens)
            for term in tf:
                self._term_df[term] += 1

        n = len(self.chunks)
        self._avgdl = total_len / n if n else 1.0

        self._idf = {}
        for term, df in self._term_df.items():
            self._idf[term] = math.log((n - df + 0.5) / (df + 0.5) + 1)

        self._built = True

    def by_id(self, doc_id: str, section_id: str) -> Chunk | None:
        for c in self.chunks:
            if c.doc_id == doc_id and c.section_id == section_id:
                return c
        return None

    def search(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        if not self._built:
            self.build()
        if not self.chunks:
            return []

        terms = self._tokenize(query)
        scores: list[tuple[Chunk, float]] = []

        for chunk, tf in zip(self.chunks, self._doc_tfs):
            dl = sum(tf.values())
            score = 0.0
            for term in terms:
                if term not in self._idf:
                    continue
                f = tf.get(term, 0)
                num = f * (self.k1 + 1)
                denom = f + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
                score += self._idf[term] * num / denom
            scores.append((chunk, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [(c, s) for c, s in scores[:top_k] if s > 0]
