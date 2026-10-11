"""
Transaction processor (FR-ING-01 + orchestration).

Ties the services together into the synchronous flow from UML User Flow A:

    ingest -> validate -> score fraud -> decide
           -> ALLOW : settle + notify
           -> REVIEW: hold + raise alerts
           -> BLOCK : block + raise alerts + notify

Every outcome is written to the audit trail, and the kill switch (incident
control) can hold all processing.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .alerting import AlertingService
from .audit import AuditService
from .decision import DecisionService
from .incident import IncidentControl
from .models import (Account, Alert, Decision, Evaluation, Transaction,
                     TransactionStatus)
from .notifications import NotificationService
from .repository import Repository
from .rules import FraudRule
from .scoring import ScoringEngine
from .settlement import SettlementService
from .validation import ValidationService


@dataclass
class ProcessResult:
    transaction: Transaction
    evaluation: Optional[Evaluation] = None
    alerts: List[Alert] = field(default_factory=list)
    message: str = ""


class TransactionProcessor:
    def __init__(self, repo: Repository, validation: ValidationService,
                 scoring: ScoringEngine, decision: DecisionService,
                 settlement: SettlementService, alerting: AlertingService,
                 notifications: NotificationService, audit: AuditService,
                 incident: IncidentControl, rules: List[FraudRule]) -> None:
        self._repo = repo
        self._validation = validation
        self._scoring = scoring
        self._decision = decision
        self._settlement = settlement
        self._alerting = alerting
        self._notifications = notifications
        self._audit = audit
        self._incident = incident
        self._rules_by_name: Dict[str, FraudRule] = {r.name: r for r in rules}

    # FR-ING-01: create a PENDING transaction, then run it through the pipeline.
    def ingest(self, account_id: int, amount: float, channel: str,
               country: str, recipient: str = "") -> ProcessResult:
        txn = Transaction(txn_id=0, account_id=account_id, amount=amount,
                          channel=channel, country=country, recipient=recipient)
        self._repo.save_transaction(txn)
        self._audit.record("Transaction", txn.txn_id, "CREATE", "system", "", "PENDING")
        return self.process(txn)

    def process(self, txn: Transaction) -> ProcessResult:
        if self._incident.is_active:
            return self._set_status(txn, TransactionStatus.HELD,
                                    "Held - incident kill switch active")

        # FR-VAL-01 / FR-VAL-02
        syntax = self._validation.validate_syntax(txn)
        if not syntax.ok:
            return self._decline(txn, syntax.reason)
        account_check = self._validation.verify_account_and_balance(txn)
        if not account_check.ok:
            return self._decline(txn, account_check.reason)

        # FR-FRD-04: score BEFORE settlement, then FR-DEC-01: decide
        evaluation = self._scoring.score(txn)
        evaluation.decision = self._decision.decide(evaluation.risk_score)
        self._repo.save_evaluation(evaluation)

        if evaluation.decision == Decision.BLOCK:
            return self._block(txn, evaluation)
        if evaluation.decision == Decision.REVIEW:
            return self._review(txn, evaluation)
        return self._approve(txn, evaluation)

    # --- outcome handlers ---------------------------------------------------
    def _approve(self, txn: Transaction, evaluation: Evaluation) -> ProcessResult:
        self._settlement.settle(txn)  # FR-DEC-02
        self._notifications.notify(txn, recipient="customer",
                                   message="Your transaction was approved.")
        self._audit.record("Transaction", txn.txn_id, "SETTLE", "system",
                           "PENDING", TransactionStatus.SETTLED.value)
        return ProcessResult(txn, evaluation, [], "Approved and settled")

    def _review(self, txn: Transaction, evaluation: Evaluation) -> ProcessResult:
        txn.status = TransactionStatus.HELD
        self._repo.save_transaction(txn)
        alerts = self._alerting.raise_alerts(txn, evaluation, self._rules_by_name)
        self._audit.record("Transaction", txn.txn_id, "HOLD", "system",
                           "PENDING", TransactionStatus.HELD.value)
        return ProcessResult(txn, evaluation, alerts, "Held for analyst review")

    def _block(self, txn: Transaction, evaluation: Evaluation) -> ProcessResult:
        txn.status = TransactionStatus.BLOCKED
        self._repo.save_transaction(txn)
        alerts = self._alerting.raise_alerts(txn, evaluation, self._rules_by_name)
        self._notifications.notify(txn, recipient="customer",
                                   message="Your transaction was blocked for your protection.")
        self._audit.record("Transaction", txn.txn_id, "BLOCK", "system",
                           "PENDING", TransactionStatus.BLOCKED.value)
        return ProcessResult(txn, evaluation, alerts, "Blocked - fraud suspected")

    def _decline(self, txn: Transaction, reason: str) -> ProcessResult:
        txn.status = TransactionStatus.DECLINED
        self._repo.save_transaction(txn)
        self._audit.record("Transaction", txn.txn_id, "DECLINE", "system", "PENDING", reason)
        return ProcessResult(txn, None, [], f"Declined - {reason}")

    def _set_status(self, txn: Transaction, status: TransactionStatus, message: str) -> ProcessResult:
        txn.status = status
        self._repo.save_transaction(txn)
        self._audit.record("Transaction", txn.txn_id, status.value, "system", "PENDING", message)
        return ProcessResult(txn, None, [], message)
