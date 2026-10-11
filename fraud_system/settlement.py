"""
Settlement service (FR-DEC-02).

Settles an approved transaction: debits the account and marks the transaction
SETTLED. Only call this once a transaction has been approved.
"""
from .models import Transaction, TransactionStatus
from .repository import Repository


class SettlementService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def settle(self, txn: Transaction) -> Transaction:
        account = self._repo.get_account(txn.account_id)
        if account is None:
            raise ValueError("Cannot settle: account not found")
        account.balance -= txn.amount
        self._repo.update_account(account)
        txn.status = TransactionStatus.SETTLED
        return self._repo.save_transaction(txn)
