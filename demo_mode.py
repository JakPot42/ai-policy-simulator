"""Shared DEMO_MODE resolution (consistency pass from the Federal Policy
Intelligence cluster -- identical logic across comment-analyzer,
ai-policy-simulator, and regulatory-velocity).

The permissive convention: demo mode is ON by default and only an explicit
false-ish value (`false`/`0`/`no`, case-insensitive) turns it off. This is
what regulatory-velocity already used; it is centralized here so all three
standalone repos and the merged `fpi` CLI agree.
"""
from __future__ import annotations

import os
from typing import Mapping

_DISABLING_VALUES = ("false", "0", "no")


def is_demo_mode(env: Mapping[str, str] | None = None) -> bool:
    """Return True when demo mode is active (the default).

    env is accepted for testability; when omitted, os.environ is read.
    """
    raw = (env if env is not None else os.environ).get("DEMO_MODE", "True")
    return raw.strip().lower() not in _DISABLING_VALUES
