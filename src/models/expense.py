from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

@dataclass
class ExpenseItem:
    date: datetime
    description: str
    payee: str
    amount: Decimal
    account: str
    reference_number: Optional[str] = None
    id: Optional[UUID] = None
    erf_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ExpenseReimbursementForm:
    employee_id: UUID
    designation: str
    date: datetime
    form_number: Optional[str] = None
    total_amount: Optional[Decimal] = Decimal('0')
    status: str = 'draft'
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    items: Optional[List[ExpenseItem]] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class VoucherEntry:
    account_title: str
    activity: Optional[str]
    debit_amount: Optional[Decimal]
    credit_amount: Optional[Decimal]
    id: Optional[UUID] = None
    voucher_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Voucher:
    date: datetime
    payee: str
    total_amount: Decimal
    particulars: str
    prepared_by: UUID
    bank_name: Optional[str] = None
    transaction_type: Optional[str] = None
    reference_number: Optional[str] = None
    payee_bank_account: Optional[str] = None
    form_type: Optional[str] = None
    form_number: Optional[str] = None
    form_date: Optional[datetime] = None
    requested_by: Optional[str] = None
    status: str = 'draft'
    voucher_number: Optional[str] = None
    entries: Optional[List[VoucherEntry]] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
