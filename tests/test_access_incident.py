"""Tests for RBAC (FR-IAM-01) and incident controls (FR-INC-01)."""
import pytest

from fraud_system.access import AccessControl, AccessDenied
from fraud_system.models import Role, TransactionStatus, User


def test_analyst_can_review_but_not_manage_users():
    ac = AccessControl()
    analyst = User(1, "ana", Role.ANALYST)
    assert ac.can(analyst, "review_alert")
    assert not ac.can(analyst, "manage_users")


def test_require_raises_for_disallowed_action():
    ac = AccessControl()
    analyst = User(1, "ana", Role.ANALYST)
    with pytest.raises(AccessDenied):
        ac.require(analyst, "configure_rules")


def test_kill_switch_holds_processing(processor, account):
    processor._incident.engage_kill_switch("ops")
    result = processor.ingest(account.account_id, 100, "POS", "ZA")
    assert result.transaction.status == TransactionStatus.HELD


def test_processing_resumes_after_release(processor, account):
    processor._incident.engage_kill_switch("ops")
    processor._incident.release("ops")
    result = processor.ingest(account.account_id, 100, "POS", "ZA")
    assert result.transaction.status == TransactionStatus.SETTLED
