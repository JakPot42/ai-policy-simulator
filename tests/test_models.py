"""Tests for models.py."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Finding, PersonaReport


class TestFinding:
    def test_defaults_unverified(self):
        f = Finding(category="persona_reaction", source="x", claim="c",
                    doc_id="d", section_id="s", quote="q")
        assert f.verified is False
        assert f.doc_title == ""
        assert f.source_url == ""
        assert f.status == ""


class TestPersonaReport:
    def test_holds_findings_list(self):
        f = Finding(category="persona_reaction", source="x", claim="c",
                    doc_id="d", section_id="s", quote="q")
        report = PersonaReport(persona_id="p1", persona_name="Persona One", summary="s", findings=[f])
        assert report.findings == [f]
        assert report.persona_name == "Persona One"
