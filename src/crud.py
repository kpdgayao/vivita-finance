from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from src.config import config
from src.models.supplier import Supplier
from src.models.purchase_request import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
    validate_decimal
)
from src.models.expense import (
    ExpenseReimbursementForm,
    ExpenseItem,
    ExpenseFormStatus
)
from supabase import create_client, Client
import streamlit as st

class BaseManager:
    """Base class for all managers"""
    def __init__(self):
        # Use the existing Supabase client from session state
        if not st.session_state.get('supabase'):
            try:
                st.session_state.supabase = create_client(
                    supabase_url=st.secrets["SUPABASE_URL"],
                    supabase_key=st.secrets["SUPABASE_KEY"]
                )
            except Exception as e:
                st.error(f"Failed to initialize Supabase client: {str(e)}")
                return
                
        self.supabase = st.session_state.supabase

class UserManager(BaseManager):
    def get_or_create_user(self, email: str, full_name: str, role: str) -> Optional[Dict]:
        try:
            # Try to get existing user
            response = self.supabase.table('users').select("*").eq('email', email).execute()
            
            if response.data:
                return response.data[0]
            
            # Create new user if not exists
            response = self.supabase.table('users').insert({
                'email': email,
                'full_name': full_name,
                'role': role
            }).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            st.error(f"Error managing user: {str(e)}")
            return None

class SupplierManager(BaseManager):
    def create_supplier(self, supplier: Supplier) -> Optional[Supplier]:
        try:
            response = self.supabase.table('suppliers').insert({
                "name": supplier.name,
                "contact_person": supplier.contact_person,
                "phone": supplier.phone,
                "email": supplier.email,
                "address": supplier.address,
                "tax_id": supplier.tax_id,
                "preferred_payment_method": supplier.preferred_payment_method,
                "bank_details": supplier.bank_details
            }).execute()
            
            return Supplier(**response.data[0]) if response.data else None
        except Exception as e:
            st.error(f"Error creating supplier: {str(e)}")
            return None
            
    def update_supplier(self, supplier: Supplier) -> Optional[Supplier]:
        try:
            if not supplier.id:
                st.error("Cannot update supplier: No ID provided")
                return None
                
            response = self.supabase.table('suppliers').update({
                "name": supplier.name,
                "contact_person": supplier.contact_person,
                "phone": supplier.phone,
                "email": supplier.email,
                "address": supplier.address,
                "tax_id": supplier.tax_id,
                "preferred_payment_method": supplier.preferred_payment_method,
                "bank_details": supplier.bank_details
            }).eq('id', str(supplier.id)).execute()
            
            return Supplier(**response.data[0]) if response.data else None
        except Exception as e:
            st.error(f"Error updating supplier: {str(e)}")
            return None
            
    def delete_supplier(self, supplier_id: UUID) -> bool:
        try:
            # First check if this supplier is referenced in any purchase requests
            pr_response = self.supabase.table('purchase_requests').select("id").eq('supplier_id', str(supplier_id)).execute()
            if pr_response.data:
                st.error("Cannot delete supplier: This supplier has associated purchase requests")
                return False
            
            # Delete the supplier
            response = self.supabase.table('suppliers').delete().eq('id', str(supplier_id)).execute()
            
            if not response.data:
                st.error("Failed to delete supplier. No supplier found with the given ID.")
                return False
                
            return True
        except Exception as e:
            st.error(f"Error deleting supplier: {str(e)}")
            return False
            
    def get_suppliers(self) -> List[Dict[str, Any]]:
        try:
            response = self.supabase.table('suppliers').select("*").execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching suppliers: {str(e)}")
            return []
            
    def get_supplier(self, supplier_id: UUID) -> Optional[Supplier]:
        try:
            response = self.supabase.table('suppliers').select("*").eq('id', str(supplier_id)).execute()
            return Supplier(**response.data[0]) if response.data else None
        except Exception as e:
            st.error(f"Error fetching supplier: {str(e)}")
            return None

