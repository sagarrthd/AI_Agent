from __future__ import annotations

from typing import List

from testgenai.models.testcase import TestCase, TestStep
from testgenai.models.requirement import Requirement


class RuleEngine:
    def build_baseline_tests(self, requirements: List[Requirement]) -> List[TestCase]:
        tests: List[TestCase] = []
        for req in requirements:
            step = TestStep(
                step_id=f"STEP-{req.req_id}",
                action=f"Verify {req.title}",
                expected=f"{req.title} is satisfied",
                requirement_ids=[req.req_id],
            )
            tests.append(
                TestCase(
                    test_id=f"TC-{req.req_id}",
                    title=f"Validate {req.title}",
                    preconditions="System initialized",
                    steps=[step],
                    requirements=[req.req_id],
                )
            )
        return tests
