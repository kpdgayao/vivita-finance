from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from supabase import Client, create_client

from src.config import config
from src.models.expense import ExpenseReimbursementForm, ExpenseItem, Voucher, VoucherEntry

class ExpenseManager:
    def __init__(self):
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )

    def create_erf(self, erf: ExpenseReimbursementForm) -> Optional[ExpenseReimbursementForm]:
        try:
            # Create the ERF
            response = self.supabase.table('expense_reimbursement_forms').insert({
                'employee_id': str(erf.employee_id),
                'designation': erf.designation,
                'date': erf.date.isoformat(),
                'total_amount': str(erf.total_amount),
                'status': erf.status
            }).execute()

            if response.data:
                erf_data = response.data[0]
                erf.id = UUID(erf_data['id'])
                erf.form_number = erf_data['form_number']
                
                # Create expense items if any
                if erf.items:
                    items_data = [{
                        'erf_id': str(erf.id),
                        'date': item.date.isoformat(),
                        'description': item.description,
                        'payee': item.payee,
                        'reference_number': item.reference_number,
                        'amount': str(item.amount),
                        'account': item.account
                    } for item in erf.items]
                    
                    items_response = self.supabase.table('expense_items').insert(items_data).execute()
                    if items_response.data:
                        for i, item_data in enumerate(items_response.data):
                            erf.items[i].id = UUID(item_data['id'])
                            erf.items[i].erf_id = erf.id
                
                return erf
        except Exception as e:
            print(f"Error creating ERF: {str(e)}")
            return None

    def get_erf(self, erf_id: UUID) -> Optional[ExpenseReimbursementForm]:
        try:
            # Get ERF data
            response = self.supabase.table('expense_reimbursement_forms').select('*').eq('id', str(erf_id)).single().execute()
            
            if response.data:
                erf_data = response.data
                
                # Get expense items
                items_response = self.supabase.table('expense_items').select('*').eq('erf_id', str(erf_id)).execute()
                
                items = []
                if items_response.data:
                    for item_data in items_response.data:
                        items.append(ExpenseItem(
                            id=UUID(item_data['id']),
                            erf_id=UUID(item_data['erf_id']),
                            date=datetime.fromisoformat(item_data['date']),
                            description=item_data['description'],
                            payee=item_data['payee'],
                            reference_number=item_data['reference_number'],
                            amount=Decimal(item_data['amount']),
                            account=item_data['account'],
                            created_at=datetime.fromisoformat(item_data['created_at']),
                            updated_at=datetime.fromisoformat(item_data['updated_at'])
                        ))
                
                return ExpenseReimbursementForm(
                    id=UUID(erf_data['id']),
                    form_number=erf_data['form_number'],
                    employee_id=UUID(erf_data['employee_id']),
                    designation=erf_data['designation'],
                    date=datetime.fromisoformat(erf_data['date']),
                    total_amount=Decimal(erf_data['total_amount']),
                    status=erf_data['status'],
                    approved_by=UUID(erf_data['approved_by']) if erf_data['approved_by'] else None,
                    approved_at=datetime.fromisoformat(erf_data['approved_at']) if erf_data['approved_at'] else None,
                    items=items,
                    created_at=datetime.fromisoformat(erf_data['created_at']),
                    updated_at=datetime.fromisoformat(erf_data['updated_at'])
                )
        except Exception as e:
            print(f"Error getting ERF: {str(e)}")
            return None

    def update_erf(self, erf: ExpenseReimbursementForm) -> Optional[ExpenseReimbursementForm]:
        try:
            # Update ERF
            response = self.supabase.table('expense_reimbursement_forms').update({
                'designation': erf.designation,
                'date': erf.date.isoformat(),
                'total_amount': str(erf.total_amount),
                'status': erf.status,
                'approved_by': str(erf.approved_by) if erf.approved_by else None,
                'approved_at': erf.approved_at.isoformat() if erf.approved_at else None
            }).eq('id', str(erf.id)).execute()
            
            if response.data:
                # Update existing items and add new ones
                if erf.items:
                    for item in erf.items:
                        item_data = {
                            'date': item.date.isoformat(),
                            'description': item.description,
                            'payee': item.payee,
                            'reference_number': item.reference_number,
                            'amount': str(item.amount),
                            'account': item.account
                        }
                        
                        if item.id:
                            # Update existing item
                            self.supabase.table('expense_items').update(item_data).eq('id', str(item.id)).execute()
                        else:
                            # Create new item
                            item_data['erf_id'] = str(erf.id)
                            item_response = self.supabase.table('expense_items').insert(item_data).execute()
                            if item_response.data:
                                item.id = UUID(item_response.data[0]['id'])
                                item.erf_id = erf.id
                
                return erf
        except Exception as e:
            print(f"Error updating ERF: {str(e)}")
            return None

    def create_voucher(self, voucher: Voucher) -> Optional[Voucher]:
        try:
            # Create the voucher
            response = self.supabase.table('vouchers').insert({
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
                'status': voucher.status
            }).execute()

            if response.data:
                voucher_data = response.data[0]
                voucher.id = UUID(voucher_data['id'])
                voucher.voucher_number = voucher_data['voucher_number']
                
                # Create voucher entries if any
                if voucher.entries:
                    entries_data = [{
                        'voucher_id': str(voucher.id),
                        'account_title': entry.account_title,
                        'activity': entry.activity,
                        'debit_amount': str(entry.debit_amount) if entry.debit_amount else None,
                        'credit_amount': str(entry.credit_amount) if entry.credit_amount else None
                    } for entry in voucher.entries]
                    
                    entries_response = self.supabase.table('voucher_entries').insert(entries_data).execute()
                    if entries_response.data:
                        for i, entry_data in enumerate(entries_response.data):
                            voucher.entries[i].id = UUID(entry_data['id'])
                            voucher.entries[i].voucher_id = voucher.id
                
                return voucher
        except Exception as e:
            print(f"Error creating voucher: {str(e)}")
            return None

    def get_voucher(self, voucher_id: UUID) -> Optional[Voucher]:
        try:
            # Get voucher data
            response = self.supabase.table('vouchers').select('*').eq('id', str(voucher_id)).single().execute()
            
            if response.data:
                voucher_data = response.data
                
                # Get voucher entries
                entries_response = self.supabase.table('voucher_entries').select('*').eq('voucher_id', str(voucher_id)).execute()
                
                entries = []
                if entries_response.data:
                    for entry_data in entries_response.data:
                        entries.append(VoucherEntry(
                            id=UUID(entry_data['id']),
                            voucher_id=UUID(entry_data['voucher_id']),
                            account_title=entry_data['account_title'],
                            activity=entry_data['activity'],
                            debit_amount=Decimal(entry_data['debit_amount']) if entry_data['debit_amount'] else None,
                            credit_amount=Decimal(entry_data['credit_amount']) if entry_data['credit_amount'] else None,
                            created_at=datetime.fromisoformat(entry_data['created_at']),
                            updated_at=datetime.fromisoformat(entry_data['updated_at'])
                        ))
                
                return Voucher(
                    id=UUID(voucher_data['id']),
                    voucher_number=voucher_data['voucher_number'],
                    date=datetime.fromisoformat(voucher_data['date']),
                    payee=voucher_data['payee'],
                    total_amount=Decimal(voucher_data['total_amount']),
                    particulars=voucher_data['particulars'],
                    prepared_by=UUID(voucher_data['prepared_by']),
                    bank_name=voucher_data['bank_name'],
                    transaction_type=voucher_data['transaction_type'],
                    reference_number=voucher_data['reference_number'],
                    payee_bank_account=voucher_data['payee_bank_account'],
                    form_type=voucher_data['form_type'],
                    form_number=voucher_data['form_number'],
                    form_date=datetime.fromisoformat(voucher_data['form_date']) if voucher_data['form_date'] else None,
                    requested_by=voucher_data['requested_by'],
                    status=voucher_data['status'],
                    entries=entries,
                    created_at=datetime.fromisoformat(voucher_data['created_at']),
                    updated_at=datetime.fromisoformat(voucher_data['updated_at'])
                )
        except Exception as e:
            print(f"Error getting voucher: {str(e)}")
            return None
