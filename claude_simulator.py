"""claude_simulator.py — stakeholder persona simulation.

Claude's job here is narrow and structural, not conversational: given a
draft and a fixed set of retrieved corpus passages, it may point out
which of those SPECIFIC passages a persona would react to and how, but
every citation it produces still passes through citation_verifier.py
before being trusted or displayed. This is the "Claude extracts, rules
decide" doctrine applied to citation integrity -- Claude is not allowed
to be the last word on whether its own citation is real.

DEMO_MODE (default) skips Claude entirely: a deterministic template picks
the persona's top-matching retrieved passage per query and quotes it
directly, so it is verified by construction (matches consequences.py's
approach). This keeps the CLI runnable with zero API keys, like every
other project in this portfolio.
"""
from __future__ import annotations

import json

from bm25_index import BM25Index, Chunk
from citation_verifier import verify_all
from config import CLAUDE_MODEL, DEMO_MODE, TOP_K_PER_QUERY
from models import Finding, PersonaReport

_SYSTEM_PROMPT = """\
You are simulating how a specific stakeholder would react to a draft AI \
policy provision, using ONLY the reference passages provided below. You \
may not use outside knowledge of any regulation not shown here.

Rules:
1. Every finding MUST cite one of the provided passages by its exact \
doc_id and section_id.
2. The "quote" field must be a real substring of that passage's text -- \
copy it, do not paraphrase it.
3. If none of the provided passages are relevant to a point you want to \
make, do not make that point. Do not invent a citation.
4. Output strict JSON only, matching this schema, no prose outside the JSON:
{"summary": "1-2 sentence persona reaction", "findings": [
  {"claim": "...", "doc_id": "...", "section_id": "...", "quote": "..."}
]}
"""


def _retrieve_for_persona(persona: dict, index: BM25Index) -> list[Chunk]:
    seen: set[tuple[str, str]] = set()
    pool: list[Chunk] = []
    for query in persona["queries"]:
        for chunk, _score in index.search(query, top_k=TOP_K_PER_QUERY):
            key = (chunk.doc_id, chunk.section_id)
            if key in seen:
                continue
            seen.add(key)
            pool.append(chunk)
    return pool


def _demo_react(persona: dict, draft_text: str, index: BM25Index) -> PersonaReport:
    findings: list[Finding] = []
    for query in persona["queries"]:
        results = index.search(query, top_k=1)
        if not results:
            continue
        chunk, _score = results[0]
        status_note = " (NOTE: this document is REVOKED -- historical contrast only)" if chunk.status != "ACTIVE" else ""
        claim = (
            f"As {persona['name']}, the passage most relevant to this draft's "
            f"treatment of \"{query}\" is {chunk.title}, {chunk.section_id}{status_note}."
        )
        findings.append(Finding(
            category="persona_reaction",
            source=persona["id"],
            claim=claim,
            doc_id=chunk.doc_id,
            section_id=chunk.section_id,
            quote=chunk.text,
        ))
    summary = (
        f"{persona['name']} ({persona['role']}) -- DEMO_MODE deterministic "
        f"match against the indexed corpus; see cited passages below."
    )
    return PersonaReport(persona["id"], persona["name"], summary, findings)


def _claude_react(persona: dict, draft_text: str, index: BM25Index) -> PersonaReport:
    try:
        import anthropic
        client = anthropic.Anthropic()

        pool = _retrieve_for_persona(persona, index)
        if not pool:
            return _demo_react(persona, draft_text, index)

        context_blocks = [
            f"[doc_id={c.doc_id} section_id={c.section_id} status={c.status}]\n"
            f"{c.title}\n{c.text}"
            for c in pool
        ]
        context = "\n\n---\n\n".join(context_blocks)

        user_prompt = (
            f"Persona: {persona['name']} -- {persona['role']}\n\n"
            f"Reference passages:\n\n{context}\n\n"
            f"Draft AI policy language:\n\n{draft_text}"
        )
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        data = json.loads(msg.content[0].text.strip())
        findings = [
            Finding(
                category="persona_reaction",
                source=persona["id"],
                claim=f.get("claim", ""),
                doc_id=f.get("doc_id", ""),
                section_id=f.get("section_id", ""),
                quote=f.get("quote", ""),
            )
            for f in data.get("findings", [])
        ]
        return PersonaReport(persona["id"], persona["name"], data.get("summary", ""), findings)
    except Exception:
        # Same doctrine as every Claude call site in this portfolio: catch
        # Exception (the SDK raises TypeError on a missing key, not
        # anthropic.APIError), fall back rather than crash.
        return _demo_react(persona, draft_text, index)


def simulate_persona(persona: dict, draft_text: str, index: BM25Index) -> PersonaReport:
    report = _demo_react(persona, draft_text, index) if DEMO_MODE else _claude_react(persona, draft_text, index)
    report.findings = verify_all(report.findings, index)
    return report


def simulate_all(draft_text: str, index: BM25Index, personas: list[dict]) -> list[PersonaReport]:
    return [simulate_persona(p, draft_text, index) for p in personas]
