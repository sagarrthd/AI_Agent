from __future__ import annotations

from typing import List, Dict


def parse_table_response(text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for line in text.splitlines():
        if "|" not in line or line.strip().startswith("Test ID"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        rows.append(
            {
                "test_id": parts[0],
                "title": parts[1],
                "preconditions": parts[2],
                "steps": parts[3],
                "expected": parts[4],
                "requirements": parts[5],
            }
        )
    return rows
