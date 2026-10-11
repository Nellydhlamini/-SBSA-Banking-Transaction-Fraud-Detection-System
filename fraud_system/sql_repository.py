"""
SQL Server-backed repository.

Implements the same Repository interface as InMemoryRepository, but persists
every entity to the FraudDetection database (schema 'fds'). Swap it in and the
whole system runs on SQL Server with no other code changes.
"""
import json
from datetime import timedelta
from typing import List, Optional

import pyodbc

from .models import (Account, Alert, AlertStatus, AuditEntry, Case, CaseStatus,
                     Customer, Decision, Evaluation, Notification, Severity,
                     Transaction, TransactionStatus)
from .repository import Repository

# --- connection settings (match db.py) --------------------------------------
DB_DRIVER = "ODBC Driver 18 for SQL Server"
DB_SERVER = r"localhost\SQLEXPRESS"
DB_NAME = "FraudDetection"
DB_USER = ""
DB_PASSWORD = ""


def build_connection_string() -> str:
    base = (f"DRIVER={{{DB_DRIVER}}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
            f"Encrypt=yes;TrustServerCertificate=yes;")
    if DB_USER:
        return base + f"UID={DB_USER};PWD={DB_PASSWORD};"
    return base + "Trusted_Connection=yes;"


def _sev(value) -> Optional[Severity]:
    return Severity(value) if value else None


