"""
fraud_system - Real-Time Transaction Processing & Fraud Detection System.

A modular, object-oriented backend that ingests a transaction, validates it,
scores it for fraud BEFORE settlement, decides allow/review/block, raises
alerts, manages cases, and records an immutable audit trail.

Module map (traced to the JIRA backlog):
    models        - domain entities and enums
    repository    - data-access abstraction + in-memory store
    validation    - FR-VAL: syntactic + account/balance checks
    rules         - FR-FRD: configurable fraud rules
    scoring       - FR-FRD-04: risk scoring engine
    decision      - FR-DEC-01: allow / review / block
    settlement    - FR-DEC-02: settle approved transactions
    alerting      - FR-ALR: raise and review alerts
    notifications - FR-CSM-02: customer notifications
    cases         - FR-CSM-01: fraud case management
    audit         - FR-AUD: immutable, hash-chained audit trail
    access        - FR-IAM: role-based access control
    incident      - FR-INC: kill switch + replay
    processor     - FR-ING + orchestration of the synchronous flow
"""

__version__ = "1.0.0"
