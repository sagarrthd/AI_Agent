from __future__ import annotations

from typing import Dict, Iterable

from testgenai.models.signal import Signal


class SignalRegistry:
    def __init__(self, signals: Iterable[Signal]) -> None:
        self._signals: Dict[str, Signal] = {s.name: s for s in signals}

    def get(self, name: str) -> Signal | None:
        return self._signals.get(name)

    def all(self) -> list[Signal]:
        return list(self._signals.values())
