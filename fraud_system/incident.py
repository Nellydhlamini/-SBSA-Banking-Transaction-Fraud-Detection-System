"""
Production incident controls (FR-INC-01).

A kill switch that halts processing during an incident, and a replay helper that
re-processes transactions once the switch is released.
"""
from typing import List

from .models import Transaction


class IncidentControl:
    def __init__(self, audit=None) -> None:
        self._active = False
        self._audit = audit

    @property
    def is_active(self) -> bool:
        return self._active

    def engage_kill_switch(self, actor: str) -> None:
        self._active = True
        if self._audit:
            self._audit.record("System", 0, "KILL_SWITCH_ON", actor)

    def release(self, actor: str) -> None:
        self._active = False
        if self._audit:
            self._audit.record("System", 0, "KILL_SWITCH_OFF", actor)

    def replay(self, processor, transactions: List[Transaction]) -> list:
        """Re-process a batch of held transactions after the switch is released."""
        if self._active:
            raise RuntimeError("Release the kill switch before replaying")
        return [processor.process(t) for t in transactions]
