"""
Alerting service (FR-ALR-01, FR-ALR-02).

Raises one alert per breached rule, exposes the open-alert queue, and lets an
analyst close an alert as confirmed fraud or a false positive.
"""
from typing import Dict, List

from .models import Alert, AlertStatus, Evaluation, Transaction
from .repository import Repository
from .rules import FraudRule


class AlertingService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def raise_alerts(self, txn: Transaction, evaluation: Evaluation,
                     rules_by_name: Dict[str, FraudRule]) -> List[Alert]:
        """FR-ALR-01: create an OPEN alert for each rule the transaction breached."""
        alerts: List[Alert] = []
        for name in evaluation.breached_rules:
            rule = rules_by_name.get(name)
            severity = rule.severity if rule else None
            alert = Alert(alert_id=0, txn_id=txn.txn_id, rule_name=name, severity=severity)
            alerts.append(self._repo.save_alert(alert))
        return alerts

    def open_queue(self) -> List[Alert]:
        """FR-ALR-02: the analyst's queue of open alerts."""
        return self._repo.open_alerts()

    def review(self, alert_id: int, is_fraud: bool) -> AlertStatus:
        """FR-ALR-02: analyst decision on an alert."""
        alert = self._repo.get_alert(alert_id)
        if alert is None:
            raise ValueError("Alert not found")
        alert.status = AlertStatus.CLOSED if is_fraud else AlertStatus.FALSE_POSITIVE
        self._repo.update_alert(alert)
        return alert.status
