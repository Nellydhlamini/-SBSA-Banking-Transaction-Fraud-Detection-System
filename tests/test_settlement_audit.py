"""Tests for settlement (FR-DEC-02) and the audit trail (FR-AUD-01/02)."""
from fraud_system.models import TransactionStatus, Transaction
from fraud_system.settlement import SettlementService


def test_settlement_debits_balance_and_marks_settled(repo, account):
    txn = repo.save_transaction(Transaction(0, account.account_id, 500, "POS", "ZA"))
    settled = SettlementService(repo).settle(txn)
    assert settled.status == TransactionStatus.SETTLED
    assert repo.get_account(account.account_id).balance == 19500.0


def test_audit_record_and_chain_integrity(audit):
    audit.record("Transaction", 1, "CREATE", "system", "", "PENDING")
    audit.record("Transaction", 1, "SETTLE", "system", "PENDING", "SETTLED")
    assert audit.verify_chain() is True
    assert len(audit.search(entity_type="Transaction", entity_id=1)) == 2


def test_tampering_breaks_the_audit_chain(audit):
    audit.record("Transaction", 1, "CREATE", "system", "", "PENDING")
    audit.record("Transaction", 1, "BLOCK", "system", "PENDING", "BLOCKED")
    entries = audit.search()
    entries[0].new_value = "HACKED"          # tamper with a committed entry
    assert audit.verify_chain() is False
