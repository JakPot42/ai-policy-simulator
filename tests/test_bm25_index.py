"""Tests for bm25_index.py."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bm25_index import BM25Index, Chunk


def _chunk(chunk_id, doc_id, section_id, text, status="ACTIVE"):
    return Chunk(
        chunk_id=chunk_id, doc_id=doc_id, title=f"Title {doc_id}",
        section_id=section_id, source_url="https://example.com",
        status=status, date="2024-01-01", text=text,
    )


class TestBM25Index:
    def test_empty_index_search_returns_empty(self):
        idx = BM25Index()
        assert idx.search("anything") == []

    def test_finds_relevant_chunk(self):
        idx = BM25Index()
        idx.add_chunk(_chunk(0, "d1", "s1", "facial recognition biometric identification"))
        idx.add_chunk(_chunk(1, "d1", "s2", "unrelated agricultural subsidy text"))
        results = idx.search("facial recognition")
        assert results
        assert results[0][0].section_id == "s1"

    def test_no_match_returns_empty(self):
        idx = BM25Index()
        idx.add_chunk(_chunk(0, "d1", "s1", "facial recognition biometric identification"))
        results = idx.search("zzz_no_such_term_xyz")
        assert results == []

    def test_top_k_limits_results(self):
        idx = BM25Index()
        for i in range(10):
            idx.add_chunk(_chunk(i, "d1", f"s{i}", "risk management governance accountability"))
        results = idx.search("risk management", top_k=3)
        assert len(results) == 3

    def test_by_id_finds_exact_chunk(self):
        idx = BM25Index()
        idx.add_chunk(_chunk(0, "d1", "s1", "text one"))
        idx.add_chunk(_chunk(1, "d2", "s2", "text two"))
        found = idx.by_id("d2", "s2")
        assert found is not None
        assert found.text == "text two"

    def test_by_id_returns_none_when_missing(self):
        idx = BM25Index()
        idx.add_chunk(_chunk(0, "d1", "s1", "text one"))
        assert idx.by_id("nope", "nope") is None

    def test_build_is_idempotent_and_auto_called(self):
        idx = BM25Index()
        idx.add_chunk(_chunk(0, "d1", "s1", "risk management"))
        # search() should auto-build even without an explicit build() call
        results = idx.search("risk management")
        assert len(results) == 1
