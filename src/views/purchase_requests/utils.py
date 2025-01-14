from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID
from ...models import PurchaseRequest, PurchaseRequestStatus

def format_currency(amount: Decimal) -> str:
    """Format decimal amount as currency string"""
    return f"₱{float(amount):,.2f}" if amount else "₱0.00"

def can_approve_prf(user: Dict) -> bool:
    """Check if user has permission to approve PRFs"""
    return user['role'].lower() in ['finance', 'admin']

def can_delete_prf(user: Dict, prf: PurchaseRequest) -> bool:
    """Check if user can delete a PRF"""
    if prf.status != PurchaseRequestStatus.DRAFT:
        return False
    return (user['id'] == prf.requestor_id) or user['role'].lower() in ['finance', 'admin']