class PurchaseRequestManager(BaseManager):
    def __init__(self):
        super().__init__()
        # Set the session token if available
        if st.session_state.get('session'):
            self.supabase.auth.set_session(
                st.session_state.session['access_token'],
                st.session_state.session['refresh_token']
            )
    
    def generate_form_number(self) -> str:
        """Generate a new PROF number"""
        try:
            # Get the current count of PRs
            response = self.supabase.table('purchase_requests').select("id").execute()
            count = len(response.data) if response.data else 0
            
            # Generate form number: PROF-YYYY-MM-XXXX
            now = datetime.now()
            return f"PROF-{now.year}-{now.month:02d}-{count+1:04d}"
        except Exception as e:
            st.error(f"Error generating form number: {str(e)}")
            return f"PROF-ERROR-{datetime.now().timestamp()}"
    
    def create_purchase_request(self, pr: PurchaseRequest) -> Optional[PurchaseRequest]:
        try:
            # Generate form number if not provided
            if not pr.form_number:
                pr.form_number = self.generate_form_number()
            
            # First, create the purchase request
            pr_data = {
                "form_number": pr.form_number,
                "requestor_id": str(pr.requestor_id),
                "supplier_id": str(pr.supplier_id),
                "status": pr.status.value,  # Use enum value
                "total_amount": float(pr.total_amount) if pr.total_amount else None,
                "remarks": pr.remarks
            }
            
            pr_response = self.supabase.table('purchase_requests').insert(pr_data).execute()
            if not pr_response.data:
                raise Exception("Failed to create purchase request")
            
            created_pr = pr_response.data[0]
            
            # Then, create all items
            if pr.items:
                for item in pr.items:
                    item_data = {
                        "purchase_request_id": created_pr['id'],
                        "item_description": item.item_description,
                        "quantity": float(item.quantity),
                        "unit": item.unit,
                        "unit_price": float(item.unit_price),
                        "total_price": float(item.total_price),
                        "account_code": item.account_code,
                        "remarks": item.remarks
                    }
                    
                    item_response = self.supabase.table('purchase_request_items').insert(item_data).execute()
                    if not item_response.data:
                        raise Exception("Failed to create purchase request item")
            
            # Return the complete purchase request with items
            return self.get_purchase_request(UUID(created_pr['id']))
            
        except Exception as e:
            st.error(f"Error creating purchase request: {str(e)}")
            return None
    
    def get_purchase_requests(self, status: Optional[PurchaseRequestStatus] = None) -> List[PurchaseRequest]:
        try:
            query = self.supabase.table('purchase_requests').select("*")
            if status:
                query = query.eq('status', status.value)  # Use enum value
            
            response = query.execute()
            
            purchase_requests = []
            for pr_data in response.data:
                # Get items for this PR
                items_response = self.supabase.table('purchase_request_items')\
                    .select("*")\
                    .eq('purchase_request_id', pr_data['id'])\
                    .execute()
                
                # Convert items
                items = []
                for item_data in items_response.data:
                    items.append(PurchaseRequestItem(
                        id=UUID(item_data['id']),
                        purchase_request_id=UUID(item_data['purchase_request_id']),
                        item_description=item_data['item_description'],
                        quantity=Decimal(str(item_data['quantity'])),
                        unit=item_data['unit'],
                        unit_price=Decimal(str(item_data['unit_price'])),
                        total_price=Decimal(str(item_data['total_price'])),
                        account_code=item_data.get('account_code'),
                        remarks=item_data.get('remarks'),
                        created_at=datetime.fromisoformat(item_data['created_at']),
                        updated_at=datetime.fromisoformat(item_data['updated_at'])
                    ))
                
                # Convert PR
                pr = PurchaseRequest(
                    id=UUID(pr_data['id']),
                    form_number=pr_data['form_number'],
                    requestor_id=UUID(pr_data['requestor_id']),
                    supplier_id=UUID(pr_data['supplier_id']),
                    status=PurchaseRequestStatus(pr_data['status']),  # Convert to enum
                    total_amount=Decimal(str(pr_data['total_amount'])) if pr_data['total_amount'] else None,
                    remarks=pr_data.get('remarks'),
                    items=items,
                    created_at=datetime.fromisoformat(pr_data['created_at']),
                    updated_at=datetime.fromisoformat(pr_data['updated_at'])
                )
                purchase_requests.append(pr)
            
            return purchase_requests
            
        except Exception as e:
            st.error(f"Error fetching purchase requests: {str(e)}")
            return []
    
    def get_purchase_request(self, pr_id: UUID) -> Optional[PurchaseRequest]:
        try:
            response = self.supabase.table('purchase_requests').select("*").eq('id', str(pr_id)).execute()
            if not response.data:
                return None
                
            pr_data = response.data[0]
            
            # Get items
            items_response = self.supabase.table('purchase_request_items')\
                .select("*")\
                .eq('purchase_request_id', pr_data['id'])\
                .execute()
            
            # Convert items
            items = []
            for item_data in items_response.data:
                items.append(PurchaseRequestItem(
                    id=UUID(item_data['id']),
                    purchase_request_id=UUID(item_data['purchase_request_id']),
                    item_description=item_data['item_description'],
                    quantity=Decimal(str(item_data['quantity'])),
                    unit=item_data['unit'],
                    unit_price=Decimal(str(item_data['unit_price'])),
                    total_price=Decimal(str(item_data['total_price'])),
                    account_code=item_data.get('account_code'),
                    remarks=item_data.get('remarks'),
                    created_at=datetime.fromisoformat(item_data['created_at']),
                    updated_at=datetime.fromisoformat(item_data['updated_at'])
                ))
            
            # Convert PR
            return PurchaseRequest(
                id=UUID(pr_data['id']),
                form_number=pr_data['form_number'],
                requestor_id=UUID(pr_data['requestor_id']),
                supplier_id=UUID(pr_data['supplier_id']),
                status=PurchaseRequestStatus(pr_data['status']),  # Convert to enum
                total_amount=Decimal(str(pr_data['total_amount'])) if pr_data['total_amount'] else None,
                remarks=pr_data.get('remarks'),
                items=items,
                created_at=datetime.fromisoformat(pr_data['created_at']),
                updated_at=datetime.fromisoformat(pr_data['updated_at'])
            )
            
        except Exception as e:
            st.error(f"Error fetching purchase request: {str(e)}")
            return None

