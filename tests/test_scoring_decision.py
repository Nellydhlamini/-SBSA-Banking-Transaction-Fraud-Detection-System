"""Tests for the scoring engine (FR-FRD-04) and decision service (FR-DEC-01)."""
from fraud_system.decision import DecisionService
from fraud_system.models import Account, Customer, Decision, Transaction
from fraud_system.scoring import ScoringEngine
from fraud_system.rules import AmountRule, LocationRule, VelocityRule


def test_score_sums_breached_rule_points(repo):
    customer = repo.add_customer(Customer(0, "A", home_country="ZA"))
    acct = repo.add_account(Account(0, customer.customer_id, "ACC", balance=50000))
    txn = repo.save_transaction(Transaction(0, acct.account_id, 8000, "ATM", "NG"))
    engine = ScoringEngine(repo, [LocationRule(points=50), AmountRule(max_amount=5000, points=30)])
    evaluation = engine.score(txn)
    assert evaluation.risk_score == 80
    assert len(evaluation.breached_rules) == 2


def test_score_capped_at_100(repo):
    customer = repo.add_customer(Customer(0, "A", home_country="ZA"))
    acct = repo.add_account(Account(0, customer.customer_id, "ACC", balance=50000))
    txn = repo.save_transaction(Transaction(0, acct.account_id, 8000, "ATM", "NG"))
    engine = ScoringEngine(repo, [LocationRule(points=80), AmountRule(max_amount=5000, points=80)])
    assert engine.score(txn).risk_score == 100


def test_decision_thresholds():
    svc = DecisionService(review_threshold=40, block_threshold=70)
    assert svc.decide(10) == Decision.ALLOW
    assert svc.decide(40) == Decision.REVIEW
    assert svc.decide(69) == Decision.REVIEW
    assert svc.decide(70) == Decision.BLOCK
    assert svc.decide(95) == Decision.BLOCK
