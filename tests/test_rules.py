"""Tests for the fraud rules (FR-FRD-01/02/03)."""
from fraud_system.models import Transaction
from fraud_system.rules import AmountRule, LocationRule, RuleContext, VelocityRule


def _txn(amount=100.0, country="ZA"):
    return Transaction(0, 1, amount, "POS", country)


def test_velocity_breached_at_threshold():
    rule = VelocityRule(max_count=5)
    ctx = RuleContext(recent_count=5, home_country="ZA")
    assert rule.evaluate(_txn(), ctx).breached


def test_velocity_not_breached_below_threshold():
    rule = VelocityRule(max_count=5)
    ctx = RuleContext(recent_count=2, home_country="ZA")
    assert not rule.evaluate(_txn(), ctx).breached


def test_location_breached_for_foreign_country():
    ctx = RuleContext(recent_count=0, home_country="ZA")
    assert LocationRule().evaluate(_txn(country="NG"), ctx).breached


def test_location_not_breached_for_home_country():
    ctx = RuleContext(recent_count=0, home_country="ZA")
    assert not LocationRule().evaluate(_txn(country="ZA"), ctx).breached


def test_amount_rule_breached_above_threshold():
    ctx = RuleContext(recent_count=0, home_country="ZA")
    assert AmountRule(max_amount=5000).evaluate(_txn(amount=6000), ctx).breached


def test_score_is_points_when_breached_else_zero():
    ctx = RuleContext(recent_count=0, home_country="ZA")
    rule = AmountRule(max_amount=5000, points=30)
    assert rule.evaluate(_txn(amount=6000), ctx).score == 30
    assert rule.evaluate(_txn(amount=10), ctx).score == 0


def test_disabled_rule_flag():
    rule = VelocityRule(max_count=1, enabled=False)
    assert rule.enabled is False
