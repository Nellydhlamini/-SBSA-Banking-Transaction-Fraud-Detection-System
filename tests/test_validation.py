"""Tests for the validation service (FR-VAL-01/02)."""
from fraud_system.models import Transaction
from fraud_system.validation import ValidationService


def _txn(account_id=1, amount=100.0, channel="POS", country="ZA"):
    return Transaction(0, account_id, amount, channel, country)


def test_valid_syntax_passes(repo):
    assert ValidationService(repo).validate_syntax(_txn()).ok


def test_zero_amount_fails(repo):
    assert not ValidationService(repo).validate_syntax(_txn(amount=0)).ok


def test_invalid_channel_fails(repo):
    assert not ValidationService(repo).validate_syntax(_txn(channel="CARRIER_PIGEON")).ok


def test_missing_country_fails(repo):
    assert not ValidationService(repo).validate_syntax(_txn(country="")).ok


def test_unknown_account_fails(repo):
    assert not ValidationService(repo).verify_account_and_balance(_txn(account_id=999)).ok


def test_insufficient_balance_fails(repo, account):
    result = ValidationService(repo).verify_account_and_balance(_txn(account_id=account.account_id, amount=999999))
    assert not result.ok


def test_sufficient_balance_passes(repo, account):
    result = ValidationService(repo).verify_account_and_balance(_txn(account_id=account.account_id, amount=100))
    assert result.ok
