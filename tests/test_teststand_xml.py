import unittest

from testgenai.models.testcase import TestCase, TestStep
from testgenai.teststand.xml_builder import build_teststand_xml


class TestStandXmlTests(unittest.TestCase):
    def test_xml_includes_variables(self) -> None:
        step = TestStep(step_id="S1", action="CallVI MotorTest", expected="Ok", requirement_ids=["REQ-1"])
        tc = TestCase(test_id="TC-1", title="T1", preconditions="", steps=[step], requirements=["REQ-1"])
        tree = build_teststand_xml([tc], step_library=[], vi_library=[{"name": "MotorTest", "path": "C:/vi"}])
        root = tree.getroot()
        self.assertIsNotNone(root.find("Variables"))
        self.assertIsNotNone(root.find("TypeDefinitions"))
        seq = root.find("Sequence")
        self.assertIsNotNone(seq)
        if seq is not None:
            self.assertIsNotNone(seq.find("Variables"))


if __name__ == "__main__":
    unittest.main()
