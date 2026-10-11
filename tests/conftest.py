"""Shared pytest fixtures: a fully wired in-memory system and a seeded account."""
import pytest

from fraud_system.alerting import AlertingService
from fraud_system.audit import AuditService
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


@pytest.fixture
def repo():
    return InMemoryRepository()


@pytest.fixture
def rules():
    return [VelocityRule(max_count=5), LocationRule(), AmountRule(max_amount=5000)]


@pytest.fixture
def audit(repo):
    return AuditService(repo)


@pytest.fixture
def processor(repo, rules, audit):
    return TransactionProcessor(
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


@pytest.fixture
def account(repo):
    customer = repo.add_customer(Customer(0, "Test Customer", home_country="ZA"))
    return repo.add_account(Account(0, customer.customer_id, "ACC-1", balance=20000.0))
