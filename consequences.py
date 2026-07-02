"""consequences.py — deterministic unintended-consequence flags.

Unlike persona reactions (claude_simulator.py), these flags never involve
Claude at all: a trigger keyword found in the draft selects a corpus query,
the best-scoring chunk is quoted directly (not paraphrased), so every flag
here is verified by construction -- there's nothing for citation_verifier
to catch because the quote IS the chunk text.
"""
from __future__ import annotations

from bm25_index import BM25Index
from citation_verifier import verify_all
from config import CONSEQUENCE_TRIGGERS
from models import Finding


def find_unintended_consequences(draft_text: str, index: BM25Index) -> list[Finding]:
    draft_lower = draft_text.lower()
    findings: list[Finding] = []

    for trigger in CONSEQUENCE_TRIGGERS:
        if not any(kw in draft_lower for kw in trigger["keywords"]):
            continue
        results = index.search(trigger["query"], top_k=1)
        if not results:
            continue
        chunk, _score = results[0]
        section_label = f"{chunk.title}, {chunk.section_id}"
        claim = trigger["explanation_template"].format(section=section_label)
        findings.append(Finding(
            category="unintended_consequence",
            source=trigger["id"],
            claim=claim,
            doc_id=chunk.doc_id,
            section_id=chunk.section_id,
            quote=chunk.text,
        ))

    return verify_all(findings, index)
