from dataclasses import dataclass
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
from uuid import UUID

@dataclass
class User:
    email: str
    full_name: str
    role: str
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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

@dataclass
class PurchaseRequest:
    form_number: str
    requestor_id: UUID
    supplier_id: UUID
    status: str = 'draft'
    total_amount: Optional[Decimal] = None
    remarks: Optional[str] = None
    items: Optional[List[PurchaseRequestItem]] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Supplier:
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    preferred_payment_method: Optional[str] = None
    bank_details: Optional[Dict] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
