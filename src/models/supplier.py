from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

@dataclass
class Supplier:
    id: Optional[UUID] = None
    name: str = ""
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    tax_id: str = ""
    preferred_payment_method: str = ""
    bank_details: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class PurchaseRequestItem:
    id: Optional[UUID] = None
    purchase_request_id: Optional[UUID] = None
    description: str = ""
    quantity: int = 0
    unit: str = ""
    unit_price: Decimal = Decimal('0')
    total_amount: Decimal = Decimal('0')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class PurchaseRequest:
    id: Optional[UUID] = None
    request_number: Optional[str] = None
    date: datetime = datetime.now()
    supplier_id: Optional[UUID] = None
    supplier_name: str = ""
    total_amount: Decimal = Decimal('0')
    status: str = "draft"  # draft, pending, approved, rejected
    remarks: str = ""
    requested_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[PurchaseRequestItem] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
