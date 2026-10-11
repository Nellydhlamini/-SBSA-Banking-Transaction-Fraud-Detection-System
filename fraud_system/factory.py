"""
System factory.

Builds a fully wired TransactionProcessor from any Repository, so the demo, the
tests and the UI all construct the system the same way.
"""
from typing import List, Optional, Tuple

from .alerting import AlertingService
from .audit import AuditService
from .decision import DecisionService
from .incident import IncidentControl
from .notifications import NotificationService
from .processor import TransactionProcessor
from .repository import Repository
from .rules import AmountRule, FraudRule, LocationRule, VelocityRule
from .scoring import ScoringEngine
from .settlement import SettlementService
from .validation import ValidationService


def default_rules() -> List[FraudRule]:
    return [VelocityRule(max_count=5), LocationRule(), AmountRule(max_amount=5000)]


def build_processor(repo: Repository,
                    rules: Optional[List[FraudRule]] = None
                    ) -> Tuple[TransactionProcessor, AuditService]:
    rules = rules or default_rules()
    audit = AuditService(repo)
    processor = TransactionProcessor(
        repo=repo,
        validation=ValidationService(repo),
        scoring=ScoringEngine(repo, rules),
        decision=DecisionService(),
        settlement=SettlementService(repo),
        alerting=AlertingService(repo),
        notifications=NotificationService(repo),
        audit=audit,
        incident=IncidentControl(audit),
        rules=rules,
    )
    return processor, audit
