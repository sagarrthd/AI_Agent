from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Requirement:
    req_id: str
    title: str
    description: str
    req_type: str
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
