"""End-to-end CLI tests. No network calls (DEMO_MODE=True is the default)."""
from __future__ import annotations

import json
import os
import sys

from click.testing import CliRunner

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import cli


def _run(*args):
    runner = CliRunner()
    return runner.invoke(cli, args)


class TestAnalyzeCommand:
    def test_with_text_argument(self):
        result = _run("analyze", "--text", "This system uses facial recognition for employment screening.")
        assert result.exit_code == 0
        assert "Stakeholder Simulation" in result.output
        assert "Unintended Consequences" in result.output
        assert "Framework Scoring" in result.output

    def test_with_file_argument(self, tmp_path):
        draft_file = tmp_path / "draft.txt"
        draft_file.write_text("A narrow pilot with human review and accountability structures.", encoding="utf-8")
        result = _run("analyze", "--file", str(draft_file))
        assert result.exit_code == 0

    def test_no_input_provided_fails_cleanly(self):
        result = _run("analyze")
        assert result.exit_code != 0

    def test_shows_verified_badge(self):
        result = _run("analyze", "--text", "This system uses facial recognition.")
        assert "VERIFIED" in result.output

    def test_no_unverified_findings_on_seeded_drafts(self):
        result = _run("analyze", "--text", "Facial recognition, social score, employment, credit scoring, fully automated.")
        assert "UNVERIFIED" not in result.output


class TestSearchCommand:
    def test_search_returns_results(self):
        result = _run("search", "facial recognition")
        assert result.exit_code == 0
        assert "Corpus Search" in result.output

    def test_search_no_results(self):
        result = _run("search", "zzz_no_such_term_xyz_qqq")
        assert result.exit_code == 0
        assert "No matches" in result.output


class TestCorpusCommand:
    def test_lists_all_documents(self):
        result = _run("corpus")
        assert result.exit_code == 0
        assert "NIST" in result.output or "nist" in result.output.lower()
        assert "REVOKED" in result.output


class TestDemoCommand:
    def test_runs_without_error(self):
        result = _run("demo")
        assert result.exit_code == 0
        assert "Demo 1" in result.output
        assert "Demo 2" in result.output

    def test_demo_has_no_unverified_findings(self):
        result = _run("demo")
        assert "UNVERIFIED" not in result.output

    def test_risky_draft_scores_lower_than_clean_draft(self):
        result = _run("demo")
        assert "NIST RMF coverage score: 0/4" in result.output
        assert "NIST RMF coverage score: 4/4" in result.output


class TestBannerFramingAppearsEverywhere:
    def test_banner_on_every_command(self):
        for args in (("corpus",), ("analyze", "--text", "test draft")):
            result = _run(*args)
            assert "grounded in real, cited regulatory text" in result.output
