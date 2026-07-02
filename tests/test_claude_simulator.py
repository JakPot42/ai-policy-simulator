"""Tests for claude_simulator.py — DEMO_MODE path only (no network calls,
consistent with every other Claude-calling project in this portfolio)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from claude_simulator import simulate_all, simulate_persona
from config import PERSONAS
from ingest import build_index

INDEX = build_index()
DRAFT = "This draft requires facial recognition for law enforcement identity verification."


class TestSimulatePersona:
    def test_returns_persona_report(self):
        persona = PERSONAS[0]
        report = simulate_persona(persona, DRAFT, INDEX)
        assert report.persona_id == persona["id"]
        assert report.persona_name == persona["name"]

    def test_findings_are_verified(self):
        persona = PERSONAS[0]
        report = simulate_persona(persona, DRAFT, INDEX)
        assert len(report.findings) > 0
        assert all(f.verified for f in report.findings)

    def test_every_finding_cites_a_real_doc_and_section(self):
        persona = PERSONAS[0]
        report = simulate_persona(persona, DRAFT, INDEX)
        for f in report.findings:
            assert INDEX.by_id(f.doc_id, f.section_id) is not None

    def test_all_four_personas_produce_reports(self):
        for persona in PERSONAS:
            report = simulate_persona(persona, DRAFT, INDEX)
            assert report.findings


class TestSimulateAll:
    def test_returns_one_report_per_persona(self):
        reports = simulate_all(DRAFT, INDEX, PERSONAS)
        assert len(reports) == len(PERSONAS)
        assert {r.persona_id for r in reports} == {p["id"] for p in PERSONAS}

    def test_no_network_call_in_demo_mode(self):
        # If this test hangs or raises a network error, DEMO_MODE routing is broken.
        reports = simulate_all(DRAFT, INDEX, PERSONAS)
        assert all(r.findings for r in reports)
