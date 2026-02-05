import unittest

from testgenai.models.requirement import Requirement
from testgenai.rules.rule_engine import RuleEngine


class RuleEngineTests(unittest.TestCase):
    def test_build_baseline_tests(self) -> None:
        reqs = [Requirement(req_id="REQ-1", title="Feature A", description="Desc", req_type="functional")]
        tests = RuleEngine().build_baseline_tests(reqs)
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0].requirements, ["REQ-1"])


if __name__ == "__main__":
    unittest.main()
