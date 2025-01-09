from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from src.config import config
from src.models import Supplier, PurchaseRequest, PurchaseRequestItem
from supabase import create_client, Client
import streamlit as st

class UserManager:
    def __init__(self):
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )
    
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

class SupplierManager:
    def __init__(self):
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )
        
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
            
    def get_suppliers(self) -> List[dict]:
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

class PurchaseRequestManager:
    def __init__(self):
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
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
                "status": pr.status,
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
    
    def get_purchase_requests(self, status: Optional[str] = None) -> List[PurchaseRequest]:
        try:
            query = self.supabase.table('purchase_requests').select("*")
            if status:
                query = query.eq('status', status)
            
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
                    status=pr_data['status'],
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
                status=pr_data['status'],
                total_amount=Decimal(str(pr_data['total_amount'])) if pr_data['total_amount'] else None,
                remarks=pr_data.get('remarks'),
                items=items,
                created_at=datetime.fromisoformat(pr_data['created_at']),
                updated_at=datetime.fromisoformat(pr_data['updated_at'])
            )
            
        except Exception as e:
            st.error(f"Error fetching purchase request: {str(e)}")
            return None
