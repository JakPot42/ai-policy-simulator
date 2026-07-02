"""scoring.py — deterministic scoring against real frameworks, with
explicit cited evidence for every point awarded or withheld.

Like consequences.py, these Findings quote the corpus directly rather than
asking Claude to generate a citation, so they are verified by construction.
Claude never sets a score here -- "Claude extracts, rules decide," the same
doctrine used across this portfolio (CFIUS Screener's TVC score, GhostTrace's
risk engine, PatientFusion's LACE index).
"""
from __future__ import annotations

from bm25_index import BM25Index
from citation_verifier import verify_all
from config import (
    EU_HIGH_RISK_DOMAIN_KEYWORDS,
    EU_PROHIBITED_PRACTICE_KEYWORDS,
    NIST_RMF_SCORING_CATEGORIES,
)
from models import Finding


def score_nist_rmf_coverage(draft_text: str, index: BM25Index) -> dict:
    draft_lower = draft_text.lower()
    findings: list[Finding] = []
    addressed_count = 0

    for cat in NIST_RMF_SCORING_CATEGORIES:
        addressed = any(kw in draft_lower for kw in cat["keywords"])
        chunk = index.by_id(cat["doc_id"], cat["section_id"])
        if chunk is None:
            continue
        if addressed:
            addressed_count += 1
            claim = f"Draft language maps to NIST AI RMF {cat['function']} -- matched keyword(s) suggest this function is addressed."
        else:
            claim = f"Draft does not clearly address NIST AI RMF {cat['function']}: {chunk.text.split('.')[0]}."
        findings.append(Finding(
            category="score_evidence",
            source=f"nist_rmf_{cat['function'].lower()}",
            claim=claim,
            doc_id=chunk.doc_id,
            section_id=chunk.section_id,
            quote=chunk.text,
        ))

    return {
        "score": addressed_count,
        "max_score": len(NIST_RMF_SCORING_CATEGORIES),
        "findings": verify_all(findings, index),
    }


def score_eu_risk_tier(draft_text: str, index: BM25Index) -> dict:
    draft_lower = draft_text.lower()
    findings: list[Finding] = []

    matched_domains = [kw for kw in EU_HIGH_RISK_DOMAIN_KEYWORDS if kw in draft_lower]
    likely_high_risk = bool(matched_domains)
    if likely_high_risk:
        chunk = index.by_id("eu_ai_act_art6", "ART6_2_ANNEX_III_DOMAINS")
        if chunk is not None:
            findings.append(Finding(
                category="score_evidence",
                source="eu_high_risk_domain",
                claim=(
                    f"Draft references domain(s) {matched_domains} -- these fall "
                    f"within Annex III use cases under EU AI Act Article 6(2), "
                    f"which would classify a covered system as high-risk."
                ),
                doc_id=chunk.doc_id,
                section_id=chunk.section_id,
                quote=chunk.text,
            ))

    prohibited_hits = []
    for section_id, keywords in EU_PROHIBITED_PRACTICE_KEYWORDS.items():
        if any(kw in draft_lower for kw in keywords):
            chunk = index.by_id("eu_ai_act_art5", section_id)
            if chunk is None:
                continue
            prohibited_hits.append(section_id)
            findings.append(Finding(
                category="score_evidence",
                source="eu_prohibited_practice",
                claim=(
                    f"Draft language resembles a practice prohibited outright by "
                    f"EU AI Act {section_id} -- not just high-risk, but banned."
                ),
                doc_id=chunk.doc_id,
                section_id=chunk.section_id,
                quote=chunk.text,
            ))

    return {
        "likely_high_risk": likely_high_risk,
        "matched_domains": matched_domains,
        "likely_prohibited_sections": prohibited_hits,
        "findings": verify_all(findings, index),
    }
