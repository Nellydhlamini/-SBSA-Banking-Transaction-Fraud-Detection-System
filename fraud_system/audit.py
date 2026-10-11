"""
Audit service (FR-AUD-01, FR-AUD-02).

Append-only, hash-chained audit trail: each entry's hash includes the previous
entry's hash, so any tampering breaks the chain. Supports simple search and a
chain-integrity check.
"""
import hashlib
from typing import List, Optional

from .models import AuditEntry
from .repository import Repository


class AuditService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    @staticmethod
    def _compute_hash(previous_hash: str, entry: AuditEntry) -> str:
        payload = "|".join([previous_hash, entry.entity_type, str(entry.entity_id),
                            entry.action, entry.actor, entry.old_value, entry.new_value])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record(self, entity_type: str, entity_id: int, action: str, actor: str,
               old_value: str = "", new_value: str = "") -> AuditEntry:
        """FR-AUD-01: append an immutable, hash-stamped entry."""
        entry = AuditEntry(entry_id=0, entity_type=entity_type, entity_id=entity_id,
                           action=action, actor=actor, old_value=old_value, new_value=new_value)
        entry.hash = self._compute_hash(self._repo.last_audit_hash(), entry)
        return self._repo.save_audit(entry)

    def search(self, entity_type: Optional[str] = None,
               entity_id: Optional[int] = None) -> List[AuditEntry]:
        """FR-AUD-02: filter the trail by entity type and/or id."""
        entries = self._repo.all_audit()
        if entity_type is not None:
            entries = [e for e in entries if e.entity_type == entity_type]
        if entity_id is not None:
            entries = [e for e in entries if e.entity_id == entity_id]
        return entries

    def verify_chain(self) -> bool:
        """Recompute every hash in order; return False if the chain is broken."""
        previous = ""
        for entry in self._repo.all_audit():
            if entry.hash != self._compute_hash(previous, entry):
                return False
            previous = entry.hash
        return True
