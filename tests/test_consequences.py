"""Tests for consequences.py — deterministic trigger matching."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from consequences import find_unintended_consequences
from ingest import build_index

INDEX = build_index()


class TestFindUnintendedConsequences:
    def test_facial_recognition_trigger_matches(self):
        findings = find_unintended_consequences(
            "This system uses facial recognition to verify identity.", INDEX
        )
        assert any(f.source == "facial_recognition" for f in findings)

    def test_no_trigger_keywords_no_findings(self):
        findings = find_unintended_consequences(
            "This is a policy about agricultural subsidies for wheat farmers.", INDEX
        )
        assert findings == []

    def test_high_risk_domain_trigger_matches_employment(self):
        findings = find_unintended_consequences(
            "The system will be used for employment screening decisions.", INDEX
        )
        assert any(f.source == "high_risk_domain" for f in findings)

    def test_state_preemption_trigger_matches(self):
        findings = find_unintended_consequences(
            "This rule establishes a uniform national standard for AI.", INDEX
        )
        assert any(f.source == "state_preemption" for f in findings)

    def test_no_human_oversight_trigger_matches(self):
        findings = find_unintended_consequences(
            "Decisions shall be made through fully automated processing without human review.", INDEX
        )
        assert any(f.source == "no_human_oversight" for f in findings)

    def test_all_returned_findings_are_verified(self):
        findings = find_unintended_consequences(
            "Facial recognition and social score systems for employment and credit scoring, "
            "fully automated, uniform national standard, shall submit annual reports.",
            INDEX,
        )
        assert len(findings) > 0
        assert all(f.verified for f in findings)

    def test_multiple_triggers_can_fire_simultaneously(self):
        findings = find_unintended_consequences(
            "Facial recognition combined with a social score for employment eligibility, "
            "fully automated, part of a uniform national standard, shall submit certification required.",
            INDEX,
        )
        sources = {f.source for f in findings}
        assert len(sources) >= 3

    def test_case_insensitive_matching(self):
        findings = find_unintended_consequences("FACIAL RECOGNITION system", INDEX)
        assert any(f.source == "facial_recognition" for f in findings)
