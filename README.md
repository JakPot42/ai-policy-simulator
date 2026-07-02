# AI Policy Impact Simulator

Paste draft AI policy language (a proposed rule, an executive order section, an
agency directive) and see how it interacts with the real, current regulatory
landscape: four stakeholder personas react, unintended consequences get
flagged, and the draft is scored against NIST AI RMF and the EU AI Act —
**every single claim cites a specific passage from an indexed corpus of real
public documents, and that citation is programmatically checked against the
actual indexed text before it is ever shown as confirmed.**

CLI tool. No web deploy (Render is full at 25/25 — see portfolio CLAUDE.md).

---

## The Problem This Solves

A naive "simulate stakeholder reactions" tool is just four Claude personas
free-associating plausible-sounding paragraphs — the Apollonian/Dionysian
shallow-theater trap this portfolio has hit before (see Agora's Bridge
Builder agent, which had to be constrained to name specific values instead
of vague compromise language). Four fluent paragraphs that *sound* like a
civil rights lawyer and a DoD engineer are worthless if nothing in them is
checkable.

This project's answer: **retrieval, not recall.** Every persona reaction,
every unintended-consequence flag, and every framework score is required to
name a specific `(doc_id, section_id)` from a small, real, indexed corpus and
quote a real substring of it. `citation_verifier.py` then re-checks that
quote against the actual chunk text — not trusting the claim, checking it —
before the finding is displayed as `VERIFIED`. A citation that doesn't check
out is shown as `UNVERIFIED`, not hidden. This is the same discipline this
portfolio already applies elsewhere: OFAC hits are "candidates, not confirmed
violations" (GhostTrace), a fuzzy-matched patient merge is either verified
against ground truth or it isn't (PatientFusion) — Claude proposes, code
disposes.

---

## What It Does

1. **Index** real reference documents first (`corpus/*.txt`, plain text,
   human-readable, checked into this repo) — see "The Corpus" below.
2. **Retrieve** the specific passages relevant to each of four stakeholder
   personas' concerns (BM25, pure Python, same algorithm as Civic RAG and
   Portfolio RAG).
3. **Simulate** each persona's reaction. DEMO_MODE (default) uses a
   deterministic template that quotes the top-matching passage directly —
   zero API keys needed, verified by construction. Live mode lets Claude
   write the reaction narrative and choose which retrieved passages to cite,
   but its citations are re-verified exactly the same way.
4. **Flag** unintended consequences via deterministic keyword triggers (no
   Claude involved at all for this layer) — e.g. a draft mentioning "facial
   recognition" automatically surfaces the EU AI Act's Article 5(1)(e) ban on
   scraped facial-recognition databases, quoted directly from the corpus.
5. **Score** the draft against NIST AI RMF's four functions (GOVERN, MAP,
   MEASURE, MANAGE) and flag EU AI Act high-risk/prohibited-practice
   triggers, every point backed by cited evidence, never a bare number.

---

## The Corpus

| Document | Status | Source |
|---|---|---|
| DoD AI Ethical Principles (2020) | ACTIVE | war.gov / Defense Innovation Board |
| NIST AI Risk Management Framework 1.0 | ACTIVE | nvlpubs.nist.gov, airc.nist.gov |
| EU AI Act, Regulation (EU) 2024/1689, Article 5 (Prohibited Practices) | ACTIVE (applicable since 2025-02-02) | artificialintelligenceact.eu / eur-lex.europa.eu |
| EU AI Act, Regulation (EU) 2024/1689, Article 6 (High-Risk Classification) | ACTIVE | artificialintelligenceact.eu / eur-lex.europa.eu |
| Executive Order 14179, Removing Barriers to American Leadership in Artificial Intelligence | ACTIVE | whitehouse.gov (2025-01-23) |
| Executive Order 14365, Ensuring a National Policy Framework for Artificial Intelligence | ACTIVE | whitehouse.gov (2025-12-11) |
| Executive Order 14110, Safe, Secure, and Trustworthy Development and Use of AI | **REVOKED** (rescinded 2025-01-20) | federalregister.gov — kept only for historical contrast |

Run `python main.py corpus` to see every indexed document and section title —
full transparency on exactly what this tool can and cannot cite.

**Why EO 14110 is in the corpus at all:** it was the operative federal AI
executive order until January 20, 2025, when it was rescinded on President
Trump's first day in office and replaced by EO 14179. Comparing a draft
against both the current regime (EO 14179, EO 14365) and the prior,
rescinded one (EO 14110) is genuinely useful — it shows how a provision would
have fared under the more prescriptive 2023 posture versus the current
deregulatory one. Every citation to EO 14110 is labeled `REVOKED` in the CLI
output; nothing here presents it as current law.

