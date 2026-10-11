"""
Data-access layer.

Defines an abstract Repository (so a SQL Server / SQLite implementation can be
swapped in later) and a ready-to-run in-memory implementation used by the
services and the demo.
"""
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Dict, List, Optional

from .models import (Account, Alert, AuditEntry, Case, Customer, Evaluation,
                     Notification, Transaction, AlertStatus, utc_now)


class Repository(ABC):
    """Contract every storage backend must fulfil."""

    # customers / accounts
    @abstractmethod
    def add_customer(self, c: Customer) -> Customer: ...
    @abstractmethod
    def get_customer(self, customer_id: int) -> Optional[Customer]: ...
    @abstractmethod
    def add_account(self, a: Account) -> Account: ...
    @abstractmethod
    def get_account(self, account_id: int) -> Optional[Account]: ...
    @abstractmethod
    def update_account(self, a: Account) -> None: ...

    # transactions
    @abstractmethod
    def save_transaction(self, t: Transaction) -> Transaction: ...
    @abstractmethod
    def recent_transactions(self, account_id: int, within: timedelta) -> List[Transaction]: ...

    # fraud artefacts
    @abstractmethod
    def save_evaluation(self, e: Evaluation) -> Evaluation: ...
    @abstractmethod
    def save_alert(self, a: Alert) -> Alert: ...
    @abstractmethod
    def get_alert(self, alert_id: int) -> Optional[Alert]: ...
    @abstractmethod
    def update_alert(self, a: Alert) -> None: ...
    @abstractmethod
    def open_alerts(self) -> List[Alert]: ...
    @abstractmethod
    def save_case(self, c: Case) -> Case: ...
    @abstractmethod
    def save_notification(self, n: Notification) -> Notification: ...

    # audit
    @abstractmethod
    def save_audit(self, e: AuditEntry) -> AuditEntry: ...
    @abstractmethod
    def last_audit_hash(self) -> str: ...
    @abstractmethod
    def all_audit(self) -> List[AuditEntry]: ...


class InMemoryRepository(Repository):
    """Simple dictionary-backed store. Keeps auto-incrementing ids per entity."""

    def __init__(self) -> None:
        self._customers: Dict[int, Customer] = {}
        self._accounts: Dict[int, Account] = {}
        self._transactions: Dict[int, Transaction] = {}
        self._evaluations: Dict[int, Evaluation] = {}
        self._alerts: Dict[int, Alert] = {}
        self._cases: Dict[int, Case] = {}
        self._notifications: Dict[int, Notification] = {}
        self._audit: List[AuditEntry] = []
        self._seq: Dict[str, int] = {}

    def _next(self, name: str) -> int:
        self._seq[name] = self._seq.get(name, 0) + 1
        return self._seq[name]

    # customers / accounts
    def add_customer(self, c: Customer) -> Customer:
        if not c.customer_id:
            c.customer_id = self._next("customer")
        self._customers[c.customer_id] = c
        return c

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        return self._customers.get(customer_id)

    def add_account(self, a: Account) -> Account:
        if not a.account_id:
            a.account_id = self._next("account")
        self._accounts[a.account_id] = a
        return a

    def get_account(self, account_id: int) -> Optional[Account]:
        return self._accounts.get(account_id)

    def update_account(self, a: Account) -> None:
        self._accounts[a.account_id] = a

    # transactions
    def save_transaction(self, t: Transaction) -> Transaction:
        if not t.txn_id:
            t.txn_id = self._next("txn")
        self._transactions[t.txn_id] = t
        return t

    def recent_transactions(self, account_id: int, within: timedelta) -> List[Transaction]:
        cutoff = utc_now() - within
        return [t for t in self._transactions.values()
                if t.account_id == account_id and t.created_at >= cutoff]

    # fraud artefacts
    def save_evaluation(self, e: Evaluation) -> Evaluation:
        self._evaluations[e.txn_id] = e
        return e

    def save_alert(self, a: Alert) -> Alert:
        if not a.alert_id:
            a.alert_id = self._next("alert")
        self._alerts[a.alert_id] = a
        return a

    def get_alert(self, alert_id: int) -> Optional[Alert]:
        return self._alerts.get(alert_id)

    def update_alert(self, a: Alert) -> None:
        self._alerts[a.alert_id] = a

    def open_alerts(self) -> List[Alert]:
        return [a for a in self._alerts.values() if a.status == AlertStatus.OPEN]

    def save_case(self, c: Case) -> Case:
        if not c.case_id:
            c.case_id = self._next("case")
        self._cases[c.case_id] = c
        return c

    def save_notification(self, n: Notification) -> Notification:
        if not n.notification_id:
            n.notification_id = self._next("notification")
        self._notifications[n.notification_id] = n
        return n

    # audit
    def save_audit(self, e: AuditEntry) -> AuditEntry:
        if not e.entry_id:
            e.entry_id = self._next("audit")
        self._audit.append(e)
        return e

    def last_audit_hash(self) -> str:
        return self._audit[-1].hash if self._audit else ""

    def all_audit(self) -> List[AuditEntry]:
        return list(self._audit)
