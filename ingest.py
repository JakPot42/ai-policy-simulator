"""ingest.py — parses corpus/*.txt into indexed Chunks.

Corpus file format (see corpus/*.txt for real examples):

    DOC_ID: <id>
    TITLE: <title>
    SOURCE_URL: <url>
    STATUS: <ACTIVE|REVOKED>
    DATE: <date>
    NOTE: <optional freeform note>

    [SECTION: <section_id>]
    <section text>

    [SECTION: <section_id>]
    <section text>
    ...

Each [SECTION: ...] block becomes one Chunk. The header fields (doc_id,
title, source_url, status, date) are attached to every chunk from that
file so a citation can always be traced back to a real, dated source with
a known current/revoked status.
"""
from __future__ import annotations

import re
from pathlib import Path

from bm25_index import BM25Index, Chunk

CORPUS_DIR = Path(__file__).parent / "corpus"

_HEADER_FIELDS = ("DOC_ID", "TITLE", "SOURCE_URL", "STATUS", "DATE")
_SECTION_RE = re.compile(r"^\[SECTION:\s*(?P<id>[^\]]+)\]\s*$", re.MULTILINE)


def parse_corpus_file(path: Path) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")

    header: dict[str, str] = {}
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            body_start = i + 1
            continue
        matched = False
        for field in _HEADER_FIELDS:
            if stripped.startswith(f"{field}:"):
                header[field] = stripped[len(field) + 1:].strip()
                matched = True
                break
        if stripped.startswith("NOTE:"):
            matched = True
        if not matched:
            body_start = i
            break

    body = "\n".join(lines[body_start:])

    for required in _HEADER_FIELDS:
        if required not in header:
            raise ValueError(f"{path.name} is missing required header field {required}")

    matches = list(_SECTION_RE.finditer(body))
    chunks: list[Chunk] = []
    for i, m in enumerate(matches):
        section_id = m.group("id").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section_text = body[start:end].strip()
        if not section_text:
            continue
        chunks.append(Chunk(
            chunk_id=0,
            doc_id=header["DOC_ID"],
            title=header["TITLE"],
            section_id=section_id,
            source_url=header["SOURCE_URL"],
            status=header["STATUS"],
            date=header["DATE"],
            text=section_text,
        ))
    return chunks


def build_index(corpus_dir: Path = CORPUS_DIR) -> BM25Index:
    idx = BM25Index()
    chunk_id = 0
    for path in sorted(corpus_dir.glob("*.txt")):
        for chunk in parse_corpus_file(path):
            chunk.chunk_id = chunk_id
            chunk_id += 1
            idx.add_chunk(chunk)
    idx.build()
    return idx
