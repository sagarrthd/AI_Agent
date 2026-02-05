from __future__ import annotations

from typing import Dict, List


def find_gaps(trace_matrix: Dict[str, List[str]]) -> List[str]:
    return [req_id for req_id, tests in trace_matrix.items() if not tests]
