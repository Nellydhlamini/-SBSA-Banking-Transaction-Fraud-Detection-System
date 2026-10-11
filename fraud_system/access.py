"""
Role-based access control (FR-IAM-01).

Maps each role to the permissions it holds and enforces them. Keeps authorisation
logic in one place so every service can ask "can this user do this?".
"""
from typing import Dict, Set

from .models import Role, User


class AccessDenied(Exception):
    """Raised when a user attempts an action their role does not permit."""


class AccessControl:
    PERMISSIONS: Dict[Role, Set[str]] = {
        Role.ANALYST:    {"review_alert", "view_dashboard"},
        Role.SUPERVISOR: {"review_alert", "manage_case", "view_dashboard"},
        Role.COMPLIANCE: {"view_audit", "view_dashboard"},
        Role.OPS:        {"view_dashboard", "handle_incident"},
        Role.ADMIN:      {"manage_users", "configure_rules", "handle_incident","view_dashboard", "view_audit"},
    }

    def can(self, user: User, permission: str) -> bool: return permission in self.PERMISSIONS.get(user.role, set())

    def require(self, user: User, permission: str) -> None:
        if not self.can(user, permission): raise AccessDenied(f"{user.role.value} may not '{permission}'")
