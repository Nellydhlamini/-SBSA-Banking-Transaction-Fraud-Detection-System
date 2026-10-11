"""Domain models and enumerations for the fraud-detection system."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- enumerations (fixed value domains) -------------------------------------
class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    BLOCKED = "BLOCKED"
    DECLINED = "DECLINED"
    SETTLED = "SETTLED"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CLOSED = "CLOSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class CaseStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class Role(str, Enum):
    ANALYST = "ANALYST"
    SUPERVISOR = "SUPERVISOR"
    COMPLIANCE = "COMPLIANCE"
    OPS = "OPS"
    ADMIN = "ADMIN"


# --- entities ---------------------------------------------------------------
@dataclass
class Customer:
    customer_id: int
    name: str
    home_country: str
    risk_rating: str = "LOW"


@dataclass
class Account:
    account_id: int
    customer_id: int
    account_number: str
    balance: float
    currency: str = "ZAR"
    status: str = "ACTIVE"


@dataclass
class Transaction:
    txn_id: int
    account_id: int
    amount: float
    channel: str          # ATM / POS / ONLINE / EFT / MOBILE
    country: str          # ISO country where the transaction originated
    recipient: str = ""
    currency: str = "ZAR"
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Evaluation:
    txn_id: int
    risk_score: float
    decision: Optional[Decision] = None
    breached_rules: List[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=utc_now)


@dataclass
class Alert:
    alert_id: int
    txn_id: int
    rule_name: str
    severity: Severity
    status: AlertStatus = AlertStatus.OPEN
    raised_at: datetime = field(default_factory=utc_now)


@dataclass
class Case:
    case_id: int
    assigned_to: Optional[int] = None
    status: CaseStatus = CaseStatus.OPEN
    alert_ids: List[int] = field(default_factory=list)
    resolution: str = ""
    opened_at: datetime = field(default_factory=utc_now)


@dataclass
class Notification:
    notification_id: int
    txn_id: int
    recipient: str
    channel: str
    message: str
    sent_at: datetime = field(default_factory=utc_now)


@dataclass
class AuditEntry:
    entry_id: int
    entity_type: str
    entity_id: int
    action: str
    actor: str
    old_value: str = ""
    new_value: str = ""
    hash: str = ""
    timestamp: datetime = field(default_factory=utc_now)


@dataclass
class User:
    user_id: int
    username: str
    role: Role
