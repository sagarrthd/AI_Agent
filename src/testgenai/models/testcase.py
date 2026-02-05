from dataclasses import dataclass
from typing import List


@dataclass
class TestStep:
    step_id: str
    action: str
    expected: str
    requirement_ids: List[str]


@dataclass
class TestCase:
    test_id: str
    title: str
    preconditions: str
    steps: List[TestStep]
    requirements: List[str]
