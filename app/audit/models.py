"""app.audit.models

Audit event domain models.
"""

from dataclasses import dataclass


@dataclass
class AuditEvent:
    id: str
    payload: dict
