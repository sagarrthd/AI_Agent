import tempfile
import unittest
from pathlib import Path

from testgenai.ingestion.doc_parser import load_requirements_from_sources


class DocParserTests(unittest.TestCase):
    def test_load_requirements_from_multiple_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req_file = Path(tmp) / "req.txt"
            code_file = Path(tmp) / "logic.c"

            req_file.write_text("REQ-10: Engine shall stop on fault\nBattery shall be monitored", encoding="utf-8")
            code_file.write_text(
                """
                // watchdog timeout must trigger safe state
                #define MAX_RPM 6500
                int compute_speed(int rpm) { return rpm / 2; }
                """,
                encoding="utf-8",
            )

            requirements = load_requirements_from_sources(str(req_file), [str(code_file)])

            descriptions = [r["description"] for r in requirements]
            self.assertIn("Engine shall stop on fault", descriptions)
            self.assertTrue(any("Function behavior: compute_speed" in d for d in descriptions))
            self.assertTrue(any("Constraint: MAX_RPM" in d for d in descriptions))


if __name__ == "__main__":
    unittest.main()
