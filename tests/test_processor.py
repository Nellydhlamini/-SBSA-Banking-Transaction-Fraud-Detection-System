"""End-to-end tests for the transaction processor (FR-ING-01 + full flow)."""
from fraud_system.models import TransactionStatus


def test_normal_transaction_is_settled(processor, account, repo):
    result = processor.ingest(account.account_id, amount=250, channel="POS", country="ZA")
    assert result.transaction.status == TransactionStatus.SETTLED
    assert result.evaluation.risk_score == 0
    assert repo.get_account(account.account_id).balance == 19750.0


def test_foreign_high_value_is_blocked_with_alerts(processor, account):
    result = processor.ingest(account.account_id, amount=8000, channel="ATM", country="NG")
    assert result.transaction.status == TransactionStatus.BLOCKED
    assert result.evaluation.risk_score >= 70
    assert len(result.alerts) >= 1


def test_foreign_low_value_is_held_for_review(processor, account):
    # location anomaly only (50 pts) -> REVIEW band -> HELD
    result = processor.ingest(account.account_id, amount=1000, channel="ONLINE", country="NG")
    assert result.transaction.status == TransactionStatus.HELD
    assert len(result.alerts) == 1


def test_insufficient_balance_is_declined(processor, account):
    result = processor.ingest(account.account_id, amount=999999, channel="POS", country="ZA")
    assert result.transaction.status == TransactionStatus.DECLINED


def test_invalid_channel_is_declined(processor, account):
    result = processor.ingest(account.account_id, amount=100, channel="BAD", country="ZA")
    assert result.transaction.status == TransactionStatus.DECLINED


def test_blocked_transaction_does_not_debit_balance(processor, account, repo):
    processor.ingest(account.account_id, amount=8000, channel="ATM", country="NG")
    assert repo.get_account(account.account_id).balance == 20000.0