class SqlRepository(Repository):
    def __init__(self, connection_string: Optional[str] = None) -> None:
        self._conn = pyodbc.connect(connection_string or build_connection_string(), autocommit=True)

    def close(self) -> None:
        self._conn.close()

    def _cur(self):
        return self._conn.cursor()

    # --- row mappers --------------------------------------------------------
    def _to_txn(self, r) -> Transaction:
        return Transaction(r.TxnId, r.AccountId, float(r.Amount), r.Channel, r.Country,
                           r.Recipient or "", r.Currency, TransactionStatus(r.Status), r.CreatedAt)

    def _to_alert(self, r) -> Alert:
        return Alert(r.AlertId, r.TxnId, r.RuleName, _sev(r.Severity), AlertStatus(r.Status), r.RaisedAt)

    # --- customers / accounts ----------------------------------------------
    def add_customer(self, c: Customer) -> Customer:
        row = self._cur().execute(
            "INSERT INTO fds.Customers (Name,HomeCountry,RiskRating) "
            "OUTPUT INSERTED.CustomerId VALUES (?,?,?)",
            c.name, c.home_country, c.risk_rating).fetchone()
        c.customer_id = int(row[0])
        return c

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        r = self._cur().execute(
            "SELECT CustomerId,Name,HomeCountry,RiskRating FROM fds.Customers WHERE CustomerId=?",
            customer_id).fetchone()
        return Customer(r.CustomerId, r.Name, r.HomeCountry, r.RiskRating) if r else None

    def add_account(self, a: Account) -> Account:
        row = self._cur().execute(
            "INSERT INTO fds.Accounts (CustomerId,AccountNumber,Balance,Currency,Status) "
            "OUTPUT INSERTED.AccountId VALUES (?,?,?,?,?)",
            a.customer_id, a.account_number, a.balance, a.currency, a.status).fetchone()
        a.account_id = int(row[0])
        return a

    def get_account(self, account_id: int) -> Optional[Account]:
        r = self._cur().execute(
            "SELECT AccountId,CustomerId,AccountNumber,Balance,Currency,Status "
            "FROM fds.Accounts WHERE AccountId=?", account_id).fetchone()
        return Account(r.AccountId, r.CustomerId, r.AccountNumber, float(r.Balance),
                       r.Currency, r.Status) if r else None

    def update_account(self, a: Account) -> None:
        self._cur().execute(
            "UPDATE fds.Accounts SET Balance=?,Status=? WHERE AccountId=?",
            a.balance, a.status, a.account_id)

    # --- transactions -------------------------------------------------------
    def save_transaction(self, t: Transaction) -> Transaction:
        cur = self._cur()
        if t.txn_id:
            cur.execute("UPDATE fds.Transactions SET Status=? WHERE TxnId=?", t.status.value, t.txn_id)
        else:
            row = cur.execute(
                "INSERT INTO fds.Transactions (AccountId,Amount,Channel,Country,Recipient,Currency,Status,CreatedAt) "
                "OUTPUT INSERTED.TxnId VALUES (?,?,?,?,?,?,?,?)",
                t.account_id, t.amount, t.channel, t.country, t.recipient or None,
                t.currency, t.status.value, t.created_at).fetchone()
            t.txn_id = int(row[0])
        return t

    def recent_transactions(self, account_id: int, within: timedelta) -> List[Transaction]:
        seconds = int(within.total_seconds())
        rows = self._cur().execute(
            "SELECT TxnId,AccountId,Amount,Channel,Country,Recipient,Currency,Status,CreatedAt "
            "FROM fds.Transactions WHERE AccountId=? AND CreatedAt >= DATEADD(SECOND,?,SYSUTCDATETIME())",
            account_id, -seconds).fetchall()
        return [self._to_txn(r) for r in rows]

    # --- evaluations --------------------------------------------------------
    def save_evaluation(self, e: Evaluation) -> Evaluation:
        cur = self._cur()
        cur.execute("DELETE FROM fds.Evaluations WHERE TxnId=?", e.txn_id)
        cur.execute(
            "INSERT INTO fds.Evaluations (TxnId,RiskScore,Decision,BreachedRules,EvaluatedAt) VALUES (?,?,?,?,?)",
            e.txn_id, e.risk_score, e.decision.value if e.decision else None,
            json.dumps(e.breached_rules), e.evaluated_at)
        return e

    # --- alerts -------------------------------------------------------------
    def save_alert(self, a: Alert) -> Alert:
        row = self._cur().execute(
            "INSERT INTO fds.Alerts (TxnId,RuleName,Severity,Status,RaisedAt) "
            "OUTPUT INSERTED.AlertId VALUES (?,?,?,?,?)",
            a.txn_id, a.rule_name, a.severity.value if a.severity else None,
            a.status.value, a.raised_at).fetchone()
        a.alert_id = int(row[0])
        return a

    def get_alert(self, alert_id: int) -> Optional[Alert]:
        r = self._cur().execute(
            "SELECT AlertId,TxnId,RuleName,Severity,Status,RaisedAt FROM fds.Alerts WHERE AlertId=?",
            alert_id).fetchone()
        return self._to_alert(r) if r else None

    def update_alert(self, a: Alert) -> None:
        self._cur().execute("UPDATE fds.Alerts SET Status=? WHERE AlertId=?", a.status.value, a.alert_id)

    def open_alerts(self) -> List[Alert]:
        rows = self._cur().execute(
            "SELECT AlertId,TxnId,RuleName,Severity,Status,RaisedAt FROM fds.Alerts WHERE Status='OPEN' "
            "ORDER BY AlertId DESC").fetchall()
        return [self._to_alert(r) for r in rows]

    # --- cases --------------------------------------------------------------
    def save_case(self, c: Case) -> Case:
        cur = self._cur()
        if c.case_id:
            cur.execute("UPDATE fds.Cases SET AssignedTo=?,Status=?,AlertIdsJson=?,Resolution=? WHERE CaseId=?",
                        c.assigned_to, c.status.value, json.dumps(c.alert_ids), c.resolution, c.case_id)
        else:
            row = cur.execute(
                "INSERT INTO fds.Cases (AssignedTo,Status,AlertIdsJson,Resolution,OpenedAt) "
                "OUTPUT INSERTED.CaseId VALUES (?,?,?,?,?)",
                c.assigned_to, c.status.value, json.dumps(c.alert_ids), c.resolution, c.opened_at).fetchone()
            c.case_id = int(row[0])
        return c

    # --- notifications ------------------------------------------------------
    def save_notification(self, n: Notification) -> Notification:
        row = self._cur().execute(
            "INSERT INTO fds.Notifications (TxnId,Recipient,Channel,Message,SentAt) "
            "OUTPUT INSERTED.NotificationId VALUES (?,?,?,?,?)",
            n.txn_id, n.recipient, n.channel, n.message, n.sent_at).fetchone()
        n.notification_id = int(row[0])
        return n

    # --- audit --------------------------------------------------------------
    def save_audit(self, e: AuditEntry) -> AuditEntry:
        row = self._cur().execute(
            "INSERT INTO fds.AuditEntries (EntityType,EntityId,Action,Actor,OldValue,NewValue,Hash,Timestamp) "
            "OUTPUT INSERTED.EntryId VALUES (?,?,?,?,?,?,?,?)",
            e.entity_type, e.entity_id, e.action, e.actor, e.old_value, e.new_value,
            e.hash, e.timestamp).fetchone()
        e.entry_id = int(row[0])
        return e

    def last_audit_hash(self) -> str:
        r = self._cur().execute("SELECT TOP 1 Hash FROM fds.AuditEntries ORDER BY EntryId DESC").fetchone()
        return r[0] if r else ""

    def all_audit(self) -> List[AuditEntry]:
        rows = self._cur().execute(
            "SELECT EntryId,EntityType,EntityId,Action,Actor,OldValue,NewValue,Hash,Timestamp "
            "FROM fds.AuditEntries ORDER BY EntryId").fetchall()
        return [AuditEntry(r.EntryId, r.EntityType, r.EntityId, r.Action, r.Actor,
                           r.OldValue or "", r.NewValue or "", r.Hash, r.Timestamp) for r in rows]

    # --- extra read helpers for the UI (not part of the interface) ----------
    def list_accounts(self) -> List[Account]:
        rows = self._cur().execute(
            "SELECT AccountId,CustomerId,AccountNumber,Balance,Currency,Status FROM fds.Accounts "
            "ORDER BY AccountId").fetchall()
        return [Account(r.AccountId, r.CustomerId, r.AccountNumber, float(r.Balance),
                        r.Currency, r.Status) for r in rows]

    def list_transactions(self, limit: int = 100) -> List[Transaction]:
        rows = self._cur().execute(
            "SELECT TOP (?) TxnId,AccountId,Amount,Channel,Country,Recipient,Currency,Status,CreatedAt "
            "FROM fds.Transactions ORDER BY TxnId DESC", limit).fetchall()
        return [self._to_txn(r) for r in rows]

    def list_alerts(self, status: Optional[str] = None) -> List[Alert]:
        if status:
            rows = self._cur().execute(
                "SELECT AlertId,TxnId,RuleName,Severity,Status,RaisedAt FROM fds.Alerts "
                "WHERE Status=? ORDER BY AlertId DESC", status).fetchall()
        else:
            rows = self._cur().execute(
                "SELECT AlertId,TxnId,RuleName,Severity,Status,RaisedAt FROM fds.Alerts "
                "ORDER BY AlertId DESC").fetchall()
        return [self._to_alert(r) for r in rows]