class ExpenseManager(BaseManager):
    def generate_form_number(self) -> str:
        """Generate a new ERF number in format YYYY-NNN"""
        try:
            # Get current year
            year = datetime.now().year
            
            # Get count of ERFs for this year
            response = self.supabase.table('expense_reimbursement_forms')\
                .select("form_number")\
                .ilike('form_number', f'{year}-%')\
                .execute()
            
            count = len(response.data) if response.data else 0
            
            # Generate form number: YYYY-NNN
            return f"{year}-{(count + 1):03d}"
        except Exception as e:
            st.error(f"Error generating form number: {str(e)}")
            return None

    def create_expense_form(self, erf: ExpenseReimbursementForm) -> Optional[ExpenseReimbursementForm]:
        try:
            # Generate form number if not provided
            if not erf.form_number:
                erf.form_number = self.generate_form_number()
                if not erf.form_number:
                    raise Exception("Failed to generate form number")

            # Ensure total is calculated
            erf.total_amount = erf.calculate_total()

            # Create ERF
            erf_data = {
                "form_number": erf.form_number,
                "employee_id": str(erf.employee_id),
                "designation": erf.designation,
                "date": erf.date.strftime("%Y-%m-%d"),
                "total_amount": float(erf.total_amount),
                "status": erf.status.value,  # Use enum value
                "approved_by": str(erf.approved_by) if erf.approved_by else None,
                "approved_at": erf.approved_at.isoformat() if erf.approved_at else None
            }
            
            erf_response = self.supabase.table('expense_reimbursement_forms').insert(erf_data).execute()
            if not erf_response.data:
                raise Exception("Failed to create expense reimbursement form")
            
            created_erf = erf_response.data[0]
            
            # Create expense items
            if erf.items:
                for item in erf.items:
                    item_data = {
                        "erf_id": created_erf['id'],
                        "date": item.date.strftime("%Y-%m-%d"),
                        "description": item.description,
                        "payee": item.payee,
                        "reference_number": item.reference_number,
                        "amount": float(item.total),  # Use item.total property
                        "account": item.account
                    }
                    
                    item_response = self.supabase.table('expense_items').insert(item_data).execute()
                    if not item_response.data:
                        raise Exception("Failed to create expense item")
            
            # Return the complete ERF with items
            return self.get_expense_form(UUID(created_erf['id']))
            
        except Exception as e:
            st.error(f"Error creating expense form: {str(e)}")
            return None

    def get_expense_forms(self, status: Optional[ExpenseFormStatus] = None) -> List[ExpenseReimbursementForm]:
        try:
            query = self.supabase.table('expense_reimbursement_forms').select("*")
            if status:
                query = query.eq('status', status.value)  # Use enum value
            
            response = query.execute()
            
            forms = []
            for erf_data in response.data:
                # Get items for this ERF
                items_response = self.supabase.table('expense_items')\
                    .select("*")\
                    .eq('erf_id', erf_data['id'])\
                    .execute()
                
                # Convert items
                items = []
                for item_data in items_response.data:
                    items.append(ExpenseItem(
                        id=UUID(item_data['id']),
                        erf_id=UUID(item_data['erf_id']),
                        date=datetime.strptime(item_data['date'], "%Y-%m-%d"),
                        description=item_data['description'],
                        payee=item_data['payee'],
                        reference_number=item_data.get('reference_number'),
                        amount=Decimal(str(item_data['amount'])),
                        account=item_data['account'],
                        created_at=datetime.fromisoformat(item_data['created_at']),
                        updated_at=datetime.fromisoformat(item_data['updated_at'])
                    ))
                
                # Convert ERF
                erf = ExpenseReimbursementForm(
                    id=UUID(erf_data['id']),
                    form_number=erf_data['form_number'],
                    employee_id=UUID(erf_data['employee_id']),
                    designation=erf_data['designation'],
                    date=datetime.strptime(erf_data['date'], "%Y-%m-%d"),
                    total_amount=Decimal(str(erf_data['total_amount'])),
                    status=ExpenseFormStatus(erf_data['status']),  # Convert to enum
                    approved_by=UUID(erf_data['approved_by']) if erf_data.get('approved_by') else None,
                    approved_at=datetime.fromisoformat(erf_data['approved_at']) if erf_data.get('approved_at') else None,
                    items=items,
                    created_at=datetime.fromisoformat(erf_data['created_at']),
                    updated_at=datetime.fromisoformat(erf_data['updated_at'])
                )
                forms.append(erf)
            
            return forms
            
        except Exception as e:
            st.error(f"Error fetching expense forms: {str(e)}")
            return []

    def get_expense_form(self, erf_id: UUID) -> Optional[ExpenseReimbursementForm]:
        try:
            response = self.supabase.table('expense_reimbursement_forms')\
                .select("*")\
                .eq('id', str(erf_id))\
                .execute()
                
            if not response.data:
                return None
                
            erf_data = response.data[0]
            
            # Get items
            items_response = self.supabase.table('expense_items')\
                .select("*")\
                .eq('erf_id', erf_data['id'])\
                .execute()
            
            # Convert items
            items = []
            for item_data in items_response.data:
                items.append(ExpenseItem(
                    id=UUID(item_data['id']),
                    erf_id=UUID(item_data['erf_id']),
                    date=datetime.strptime(item_data['date'], "%Y-%m-%d"),
                    description=item_data['description'],
                    payee=item_data['payee'],
                    reference_number=item_data.get('reference_number'),
                    amount=Decimal(str(item_data['amount'])),
                    account=item_data['account'],
                    created_at=datetime.fromisoformat(item_data['created_at']),
                    updated_at=datetime.fromisoformat(item_data['updated_at'])
                ))
            
            # Convert ERF
            return ExpenseReimbursementForm(
                id=UUID(erf_data['id']),
                form_number=erf_data['form_number'],
                employee_id=UUID(erf_data['employee_id']),
                designation=erf_data['designation'],
                date=datetime.strptime(erf_data['date'], "%Y-%m-%d"),
                total_amount=Decimal(str(erf_data['total_amount'])),
                status=ExpenseFormStatus(erf_data['status']),  # Convert to enum
                approved_by=UUID(erf_data['approved_by']) if erf_data.get('approved_by') else None,
                approved_at=datetime.fromisoformat(erf_data['approved_at']) if erf_data.get('approved_at') else None,
                items=items,
                created_at=datetime.fromisoformat(erf_data['created_at']),
                updated_at=datetime.fromisoformat(erf_data['updated_at'])
            )
            
        except Exception as e:
            st.error(f"Error fetching expense form: {str(e)}")
            return None

    def update_expense_form_status(self, erf_id: UUID, status: ExpenseFormStatus, approved_by: Optional[UUID] = None) -> bool:
        try:
            update_data = {
                "status": status.value,  # Use enum value
                "approved_by": str(approved_by) if approved_by else None,
                "approved_at": datetime.now().isoformat() if status == ExpenseFormStatus.APPROVED else None
            }
            
            response = self.supabase.table('expense_reimbursement_forms')\
                .update(update_data)\
                .eq('id', str(erf_id))\
                .execute()
            
            return bool(response.data)
            
        except Exception as e:
            st.error(f"Error updating expense form status: {str(e)}")
            return False
