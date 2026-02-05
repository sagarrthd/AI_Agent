import tempfile
import unittest
from pathlib import Path

from testgenai.models.testcase import TestCase, TestStep
from testgenai.reports.stp_writer import write_stp_output


class StpWriterTests(unittest.TestCase):
    def test_write_stp_output(self) -> None:
        step = TestStep(step_id="S1", action="Do", expected="Ok", requirement_ids=["REQ-1"])
        test = TestCase(
            test_id="TC-1",
            title="Title",
            preconditions="",
            steps=[step],
            requirements=["REQ-1"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "out.xlsx"
            write_stp_output("", str(out_path), [test], {"REQ-1": ["TC-1"]}, "Trace")
            self.assertTrue(out_path.exists())


if __name__ == "__main__":
    unittest.main()
