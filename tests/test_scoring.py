"""Tests for scoring.py — deterministic framework scoring."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ingest import build_index
from scoring import score_eu_risk_tier, score_nist_rmf_coverage

INDEX = build_index()


class TestScoreNistRmfCoverage:
    def test_empty_draft_scores_zero(self):
        result = score_nist_rmf_coverage("The sky is blue today.", INDEX)
        assert result["score"] == 0
        assert result["max_score"] == 4

    def test_full_coverage_draft_scores_max(self):
        draft = (
            "An accountability structure and governance policy shall be documented. "
            "The intended use and deployment context shall be scoped. "
            "The system shall undergo testing and evaluation for validity. "
            "Risk treatment and mitigation shall be monitored continuously."
        )
        result = score_nist_rmf_coverage(draft, INDEX)
        assert result["score"] == 4

    def test_partial_coverage(self):
        draft = "The system shall undergo testing and evaluation."
        result = score_nist_rmf_coverage(draft, INDEX)
        assert 0 < result["score"] < 4

    def test_every_finding_is_verified(self):
        draft = "Accountability and testing shall be documented."
        result = score_nist_rmf_coverage(draft, INDEX)
        assert all(f.verified for f in result["findings"])

    def test_returns_one_finding_per_category(self):
        result = score_nist_rmf_coverage("irrelevant text", INDEX)
        assert len(result["findings"]) == 4


class TestScoreEuRiskTier:
    def test_no_domain_keywords_not_high_risk(self):
        result = score_eu_risk_tier("A policy about park maintenance schedules.", INDEX)
        assert result["likely_high_risk"] is False
        assert result["matched_domains"] == []

    def test_employment_domain_triggers_high_risk(self):
        result = score_eu_risk_tier("Used for employment screening decisions.", INDEX)
        assert result["likely_high_risk"] is True
        assert "employment" in result["matched_domains"]

    def test_social_scoring_triggers_prohibited_practice(self):
        result = score_eu_risk_tier("The system assigns a social score to each citizen.", INDEX)
        assert "ART5_1C_SOCIAL_SCORING" in result["likely_prohibited_sections"]

    def test_facial_scraping_triggers_prohibited_practice(self):
        result = score_eu_risk_tier("Builds a facial recognition database by scraping images.", INDEX)
        assert "ART5_1E_FACIAL_SCRAPING" in result["likely_prohibited_sections"]

    def test_clean_draft_has_no_prohibited_hits(self):
        result = score_eu_risk_tier("A narrow pilot for internal document formatting review.", INDEX)
        assert result["likely_prohibited_sections"] == []

    def test_every_finding_is_verified(self):
        result = score_eu_risk_tier(
            "Employment screening with a social score and facial recognition database scraping.", INDEX
        )
        assert len(result["findings"]) > 0
        assert all(f.verified for f in result["findings"])
