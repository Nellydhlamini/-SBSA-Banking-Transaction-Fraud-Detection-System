"""
Decision service (FR-DEC-01).

Turns a numeric risk score into an ALLOW / REVIEW / BLOCK decision using two
configurable thresholds.
"""
from .models import Decision


class DecisionService:
    def __init__(self, review_threshold: float = 40.0, block_threshold: float = 70.0) -> None:
        self.review_threshold = review_threshold
        self.block_threshold = block_threshold

    def decide(self, risk_score: float) -> Decision:
        if risk_score >= self.block_threshold:
            return Decision.BLOCK
        if risk_score >= self.review_threshold:
            return Decision.REVIEW
        return Decision.ALLOW
