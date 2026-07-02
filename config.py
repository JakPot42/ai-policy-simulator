"""config.py — personas, trigger-phrase mappings, and scoring rubrics.
No retrieval or Claude-calling logic lives here.
"""
from __future__ import annotations

import os

DEMO_MODE = os.environ.get("DEMO_MODE", "True") == "True"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

TOP_K_PER_QUERY = 3

# ---------------------------------------------------------------------------
# Stakeholder personas. Each persona's `queries` are the search strings run
# against the BM25 index (bm25_index.py / ingest.py) to retrieve the
# specific corpus passages that persona is most likely to invoke -- this is
# what keeps the simulation grounded instead of free-form roleplay: a
# persona can only cite what actually comes back from these queries.
# ---------------------------------------------------------------------------
PERSONAS: list[dict] = [
    {
        "id": "startup_founder",
        "name": "Startup Founder",
        "role": (
            "Founder of a 12-person AI startup building a vertical SaaS product. "
            "Cares about compliance cost, ambiguous high-risk classification "
            "sweeping in small players, and proportionality."
        ),
        "queries": [
            "minimally burdensome innovation policy deregulatory",
            "narrow procedural task exemption not high-risk",
            "small business proportionate compliance burden",
        ],
    },
    {
        "id": "civil_rights_org",
        "name": "Civil Rights Organization",
        "role": (
            "Policy director at a civil liberties nonprofit. Cares about "
            "bias, discrimination, due process, and whether federal "
            "deregulation weakens existing protections against algorithmic harm."
        ),
        "queries": [
            "bias discrimination equitable unintended harm",
            "social scoring biometric categorization profiling",
            "state law civil rights protection preemption",
        ],
    },
    {
        "id": "foreign_government",
        "name": "Foreign Government (EU-aligned)",
        "role": (
            "Official from an EU member-state digital ministry. Cares about "
            "interoperability with the EU AI Act's risk-tiered regime and "
            "regulatory divergence with US policy."
        ),
        "queries": [
            "high-risk classification annex prohibited practices",
            "global AI dominance national policy framework",
            "risk management framework accountability governance",
        ],
    },
    {
        "id": "dod_contractor",
        "name": "DoD / Defense Contractor",
        "role": (
            "Chief engineer at a defense contractor building AI-enabled "
            "systems for DoD. Cares about mission assurance, testing rigor, "
            "traceability, and human accountability for high-consequence systems."
        ),
        "queries": [
            "traceable reliable governable testing assurance",
            "accountability structures risk management measure",
            "human judgment responsible outcomes AI systems",
        ],
    },
]

# ---------------------------------------------------------------------------
# Unintended-consequences trigger phrases. If a draft contains any keyword
# in a trigger's `keywords` list, the corresponding corpus query is run and
# the matched passage is surfaced as a potential unintended interaction --
# always backed by a real retrieved chunk, never invented.
# ---------------------------------------------------------------------------
CONSEQUENCE_TRIGGERS: list[dict] = [
    {
        "id": "facial_recognition",
        "keywords": ["facial recognition", "biometric", "face scraping"],
        "query": "facial recognition biometric scraping prohibited",
        "explanation_template": (
            "If this system is offered in the EU market, {section} may bar it "
            "outright regardless of this draft's domestic treatment."
        ),
    },
    {
        "id": "social_scoring",
        "keywords": ["social score", "trustworthiness score", "citizen score"],
        "query": "social scoring detrimental treatment prohibited",
        "explanation_template": (
            "{section} prohibits exactly this pattern in the EU market -- a "
            "product built to this draft could not be offered there unmodified."
        ),
    },
    {
        "id": "high_risk_domain",
        "keywords": ["employment", "credit scoring", "law enforcement", "critical infrastructure", "education", "border control", "asylum"],
        "query": "annex high-risk domain classification employment credit law enforcement",
        "explanation_template": (
            "{section} automatically classifies AI systems in this domain as "
            "high-risk in the EU, triggering conformity-assessment obligations "
            "this draft may not anticipate."
        ),
    },
    {
        "id": "state_preemption",
        "keywords": ["uniform national standard", "preempt state", "federal standard", "state law"],
        "query": "state law preemption litigation task force funding conditions",
        "explanation_template": (
            "{section} already directs a DOJ task force and funding conditions "
            "aimed at exactly this kind of state/federal conflict."
        ),
    },
    {
        "id": "no_human_oversight",
        "keywords": ["fully automated", "without human review", "autonomous decision"],
        "query": "human judgment responsible governable accountability oversight",
        "explanation_template": (
            "{section} requires exactly the human-accountability layer this "
            "draft language omits."
        ),
    },
    {
        "id": "compliance_burden",
        "keywords": ["shall submit", "shall report", "certification required", "annual audit"],
        "query": "minimally burdensome deregulatory innovation policy",
        "explanation_template": (
            "{section} states a federal policy goal of minimizing exactly this "
            "kind of reporting/certification burden -- a tension worth flagging."
        ),
    },
]

# ---------------------------------------------------------------------------
# Deterministic scoring rubric. Each row maps a corpus category to keywords
# whose presence in the draft counts as "addressed" -- every score comes
# with the specific chunk that justified crediting (or not crediting) it.
# ---------------------------------------------------------------------------
NIST_RMF_SCORING_CATEGORIES: list[dict] = [
    {"function": "GOVERN", "doc_id": "nist_ai_rmf_1_0", "section_id": "GOVERN",
     "keywords": ["accountab", "govern", "polic", "oversight board", "responsib"]},
    {"function": "MAP", "doc_id": "nist_ai_rmf_1_0", "section_id": "MAP",
     "keywords": ["intended use", "deployment setting", "context", "scope"]},
    {"function": "MEASURE", "doc_id": "nist_ai_rmf_1_0", "section_id": "MEASURE",
     "keywords": ["test", "evaluat", "audit", "metric", "valid"]},
    {"function": "MANAGE", "doc_id": "nist_ai_rmf_1_0", "section_id": "MANAGE",
     "keywords": ["mitigat", "remediat", "monitor", "respond", "risk treatment"]},
]

EU_HIGH_RISK_DOMAIN_KEYWORDS = [
    "employment", "credit scoring", "law enforcement", "critical infrastructure",
    "education", "border control", "asylum", "biometric identification",
    "administration of justice",
]
EU_PROHIBITED_PRACTICE_KEYWORDS = {
    "ART5_1C_SOCIAL_SCORING": ["social score", "trustworthiness score", "citizen score"],
    "ART5_1E_FACIAL_SCRAPING": ["facial recognition database", "scrape", "scraping"],
    "ART5_1G_BIOMETRIC_CATEGORIZATION": ["infer race", "infer religion", "infer sexual orientation", "biometric categoriz"],
    "ART5_1H_REALTIME_BIOMETRIC_ID": ["real-time biometric", "live facial recognition"],
}
