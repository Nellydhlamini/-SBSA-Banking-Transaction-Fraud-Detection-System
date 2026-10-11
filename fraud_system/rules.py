"""
Configurable fraud rules (FR-FRD-01, FR-FRD-02, FR-FRD-03).

Each rule is a small, independent object that inspects a transaction and its
context and reports whether it was breached and how many risk points to add.
New rule types are added by subclassing FraudRule - no change to the engine.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .models import Severity, Transaction


@dataclass
class RuleContext:
    """Facts the engine gathers once and hands to every rule."""
    recent_count: int      # transactions on this account within the velocity window
    home_country: str      # the customer's registered country


@dataclass
class RuleResult:
    rule_name: str
    breached: bool
    score: float
    severity: Severity


class FraudRule(ABC):
    """Base class for all fraud rules."""

    def __init__(self, name: str, severity: Severity, points: float, enabled: bool = True) -> None:
        self.name = name
        self.severity = severity
        self.points = points
        self.enabled = enabled

    @abstractmethod
    def _is_breached(self, txn: Transaction, ctx: RuleContext) -> bool:
        """Return True if this transaction breaks the rule."""

    def evaluate(self, txn: Transaction, ctx: RuleContext) -> RuleResult:
        breached = self._is_breached(txn, ctx)
        return RuleResult(self.name, breached, self.points if breached else 0.0, self.severity)


class VelocityRule(FraudRule):
    """FR-FRD-02: too many transactions on one account in a short window."""

    def __init__(self, max_count: int, points: float = 40, enabled: bool = True) -> None:
        super().__init__("High-Velocity Micro-Transactions", Severity.HIGH, points, enabled)
        self.max_count = max_count

    def _is_breached(self, txn: Transaction, ctx: RuleContext) -> bool:
        return ctx.recent_count >= self.max_count


class LocationRule(FraudRule):
    """FR-FRD-03: transaction originates outside the customer's home country."""

    def __init__(self, points: float = 50, enabled: bool = True) -> None:
        super().__init__("Foreign Location Anomaly", Severity.CRITICAL, points, enabled)

    def _is_breached(self, txn: Transaction, ctx: RuleContext) -> bool:
        return bool(ctx.home_country) and txn.country != ctx.home_country


class AmountRule(FraudRule):
    """A transaction above a configured amount threshold."""

    def __init__(self, max_amount: float, points: float = 30, enabled: bool = True) -> None:
        super().__init__("Large Amount Threshold", Severity.MEDIUM, points, enabled)
        self.max_amount = max_amount

    def _is_breached(self, txn: Transaction, ctx: RuleContext) -> bool:
        return txn.amount > self.max_amount
