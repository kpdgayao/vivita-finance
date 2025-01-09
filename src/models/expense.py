from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from uuid import UUID
from enum import Enum
import re

def validate_decimal(value: Decimal) -> Decimal:
    """Validate decimal to ensure it matches database precision (15,2)"""
    if value is None:
        return Decimal('0')
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class ExpenseFormStatus(Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

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

    def __post_init__(self):
        # Validate decimal fields
        self.amount = validate_decimal(self.amount)

    @property
    def total(self) -> Decimal:
        """Calculate total for this item"""
        return validate_decimal(self.amount)

@dataclass
class ExpenseReimbursementForm:
    employee_id: UUID
    designation: str
    date: datetime
    form_number: Optional[str] = None
    total_amount: Decimal = Decimal('0')
    status: ExpenseFormStatus = ExpenseFormStatus.DRAFT
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    items: List[ExpenseItem] = field(default_factory=list)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Convert status string to enum if needed
        if isinstance(self.status, str):
            self.status = ExpenseFormStatus(self.status)
        
        # Validate total_amount
        self.total_amount = validate_decimal(self.total_amount)
        
        # Calculate total_amount from items if available and no total provided
        if self.items and self.total_amount == Decimal('0'):
            self.total_amount = self.calculate_total()

        # Validate form number format
        if self.form_number and not re.match(r'^[0-9]{4}-[0-9]{3}$', self.form_number):
            raise ValueError("Form number must be in format YYYY-NNN")

    def calculate_total(self) -> Decimal:
        """Calculate total amount from all items"""
        return validate_decimal(sum(item.total for item in self.items))

    def add_item(self, item: ExpenseItem) -> None:
        """Add an item and update total"""
        self.items.append(item)
        self.total_amount = self.calculate_total()

    def remove_item(self, index: int) -> None:
        """Remove an item and update total"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.total_amount = self.calculate_total()

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

    def __post_init__(self):
        # Validate decimal fields
        if self.debit_amount is not None:
            self.debit_amount = validate_decimal(self.debit_amount)
        if self.credit_amount is not None:
            self.credit_amount = validate_decimal(self.credit_amount)

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
    entries: List[VoucherEntry] = field(default_factory=list)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Validate decimal fields
        self.total_amount = validate_decimal(self.total_amount)
        
        # Calculate total from entries if available
        if self.entries:
            debit_total = sum((e.debit_amount or Decimal('0')) for e in self.entries)
            credit_total = sum((e.credit_amount or Decimal('0')) for e in self.entries)
            self.total_amount = validate_decimal(max(debit_total, credit_total))
