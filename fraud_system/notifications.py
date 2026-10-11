"""
Notification service (FR-CSM-02).

Creates a notification record for a transaction outcome and dispatches it via a
channel (the actual gateway integration is out of scope - this records intent).
"""
from .models import Notification, Transaction
from .repository import Repository

VALID_CHANNELS = {"SMS", "EMAIL", "DASHBOARD", "PUSH"}


class NotificationService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def notify(self, txn: Transaction, recipient: str, message: str,
               channel: str = "SMS") -> Notification:
        if channel not in VALID_CHANNELS:
            raise ValueError(f"Unsupported channel: {channel}")
        notification = Notification(notification_id=0, txn_id=txn.txn_id,
                                    recipient=recipient, channel=channel, message=message)
        return self._repo.save_notification(notification)
