import unittest

from testgenai.models.requirement import Requirement
from testgenai.models.testcase import TestCase, TestStep
from testgenai.mapping.traceability import build_trace_matrix


class MappingTests(unittest.TestCase):
    def test_traceability_matrix(self) -> None:
        reqs = [Requirement(req_id="REQ-1", title="A", description="", req_type="functional")]
        steps = [TestStep(step_id="S1", action="Do", expected="Ok", requirement_ids=["REQ-1"])]
        tests = [TestCase(test_id="TC-1", title="T", preconditions="", steps=steps, requirements=["REQ-1"])]
        matrix = build_trace_matrix(reqs, tests)
        self.assertEqual(matrix["REQ-1"], ["TC-1"])


if __name__ == "__main__":
    unittest.main()
