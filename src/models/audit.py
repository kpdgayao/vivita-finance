from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from uuid import UUID

@dataclass
class AuditEntry:
    """Represents an audit trail entry for tracking changes"""
    purchase_request_id: UUID
    action: str
    user_id: UUID
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[str] = None
    id: Optional[UUID] = None
