from __future__ import annotations

from .audit import record

STATE = {
    "rag_slow": False,
    "tool_fail": False,
    "cost_spike": False,
}


def enable(name: str) -> None:
    if name not in STATE:
        raise KeyError(f"Unknown incident: {name}")
    STATE[name] = True
    record("incident_enabled", incident=name)



def disable(name: str) -> None:
    if name not in STATE:
        raise KeyError(f"Unknown incident: {name}")
    STATE[name] = False
    record("incident_disabled", incident=name)



def status() -> dict[str, bool]:
    return dict(STATE)
