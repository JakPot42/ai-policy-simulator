"""citation_verifier.py — THE enforcement layer.

Every persona reaction and unintended-consequence flag in this project
comes from a Finding with a claimed (doc_id, section_id, quote). This
module is what stops that from being "plausible-sounding roleplay": it
deterministically checks the claimed quote against the actual indexed
corpus text before a Finding is ever displayed as verified. A citation
that doesn't check out is downgraded, not hidden -- the user sees exactly
what failed and why, the same "don't hide the failure mode" discipline as
GhostTrace's OFAC screening (candidates, not confirmed) and PatientFusion's
entity resolution (missed merge visible, not silently dropped).

Verification has two tiers:
  1. The (doc_id, section_id) pair must exist in the index at all.
  2. The claimed quote must be a normalized substring of that chunk's real
     text, or a near-verbatim match (SequenceMatcher ratio >= the
     NEAR_VERBATIM_THRESHOLD) of some substring of it. Paraphrase that
     isn't a substantial verbatim excerpt does NOT verify -- that is the
     whole point.
"""
from __future__ import annotations

import re
from dataclasses import replace
from difflib import SequenceMatcher

from bm25_index import BM25Index
from models import Finding

NEAR_VERBATIM_THRESHOLD = 0.90


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _best_substring_ratio(quote: str, chunk_text: str) -> float:
    """Highest similarity between the quote and any equal-length window of
    the chunk text -- catches near-verbatim quotes that drop punctuation
    or an ellipsis without accepting loose paraphrase."""
    nq, nc = _normalize(quote), _normalize(chunk_text)
    if not nq:
        return 0.0
    if nq in nc:
        return 1.0
    window = len(nq)
    best = 0.0
    step = max(1, window // 4)
    for start in range(0, max(1, len(nc) - window + 1), step):
        candidate = nc[start:start + window]
        ratio = SequenceMatcher(None, nq, candidate).ratio()
        if ratio > best:
            best = ratio
    return best


def verify(finding: Finding, index: BM25Index) -> Finding:
    """Returns a new Finding with `verified` (and enrichment fields)
    set based on a real check against the index -- never mutates in place."""
    chunk = index.by_id(finding.doc_id, finding.section_id)
    if chunk is None:
        return replace(finding, verified=False)

    ratio = _best_substring_ratio(finding.quote, chunk.text)
    verified = ratio >= NEAR_VERBATIM_THRESHOLD

    return replace(
        finding,
        verified=verified,
        doc_title=chunk.title,
        source_url=chunk.source_url,
        status=chunk.status,
    )


def verify_all(findings: list[Finding], index: BM25Index) -> list[Finding]:
    return [verify(f, index) for f in findings]
