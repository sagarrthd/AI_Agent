from dataclasses import dataclass
from typing import List


@dataclass
class Scenario:
    scenario_id: str
    title: str
    description: str
    requirement_ids: List[str]
