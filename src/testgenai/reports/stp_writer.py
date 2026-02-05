from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from testgenai.models.testcase import TestCase


def write_stp_output(
    template_path: str,
    output_path: str,
    tests: List[TestCase],
    trace_matrix: Dict[str, List[str]],
    trace_sheet_name: str,
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    template_df = _load_template(template_path)
    data_df = _tests_to_dataframe(tests, template_df)
    trace_df = _trace_to_dataframe(trace_matrix)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data_df.to_excel(writer, index=False, sheet_name="TestPlan")
        trace_df.to_excel(writer, index=False, sheet_name=trace_sheet_name)


def _load_template(path: str) -> Optional[pd.DataFrame]:
    if not path:
        return None
    template_path = Path(path)
    if not template_path.exists():
        return None
    return pd.read_excel(template_path)


def _tests_to_dataframe(
    tests: List[TestCase], template_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    rows = []
    for tc in tests:
        steps = "\n".join(f"{s.step_id}: {s.action}" for s in tc.steps)
        expected = "\n".join(s.expected for s in tc.steps)
        rows.append(
            {
                "Test ID": tc.test_id,
                "Title": tc.title,
                "Description": tc.title,
                "Preconditions": tc.preconditions,
                "Steps": steps,
                "Expected Results": expected,
                "Requirement IDs": ", ".join(tc.requirements),
            }
        )

    df = pd.DataFrame(rows)
    if template_df is None or template_df.empty:
        return df

    normalized = {c.lower().strip(): c for c in template_df.columns}
    mapping = {
        "test id": "Test ID",
        "title": "Title",
        "description": "Description",
        "preconditions": "Preconditions",
        "steps": "Steps",
        "expected": "Expected Results",
        "expected results": "Expected Results",
        "requirement ids": "Requirement IDs",
        "requirements": "Requirement IDs",
    }

    aligned = {}
    for key, default_col in mapping.items():
        if key in normalized:
            aligned[normalized[key]] = df[default_col]

    # Preserve any template columns not mapped by filling empty values.
    for col in template_df.columns:
        if col not in aligned:
            aligned[col] = ""

    return pd.DataFrame(aligned)


def _trace_to_dataframe(trace_matrix: Dict[str, List[str]]) -> pd.DataFrame:
    rows = []
    for req_id, tests in trace_matrix.items():
        rows.append({"Requirement ID": req_id, "Test IDs": ", ".join(tests)})
    return pd.DataFrame(rows)
