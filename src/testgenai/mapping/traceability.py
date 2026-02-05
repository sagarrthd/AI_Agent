from __future__ import annotations

from typing import Dict, List

from testgenai.models.testcase import TestCase
from testgenai.models.requirement import Requirement


def build_trace_matrix(
    requirements: List[Requirement], tests: List[TestCase]
) -> Dict[str, List[str]]:
    matrix = {r.req_id: [] for r in requirements}
    for tc in tests:
        for req_id in tc.requirements:
            matrix.setdefault(req_id, []).append(tc.test_id)
    return matrix
