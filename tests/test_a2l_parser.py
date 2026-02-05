import unittest
from pathlib import Path

from testgenai.a2l.a2l_parser import load_a2l_signals


class A2LParserTests(unittest.TestCase):
    def test_empty_path(self) -> None:
        self.assertEqual(load_a2l_signals(""), [])

    def test_missing_file(self) -> None:
        self.assertEqual(load_a2l_signals(str(Path("missing.a2l"))), [])


if __name__ == "__main__":
    unittest.main()