**Honest limitation on corpus fidelity:** the corpus text is a careful,
accurately-sectioned summary of each real document (correct article/section
numbers, correct substantive content, sourced from the documents' official
publication or a specialized reference site like artificialintelligenceact.eu),
not a verbatim character-for-character reproduction of the Official Journal
or Federal Register text. Verify exact statutory language against
eur-lex.europa.eu or federalregister.gov before relying on this tool's output
for a real filing — the same `⚠ VERIFY` discipline this portfolio applies to
every other regulatory citation (ATO Accelerator, CFIUS Screener, Harvest
Horizon).

---

## Citation Enforcement — How It Actually Works

```
draft text
   |
   v
BM25 retrieval (per persona query / per trigger keyword)
   |
   v
Finding{doc_id, section_id, quote, claim}   <-- Claude (live) or a
   |                                             template (DEMO_MODE)
   |                                             proposes this
   v
citation_verifier.verify()                  <-- code checks it
   |
   +--> chunk = index.by_id(doc_id, section_id) exists?  no -> UNVERIFIED
   |
   +--> is `quote` a real (near-)verbatim substring of chunk.text?
          no  -> UNVERIFIED (shown, flagged, not hidden)
          yes -> VERIFIED (doc title / source URL / REVOKED status attached)
```

`consequences.py` and `scoring.py` never ask Claude for a citation at all —
they retrieve the single best-matching chunk and quote it directly, so those
findings are verified by construction. Only `claude_simulator.py`'s live-mode
path produces a citation that didn't come from code, and that's exactly the
path that gets checked.

`tests/test_citation_verifier.py` proves the negative case directly: a
plausible-sounding paraphrase ("The Act bans manipulating people without
their knowledge") that is NOT a real quote from the indexed Article 5(1)(a)
text is asserted to come back `UNVERIFIED`.

---

## Architecture

```
corpus/*.txt              Real reference documents (see table above)
ingest.py                  Parses corpus/*.txt into Chunks with doc_id/section_id/status
bm25_index.py               Pure-Python BM25 retrieval (adapted from Portfolio RAG)
config.py                    Personas, consequence triggers, scoring rubrics -- no logic
models.py                    Finding / PersonaReport dataclasses
citation_verifier.py          THE enforcement layer -- checks a claimed quote against the real chunk
claude_simulator.py            Persona reactions (DEMO_MODE template or live Claude, always re-verified)
consequences.py                 Deterministic trigger-keyword -> cited passage flags
scoring.py                       Deterministic NIST RMF / EU AI Act scoring, cited evidence per point
dashboard.py                      Rich terminal rendering (ASCII-safe)
main.py                            Click CLI
```

---

## Quick Start

```bash
git clone https://github.com/JakPot42/ai-policy-simulator.git
cd ai-policy-simulator
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py demo
```

## Commands

```bash
python main.py corpus                       # list every indexed document/section
python main.py search "facial recognition"  # query the corpus directly
python main.py analyze --text "..."         # analyze pasted draft text
python main.py analyze --file draft.txt     # analyze a draft from a file
python main.py demo                         # two pre-written example drafts, full pipeline
```

DEMO_MODE=True (default) needs zero API keys. Set `DEMO_MODE=False` with a
valid `ANTHROPIC_API_KEY` for live Claude persona narratives — citations are
still verified identically either way.

---

## Tests

```bash
python -m pytest -q
# 69 passed
```

Covers: corpus parsing (including the REVOKED-status handling), BM25
retrieval, the citation verifier (including the negative case — a fabricated
paraphrase must fail verification), deterministic consequence triggers,
deterministic framework scoring, persona simulation in DEMO_MODE, and
end-to-end CLI commands (including the demo's differentiated scores: the
broad/automated draft scores 0/4 on NIST RMF with EU high-risk and
prohibited-practice flags; the narrow/human-reviewed draft scores 4/4 with
no flags).

---

## Honest Limitations

- Corpus text is an accurately-sectioned summary, not a verbatim legal
  reproduction — see "Honest limitation on corpus fidelity" above.
- Four personas is a deliberately small, fixed set; a real OSTP-facing tool
  would need many more (state AG, academic researcher, labor union, etc.)
  and a broader corpus (full Annexes I/III text, more EO sections, agency
  guidance documents).
- BM25 is lexical, not semantic — a persona query using different vocabulary
  than the corpus text will retrieve nothing, same tradeoff GhostTrace
  documented for its hashed bag-of-words embedder.
- The EU AI Act and both current executive orders are evolving; the
  Commission's Article 6 implementation guidelines are due February 2026 and
  will likely refine what counts as high-risk. Re-index when they publish.
- This tool does not, and cannot, replace legal review of an actual policy
  filing.

---

*Every citation traces to a real, dated, sourced document — verify against
the primary source before relying on this for real legal or policy work.*
