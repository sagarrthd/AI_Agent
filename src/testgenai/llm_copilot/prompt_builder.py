from __future__ import annotations

from typing import Any, Dict, List


def build_prompt(
    requirements: List[Any],
    signals: List[Any],
    user_prompt: str,
    template_schema: Dict[str, Any] | None = None,
    code_context: str = "",
) -> str:
    req_lines = [
        f"- **{_get_value(r, 'req_id')}**: {_get_value(r, 'description')}" for r in requirements
    ]
    sig_lines = [_get_value(s, "name") for s in signals]

    persona = (
        "You are a Senior Automotive Test Engineer with 20 years of experience in ISO 26262 Functional Safety. "
        "Your job is to write incredibly detailed, high-coverage test cases for the following requirements."
    )

    task = (
        "Create a comprehensive Test Plan in a strict Markdown table format. "
        "For each requirement, generate multiple test cases covering:\n"
        "1. **Nominal/Happy Path**: Standard operation.\n"
        "2. **Boundary/Edge Cases**: Min/Max values, limits.\n"
        "3. **Failure/Robustness**: Invalid inputs, timeout scenarios, fault injection.\n\n"
        "Format the output EXACTLY as this Markdown table (no other text):\n"
        "| Test ID | Title | Preconditions | Steps | Expected Results | Requirement IDs |\n"
        "|---------|-------|---------------|-------|------------------|-----------------|"
    )

    template_hint = ""
    if template_schema and template_schema.get("columns"):
        template_hint = (
            "The STP Excel template was analyzed. Use naming aligned to these columns: "
            f"{', '.join(template_schema['columns'])}."
        )

    signals_hint = ""
    if sig_lines:
        signals_hint = f"Available A2L signals (sample): {', '.join(sig_lines[:30])}"

    code_hint = ""
    if code_context:
        code_hint = f"Code-derived constraints/functions:\n{code_context[:4000]}"

    full_prompt = [
        persona,
        "\n---",
        "## REQUIREMENTS:",
        "\n".join(req_lines),
        "\n---",
        "## INSTRUCTIONS:",
        task,
        template_hint,
        signals_hint,
        code_hint,
        "## RULES:",
        "- 'Steps' and 'Expected Results' must be numbered lists (1. 2. 3.).",
        "- 'Preconditions' should be specific (e.g. 'Ignition ON', 'Speed > 100km/h').",
        "- 'Test ID' should be unique (e.g. TC-001, TC-002).",
        "- strictly map 'Requirement IDs' to the input list.",
        "- Do not include chatter or explanations. Just the table.",
        user_prompt,
    ]

    return "\n".join([p for p in full_prompt if p])


def _get_value(item: Any, key: str) -> str:
    if isinstance(item, dict):
        return str(item.get(key, ""))
    return str(getattr(item, key, ""))
