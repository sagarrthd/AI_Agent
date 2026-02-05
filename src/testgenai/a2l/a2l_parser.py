from __future__ import annotations

from pathlib import Path
from typing import List
import re

from testgenai.models.signal import Signal


_MEASUREMENT_RE = re.compile(r"^/begin\s+MEASUREMENT\s+(\S+)")
_CHARACTERISTIC_RE = re.compile(r"^/begin\s+CHARACTERISTIC\s+(\S+)")


def load_a2l_signals(path: str) -> List[Signal]:
    if not path:
        return []
    a2l_path = Path(path)
    if not a2l_path.exists():
        return []

    signals: List[Signal] = []
    for line in a2l_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        name = _match_name(line)
        if not name:
            continue
        signals.append(
            Signal(
                name=name,
                unit="",
                min_val=0.0,
                max_val=0.0,
                data_type="",
                source="A2L",
            )
        )
    return signals


def _match_name(line: str) -> str | None:
    for pattern in (_MEASUREMENT_RE, _CHARACTERISTIC_RE):
        match = pattern.match(line.strip())
        if match:
            return match.group(1)
    return None
