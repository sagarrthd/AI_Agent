from __future__ import annotations

from typing import List, Dict, Any


def build_prompt(requirements: List[Any], signals: List[Any], user_prompt: str) -> str:
    req_lines = [
        f"{_get_value(r, 'req_id')}: {_get_value(r, 'description')}" for r in requirements
    ]
    sig_lines = [_get_value(s, "name") for s in signals]
    prompt = [
        "Generate test cases in a strict table:",
        "Test ID | Title | Preconditions | Steps | Expected | Requirement IDs",
        "User instruction:",
        user_prompt,
        "Requirements:",
        "\n".join(req_lines),
        "Signals:",
        ", ".join(sig_lines),
    ]
    return "\n".join([p for p in prompt if p])


def _get_value(item: Any, key: str) -> str:
    if isinstance(item, dict):
        return str(item.get(key, ""))
    return str(getattr(item, key, ""))
