import unittest

from testgenai.models.requirement import Requirement
from testgenai.models.signal import Signal
from testgenai.scenarios.generator import build_scenarios


class ScenarioTests(unittest.TestCase):
    def test_build_scenarios(self) -> None:
        reqs = [Requirement(req_id="REQ-1", title="A", description="D", req_type="functional")]
        signals = [Signal(name="S1", unit="", min_val=0.0, max_val=1.0, data_type="", source="A2L")]
        scenarios = build_scenarios(reqs, signals)
        self.assertGreaterEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].requirement_ids, ["REQ-1"])


if __name__ == "__main__":
    unittest.main()
