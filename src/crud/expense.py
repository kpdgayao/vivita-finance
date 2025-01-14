from datetime import datetime
from uuid import UUID
from typing import List, Optional
from decimal import Decimal

from ..models.expense import (
    ExpenseReimbursementForm,
    ExpenseItem,
    ExpenseFormStatus,
    Voucher,
    VoucherEntry
)
from ..database import get_supabase_client

class ExpenseManager:
    def __init__(self):
        self.supabase = get_supabase_client()

    def create_erf(self, erf: ExpenseReimbursementForm) -> ExpenseReimbursementForm:
        """Create a new Expense Reimbursement Form."""
        data = {
            'employee_id': str(erf.employee_id),
            'designation': erf.designation,
            'date': erf.date.isoformat(),
            'total_amount': str(erf.total_amount),
            'status': erf.status.value if isinstance(erf.status, ExpenseFormStatus) else erf.status,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('expense_reimbursement_forms').insert(data).execute()
        created_erf = result.data[0]
        return ExpenseReimbursementForm(**created_erf)

    def update_erf(self, erf: ExpenseReimbursementForm) -> ExpenseReimbursementForm:
        """Update an existing Expense Reimbursement Form."""
        if not erf.id:
            raise ValueError("ERF ID is required for update")

        data = {
            'employee_id': str(erf.employee_id),
            'designation': erf.designation,
            'date': erf.date.isoformat(),
            'total_amount': str(erf.total_amount),
            'status': erf.status.value if isinstance(erf.status, ExpenseFormStatus) else erf.status,
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('expense_reimbursement_forms').update(data).eq('id', str(erf.id)).execute()
        updated_erf = result.data[0]
        return ExpenseReimbursementForm(**updated_erf)

    def delete_erf(self, erf_id: UUID) -> bool:
        """Delete an Expense Reimbursement Form."""
        result = self.supabase.table('expense_reimbursement_forms').delete().eq('id', str(erf_id)).execute()
        return len(result.data) > 0

    def get_erf(self, erf_id: UUID) -> Optional[ExpenseReimbursementForm]:
        """Get an Expense Reimbursement Form by ID."""
        result = self.supabase.table('expense_reimbursement_forms').select('*').eq('id', str(erf_id)).execute()
        if not result.data:
            return None
        return ExpenseReimbursementForm(**result.data[0])

    def list_erfs(self, employee_id: Optional[UUID] = None, status: Optional[str] = None) -> List[ExpenseReimbursementForm]:
        """List Expense Reimbursement Forms."""
        query = self.supabase.table('expense_reimbursement_forms').select('*')
        
        if employee_id:
            query = query.eq('employee_id', str(employee_id))
        if status:
            query = query.eq('status', status)
            
        result = query.execute()
        return [ExpenseReimbursementForm(**item) for item in result.data]

    def create_expense_item(self, item: ExpenseItem) -> ExpenseItem:
        """Create a new Expense Item."""
        data = {
            'erf_id': str(item.erf_id) if item.erf_id else None,
            'date': item.date.isoformat(),
            'description': item.description,
            'payee': item.payee,
            'amount': str(item.amount),
            'account': item.account,
            'reference_number': item.reference_number,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('expense_items').insert(data).execute()
        created_item = result.data[0]
        return ExpenseItem(**created_item)

    def update_expense_item(self, item: ExpenseItem) -> ExpenseItem:
        """Update an existing Expense Item."""
        if not item.id:
            raise ValueError("Item ID is required for update")

        data = {
            'date': item.date.isoformat(),
            'description': item.description,
            'payee': item.payee,
            'amount': str(item.amount),
            'account': item.account,
            'reference_number': item.reference_number,
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('expense_items').update(data).eq('id', str(item.id)).execute()
        updated_item = result.data[0]
        return ExpenseItem(**updated_item)

    def delete_expense_item(self, item_id: UUID) -> bool:
        """Delete an Expense Item."""
        result = self.supabase.table('expense_items').delete().eq('id', str(item_id)).execute()
        return len(result.data) > 0

    def get_expense_items(self, erf_id: UUID) -> List[ExpenseItem]:
        """Get all Expense Items for an ERF."""
        result = self.supabase.table('expense_items').select('*').eq('erf_id', str(erf_id)).execute()
        return [ExpenseItem(**item) for item in result.data]

    def create_voucher(self, voucher: Voucher) -> Voucher:
        """Create a new Voucher."""
        data = {
            'date': voucher.date.isoformat(),
            'payee': voucher.payee,
            'total_amount': str(voucher.total_amount),
            'particulars': voucher.particulars,
            'prepared_by': str(voucher.prepared_by),
            'bank_name': voucher.bank_name,
            'transaction_type': voucher.transaction_type,
            'reference_number': voucher.reference_number,
            'payee_bank_account': voucher.payee_bank_account,
            'form_type': voucher.form_type,
            'form_number': voucher.form_number,
            'form_date': voucher.form_date.isoformat() if voucher.form_date else None,
            'requested_by': voucher.requested_by,
            'status': voucher.status,
            'voucher_number': voucher.voucher_number,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('vouchers').insert(data).execute()
        created_voucher = result.data[0]
        
        # Create voucher entries
        for entry in voucher.entries:
            entry_data = {
                'voucher_id': created_voucher['id'],
                'account_title': entry.account_title,
                'activity': entry.activity,
                'debit_amount': str(entry.debit_amount) if entry.debit_amount else None,
                'credit_amount': str(entry.credit_amount) if entry.credit_amount else None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self.supabase.table('voucher_entries').insert(entry_data).execute()
        
        return self.get_voucher(UUID(created_voucher['id']))

    def update_voucher(self, voucher: Voucher) -> Voucher:
        """Update an existing Voucher."""
        if not voucher.id:
            raise ValueError("Voucher ID is required for update")

        data = {
            'date': voucher.date.isoformat(),
            'payee': voucher.payee,
            'total_amount': str(voucher.total_amount),
            'particulars': voucher.particulars,
            'bank_name': voucher.bank_name,
            'transaction_type': voucher.transaction_type,
            'reference_number': voucher.reference_number,
            'payee_bank_account': voucher.payee_bank_account,
            'form_type': voucher.form_type,
            'form_number': voucher.form_number,
            'form_date': voucher.form_date.isoformat() if voucher.form_date else None,
            'requested_by': voucher.requested_by,
            'status': voucher.status,
            'voucher_number': voucher.voucher_number,
            'updated_at': datetime.now().isoformat()
        }
        
        result = self.supabase.table('vouchers').update(data).eq('id', str(voucher.id)).execute()
        updated_voucher = result.data[0]
        
        # Update voucher entries
        self.supabase.table('voucher_entries').delete().eq('voucher_id', str(voucher.id)).execute()
        for entry in voucher.entries:
            entry_data = {
                'voucher_id': str(voucher.id),
                'account_title': entry.account_title,
                'activity': entry.activity,
                'debit_amount': str(entry.debit_amount) if entry.debit_amount else None,
                'credit_amount': str(entry.credit_amount) if entry.credit_amount else None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self.supabase.table('voucher_entries').insert(entry_data).execute()
        
        return self.get_voucher(voucher.id)

    def delete_voucher(self, voucher_id: UUID) -> bool:
        """Delete a Voucher and its entries."""
        # Delete entries first due to foreign key constraint
        self.supabase.table('voucher_entries').delete().eq('voucher_id', str(voucher_id)).execute()
        result = self.supabase.table('vouchers').delete().eq('id', str(voucher_id)).execute()
        return len(result.data) > 0

    def get_voucher(self, voucher_id: UUID) -> Optional[Voucher]:
        """Get a Voucher by ID, including its entries."""
        voucher_result = self.supabase.table('vouchers').select('*').eq('id', str(voucher_id)).execute()
        if not voucher_result.data:
            return None
            
        entries_result = self.supabase.table('voucher_entries').select('*').eq('voucher_id', str(voucher_id)).execute()
        entries = [VoucherEntry(**entry) for entry in entries_result.data]
        
        voucher_data = voucher_result.data[0]
        voucher_data['entries'] = entries
        return Voucher(**voucher_data)

    def list_vouchers(self, status: Optional[str] = None) -> List[Voucher]:
        """List Vouchers with optional status filter."""
        query = self.supabase.table('vouchers').select('*')
        if status:
            query = query.eq('status', status)
            
        result = query.execute()
        vouchers = []
        for voucher_data in result.data:
            entries_result = self.supabase.table('voucher_entries').select('*').eq('voucher_id', voucher_data['id']).execute()
            entries = [VoucherEntry(**entry) for entry in entries_result.data]
            voucher_data['entries'] = entries
            vouchers.append(Voucher(**voucher_data))
            
        return vouchers
