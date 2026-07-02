"""models.py — shared dataclasses. No logic."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Finding:
    """A single grounded claim: some text asserting how a draft interacts
    with a real framework, tied to a specific retrieved passage. `verified`
    is set by citation_verifier.py -- never trust a Finding's citation
    before it has been through verification."""

    category: str          # "persona_reaction" | "unintended_consequence" | "score_evidence"
    source: str             # persona id, trigger id, or scoring function name
    claim: str               # the natural-language claim/reaction text
    doc_id: str
    section_id: str
    quote: str               # the text claimed to be quoted from the source chunk
    verified: bool = False
    doc_title: str = ""
    source_url: str = ""
    status: str = ""


@dataclass
class PersonaReport:
    persona_id: str
    persona_name: str
    summary: str
    findings: list[Finding]
