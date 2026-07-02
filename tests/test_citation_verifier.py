"""Tests for citation_verifier.py — the enforcement layer. This is the
single most important test file in this project: it proves that a
citation which doesn't actually match the indexed corpus text gets
flagged, not silently trusted."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bm25_index import BM25Index, Chunk
from citation_verifier import verify, verify_all
from models import Finding


def _index_with_chunk(text="Article 5(1)(a) prohibits subliminal manipulation techniques.", status="ACTIVE"):
    idx = BM25Index()
    idx.add_chunk(Chunk(
        chunk_id=0, doc_id="test_doc", title="Test Doc", section_id="ART5",
        source_url="https://example.com/art5", status=status,
        date="2024-01-01", text=text,
    ))
    idx.build()
    return idx


def _finding(doc_id="test_doc", section_id="ART5", quote="Article 5(1)(a) prohibits subliminal manipulation techniques."):
    return Finding(
        category="persona_reaction", source="test_persona", claim="test claim",
        doc_id=doc_id, section_id=section_id, quote=quote,
    )


class TestVerifyExactMatch:
    def test_exact_substring_verifies(self):
        idx = _index_with_chunk()
        result = verify(_finding(quote="prohibits subliminal manipulation"), idx)
        assert result.verified is True

    def test_full_text_quote_verifies(self):
        idx = _index_with_chunk()
        result = verify(_finding(), idx)
        assert result.verified is True

    def test_enriches_metadata_on_verify(self):
        idx = _index_with_chunk()
        result = verify(_finding(), idx)
        assert result.doc_title == "Test Doc"
        assert result.source_url == "https://example.com/art5"
        assert result.status == "ACTIVE"


class TestVerifyRejectsFabrication:
    def test_completely_unrelated_quote_fails(self):
        idx = _index_with_chunk()
        result = verify(_finding(quote="this text does not appear anywhere in the source"), idx)
        assert result.verified is False

    def test_paraphrase_not_verbatim_fails(self):
        idx = _index_with_chunk(text="Article 5(1)(a) prohibits subliminal manipulation techniques.")
        # A plausible-sounding paraphrase, not a real quote -- must NOT verify.
        result = verify(_finding(quote="The Act bans manipulating people without their knowledge."), idx)
        assert result.verified is False

    def test_wrong_doc_id_fails(self):
        idx = _index_with_chunk()
        result = verify(_finding(doc_id="nonexistent_doc"), idx)
        assert result.verified is False

    def test_wrong_section_id_fails(self):
        idx = _index_with_chunk()
        result = verify(_finding(section_id="NONEXISTENT_SECTION"), idx)
        assert result.verified is False

    def test_empty_quote_fails(self):
        idx = _index_with_chunk()
        result = verify(_finding(quote=""), idx)
        assert result.verified is False


class TestVerifyNearVerbatimTolerance:
    def test_whitespace_normalization_still_verifies(self):
        idx = _index_with_chunk(text="Article  5(1)(a)   prohibits subliminal   manipulation techniques.")
        result = verify(_finding(quote="Article 5(1)(a) prohibits subliminal manipulation techniques."), idx)
        assert result.verified is True

    def test_case_insensitive_match_verifies(self):
        idx = _index_with_chunk(text="Article 5(1)(a) PROHIBITS subliminal manipulation techniques.")
        result = verify(_finding(quote="article 5(1)(a) prohibits subliminal manipulation techniques."), idx)
        assert result.verified is True


class TestVerifyPreservesRevokedStatus:
    def test_revoked_status_carried_through(self):
        idx = _index_with_chunk(status="REVOKED (rescinded 2025-01-20)")
        result = verify(_finding(), idx)
        assert result.verified is True
        assert "REVOKED" in result.status


class TestVerifyAll:
    def test_verifies_each_finding_independently(self):
        idx = _index_with_chunk()
        findings = [
            _finding(quote="prohibits subliminal manipulation"),
            _finding(quote="totally fabricated text"),
        ]
        results = verify_all(findings, idx)
        assert results[0].verified is True
        assert results[1].verified is False

    def test_does_not_mutate_original_findings(self):
        idx = _index_with_chunk()
        original = _finding(quote="totally fabricated text")
        assert original.verified is False
        verify(original, idx)
        # original Finding object must be untouched -- verify() returns a copy
        assert original.verified is False

    def test_empty_list_returns_empty(self):
        idx = _index_with_chunk()
        assert verify_all([], idx) == []
