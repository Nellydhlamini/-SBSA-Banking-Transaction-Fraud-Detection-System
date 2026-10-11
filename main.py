"""
Demo runner for the fraud-detection system.

Wires the services together, seeds a customer and account, then processes a
normal transaction (settles) and a suspicious one (blocked with alerts).

Run:
    python main.py
"""
from fraud_system.access import AccessControl
from fraud_system.alerting import AlertingService
from fraud_system.audit import AuditService
from fraud_system.cases import CaseService
from fraud_system.decision import DecisionService
from fraud_system.incident import IncidentControl
from fraud_system.models import Account, Customer
from fraud_system.notifications import NotificationService
from fraud_system.processor import TransactionProcessor
from fraud_system.repository import InMemoryRepository
from fraud_system.rules import AmountRule, LocationRule, VelocityRule
from fraud_system.scoring import ScoringEngine
from fraud_system.settlement import SettlementService
from fraud_system.validation import ValidationService


def build_system():
    repo = InMemoryRepository()
    rules = [VelocityRule(max_count=5), LocationRule(), AmountRule(max_amount=5000)]
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
    return repo, processor, audit


def main() -> None:
    repo, processor, audit = build_system()

    customer = repo.add_customer(Customer(0, "Thabo Nkosi", home_country="ZA"))
    account = repo.add_account(Account(0, customer.customer_id, "1001234567", balance=15000.0))

    print("A) Normal domestic purchase (R250, POS, ZA)")
    a = processor.ingest(account.account_id, amount=250.0, channel="POS", country="ZA")
    print(f"   -> {a.transaction.status.value} | score {a.evaluation.risk_score} | {a.message}")

    print("B) Suspicious foreign high-value withdrawal (R8000, ATM, NG)")
    b = processor.ingest(account.account_id, amount=8000.0, channel="ATM", country="NG")
    alerts = ", ".join(al.rule_name for al in b.alerts) or "none"
    print(f"   -> {b.transaction.status.value} | score {b.evaluation.risk_score} | alerts: {alerts}")

    print(f"\nAccount balance after settlement: {repo.get_account(account.account_id).balance}")
    print(f"Audit entries: {len(audit.search())} | chain intact: {audit.verify_chain()}")


if __name__ == "__main__":
    main()
