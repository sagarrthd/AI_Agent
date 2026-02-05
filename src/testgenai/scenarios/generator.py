from __future__ import annotations

from typing import List

from testgenai.models.requirement import Requirement
from testgenai.models.scenario import Scenario
from testgenai.models.signal import Signal


def build_scenarios(
    requirements: List[Requirement], signals: List[Signal]
) -> List[Scenario]:
    scenarios: List[Scenario] = []
    signal_names = [s.name for s in signals][:5]
    signal_text = ", ".join(signal_names) if signal_names else "No signals provided"

    for idx, req in enumerate(requirements, start=1):
        scenarios.append(
            Scenario(
                scenario_id=f"SCN-{idx:03d}",
                title=f"{req.title}",
                description=(
                    f"Validate requirement {req.req_id}. Signals: {signal_text}."
                ),
                requirement_ids=[req.req_id],
            )
        )

    if signals:
        scenarios.append(
            Scenario(
                scenario_id=f"SCN-{len(scenarios)+1:03d}",
                title="Signal coverage sweep",
                description="Validate baseline coverage across listed signals.",
                requirement_ids=[r.req_id for r in requirements],
            )
        )

    return scenarios
