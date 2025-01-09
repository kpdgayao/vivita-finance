from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from uuid import UUID
from enum import Enum

class PurchaseRequestStatus(Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

def validate_decimal(value: Decimal) -> Decimal:
    """Validate decimal to ensure it matches database precision (15,2)"""
    if value is None:
        return None
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

@dataclass
class PurchaseRequestItem:
    item_description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    total_price: Decimal
    purchase_request_id: UUID
    account_code: Optional[str] = None
    remarks: Optional[str] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Validate decimal fields
        self.quantity = validate_decimal(self.quantity)
        self.unit_price = validate_decimal(self.unit_price)
        self.total_price = validate_decimal(self.total_price)
        
        # Validate total_price calculation
        calculated_total = validate_decimal(self.quantity * self.unit_price)
        if self.total_price != calculated_total:
            self.total_price = calculated_total

@dataclass
class PurchaseRequest:
    form_number: str
    requestor_id: UUID
    supplier_id: UUID
    status: PurchaseRequestStatus = PurchaseRequestStatus.DRAFT
    total_amount: Optional[Decimal] = None
    remarks: Optional[str] = None
    items: Optional[List[PurchaseRequestItem]] = field(default_factory=list)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Convert status string to enum if needed
        if isinstance(self.status, str):
            self.status = PurchaseRequestStatus(self.status)
        
        # Validate total_amount
        if self.total_amount is not None:
            self.total_amount = validate_decimal(self.total_amount)
        
        # Calculate total_amount from items if available
        if self.items:
            calculated_total = sum(item.total_price for item in self.items)
            self.total_amount = validate_decimal(calculated_total)
