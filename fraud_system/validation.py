"""
Validation service (FR-VAL-01, FR-VAL-02).

Checks a transaction is structurally valid, then that its account exists, is
active and has sufficient balance - before any fraud scoring happens.
"""
from dataclasses import dataclass

from .models import Transaction
from .repository import Repository

VALID_CHANNELS = {"ATM", "POS", "ONLINE", "EFT", "MOBILE"}


@dataclass
class ValidationResult:
    ok: bool
    reason: str = ""


class ValidationService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def validate_syntax(self, txn: Transaction) -> ValidationResult:
        """FR-VAL-01: required fields present and well-formed."""
        if txn.amount is None or txn.amount <= 0:
            return ValidationResult(False, "Amount must be greater than zero")
        if not txn.channel or txn.channel not in VALID_CHANNELS:
            return ValidationResult(False, f"Invalid channel: {txn.channel}")
        if not txn.country:
            return ValidationResult(False, "Country is required")
        return ValidationResult(True)

    def verify_account_and_balance(self, txn: Transaction) -> ValidationResult:
        """FR-VAL-02: account exists, is active, and is sufficiently funded."""
        account = self._repo.get_account(txn.account_id)
        if account is None:
            return ValidationResult(False, "Unknown account")
        if account.status != "ACTIVE":
            return ValidationResult(False, f"Account not active ({account.status})")
        if account.balance < txn.amount:
            return ValidationResult(False, "Insufficient balance")
        return ValidationResult(True)
