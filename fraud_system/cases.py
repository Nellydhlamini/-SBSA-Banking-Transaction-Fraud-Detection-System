"""
Fraud case management (FR-CSM-01).

Groups one or more alerts into a case, assigns it to an analyst, and moves it
through its status workflow (OPEN -> IN_PROGRESS -> CLOSED).
"""
from typing import Optional

from .models import Alert, Case, CaseStatus
from .repository import Repository


class CaseService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def open_case(self, assigned_to: Optional[int] = None) -> Case:
        return self._repo.save_case(Case(case_id=0, assigned_to=assigned_to))

    def link_alert(self, case: Case, alert: Alert) -> Case:
        if alert.alert_id not in case.alert_ids:
            case.alert_ids.append(alert.alert_id)
        return self._repo.save_case(case)

    def assign(self, case: Case, user_id: int) -> Case:
        case.assigned_to = user_id
        return self._repo.save_case(case)

    def set_status(self, case: Case, status: CaseStatus, resolution: str = "") -> Case:
        case.status = status
        if status == CaseStatus.CLOSED:
            case.resolution = resolution
        return self._repo.save_case(case)
