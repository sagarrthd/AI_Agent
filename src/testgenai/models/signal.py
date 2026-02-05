from dataclasses import dataclass


@dataclass
class Signal:
    name: str
    unit: str
    min_val: float
    max_val: float
    data_type: str
    source: str
