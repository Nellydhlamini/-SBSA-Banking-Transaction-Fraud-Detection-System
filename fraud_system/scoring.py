"""
Fraud scoring engine (FR-FRD-04).

Runs every enabled rule against a transaction, sums the risk points (capped at
100) and records which rules were breached. Runs on the synchronous path,
before settlement.
"""
from datetime import timedelta
from typing import List

from .models import Evaluation, Transaction
from .repository import Repository
from .rules import FraudRule, RuleContext


class ScoringEngine:
    def __init__(self, repo: Repository, rules: List[FraudRule], velocity_window_seconds: int = 60) -> None:
        self._repo = repo
        self._rules = rules
        self._window = timedelta(seconds=velocity_window_seconds)

    def _build_context(self, txn: Transaction) -> RuleContext:
        recent = self._repo.recent_transactions(txn.account_id, self._window)
        account = self._repo.get_account(txn.account_id)
        home_country = ""
        if account is not None:
            customer = self._repo.get_customer(account.customer_id)
            if customer is not None:
                home_country = customer.home_country
        return RuleContext(recent_count=len(recent), home_country=home_country)

    def score(self, txn: Transaction) -> Evaluation:
        ctx = self._build_context(txn)
        total = 0.0
        breached: List[str] = []
        for rule in self._rules:
            if not rule.enabled:
                continue
            result = rule.evaluate(txn, ctx)
            if result.breached:
                total += result.score
                breached.append(result.rule_name)
        evaluation = Evaluation(txn.txn_id, min(total, 100.0), breached_rules=breached)
        return self._repo.save_evaluation(evaluation)
