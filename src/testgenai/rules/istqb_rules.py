from __future__ import annotations

from typing import List

from testgenai.models.requirement import Requirement


def suggest_edge_cases(requirements: List[Requirement]) -> List[str]:
    cases: List[str] = []
    for req in requirements:
        cases.append(f"Boundary conditions for {req.req_id}")
        cases.append(f"Invalid input handling for {req.req_id}")
    return cases
