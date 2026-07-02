"""Tests for ingest.py — corpus file parsing."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ingest import build_index, parse_corpus_file

FIXTURE = """\
DOC_ID: test_doc
TITLE: Test Document
SOURCE_URL: https://example.com/test
STATUS: ACTIVE
DATE: 2024-01-01
NOTE: A note that should be ignored as a section.

[SECTION: FIRST]
This is the first section's text.

[SECTION: SECOND]
This is the second section's text.
It spans multiple lines.
"""


class TestParseCorpusFile:
    def _write(self, tmp_path: Path, content: str) -> Path:
        p = tmp_path / "test.txt"
        p.write_text(content, encoding="utf-8")
        return p

    def test_parses_header_fields(self, tmp_path):
        path = self._write(tmp_path, FIXTURE)
        chunks = parse_corpus_file(path)
        assert all(c.doc_id == "test_doc" for c in chunks)
        assert all(c.title == "Test Document" for c in chunks)
        assert all(c.source_url == "https://example.com/test" for c in chunks)
        assert all(c.status == "ACTIVE" for c in chunks)
        assert all(c.date == "2024-01-01" for c in chunks)

    def test_splits_into_correct_number_of_sections(self, tmp_path):
        path = self._write(tmp_path, FIXTURE)
        chunks = parse_corpus_file(path)
        assert len(chunks) == 2
        assert {c.section_id for c in chunks} == {"FIRST", "SECOND"}

    def test_section_text_preserved(self, tmp_path):
        path = self._write(tmp_path, FIXTURE)
        chunks = parse_corpus_file(path)
        second = next(c for c in chunks if c.section_id == "SECOND")
        assert "spans multiple lines" in second.text

    def test_missing_required_header_raises(self, tmp_path):
        bad = "TITLE: Missing doc id\nSOURCE_URL: x\nSTATUS: ACTIVE\nDATE: 2024-01-01\n\n[SECTION: A]\ntext\n"
        path = self._write(tmp_path, bad)
        try:
            parse_corpus_file(path)
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_empty_section_skipped(self, tmp_path):
        content = FIXTURE + "\n[SECTION: EMPTY]\n\n[SECTION: THIRD]\nreal text\n"
        path = self._write(tmp_path, content)
        chunks = parse_corpus_file(path)
        assert "EMPTY" not in {c.section_id for c in chunks}
        assert "THIRD" in {c.section_id for c in chunks}


class TestBuildIndex:
    def test_indexes_real_corpus_directory(self):
        idx = build_index()
        assert len(idx.chunks) > 20

    def test_all_real_documents_present(self):
        idx = build_index()
        doc_ids = {c.doc_id for c in idx.chunks}
        expected = {
            "dod_ai_principles_2020", "nist_ai_rmf_1_0",
            "eu_ai_act_art5", "eu_ai_act_art6",
            "eo_14179", "eo_14365", "eo_14110",
        }
        assert expected.issubset(doc_ids)

    def test_revoked_document_flagged(self):
        idx = build_index()
        eo_14110_chunks = [c for c in idx.chunks if c.doc_id == "eo_14110"]
        assert all(c.status != "ACTIVE" for c in eo_14110_chunks)

    def test_chunk_ids_are_sequential(self, tmp_path):
        idx = build_index()
        ids = [c.chunk_id for c in idx.chunks]
        assert ids == list(range(len(ids)))
