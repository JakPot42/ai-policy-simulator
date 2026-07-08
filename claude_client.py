"""Shared Claude call wrapper (consistency pass from the Federal Policy
Intelligence cluster -- identical logic across comment-analyzer,
ai-policy-simulator, and regulatory-velocity).

One place to make an Anthropic call, with an explicit
`on_error="raise"|"fallback"` parameter so a call site's failure behavior
is declared, not guessed:
  * "raise"    -- wrap any failure in RuntimeError and re-raise.
  * "fallback" -- return `fallback` (default None) instead of raising, so
                  the caller can substitute a deterministic result.

Doctrine preserved from every Claude call site in this portfolio: catch
broad `Exception`, not `anthropic.APIError` -- the SDK raises `TypeError`
(not an APIError subclass) when the API key is missing/empty.

Returns the raw response TEXT; any structured parsing stays at the call
site. Callers pass `model=` to keep their own model constant/env var.
"""
from __future__ import annotations

import os

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

_VALID_ON_ERROR = ("raise", "fallback")


def _make_client(api_key: str | None = None):
    """Construct an Anthropic client. Isolated so tests can monkeypatch it
    without depending on the SDK's internals. Imported lazily."""
    import anthropic

    if api_key is None:
        return anthropic.Anthropic()
    return anthropic.Anthropic(api_key=api_key)


def call_claude(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    on_error: str = "raise",
    fallback: str | None = None,
    api_key: str | None = None,
) -> str | None:
    """Make a single Claude call and return the response text (stripped)."""
    if on_error not in _VALID_ON_ERROR:
        raise ValueError(
            f"on_error must be one of {_VALID_ON_ERROR}, got {on_error!r}"
        )

    try:
        client = _make_client(api_key)
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        msg = client.messages.create(**kwargs)
        return msg.content[0].text.strip()
    except Exception as exc:  # NOT anthropic.APIError -- see module docstring
        if on_error == "fallback":
            return fallback
        raise RuntimeError(f"Claude API error: {exc}") from exc
