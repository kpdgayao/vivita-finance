from typing import List, Optional, Dict, Tuple
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from src.models import PurchaseRequest, PurchaseRequestStatus, AuditEntry, PurchaseRequestItem
from ..database import get_supabase_client

class PurchaseRequestManager:
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def generate_form_number(self) -> str:
        """Generate a new PRF number using database sequence"""
        try:
            result = self.supabase.rpc('generate_prf_number').execute()
            if result.data:
                return result.data[0]
            raise Exception("Failed to generate form number")
        except Exception as e:
            print(f"Error generating form number: {str(e)}")
            raise
    
    def create_purchase_request(self, pr: PurchaseRequest) -> Optional[PurchaseRequest]:
        """Create a new purchase request with retry logic for form number conflicts"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Generate form number if not provided
                if not pr.form_number:
                    pr.form_number = self.generate_form_number()
                
                # Insert purchase request
                pr_data = {
                    'form_number': pr.form_number,
                    'requestor_id': str(pr.requestor_id),
                    'supplier_id': str(pr.supplier_id),
                    'status': pr.status.value,
                    'total_amount': float(pr.total_amount) if pr.total_amount else None,
                    'remarks': pr.remarks
                }
                
                if pr.id:
                    # Update existing PRF
                    result = self.supabase.table('purchase_requests')\
                        .update(pr_data)\
                        .eq('id', str(pr.id))\
                        .execute()
                else:
                    # Create new PRF
                    result = self.supabase.table('purchase_requests')\
                        .insert(pr_data)\
                        .execute()
                
                if not result.data:
                    return None
                
                pr_id = UUID(result.data[0]['id'])
                
                # Insert items if present
                if pr.items:
                    items_data = []
                    for item in pr.items:
                        items_data.append({
                            'purchase_request_id': str(pr_id),
                            'item_description': item.item_description,
                            'quantity': float(item.quantity),
                            'unit': item.unit,
                            'unit_price': float(item.unit_price),
                            'total_price': float(item.total_price),
                            'account_code': item.account_code,
                            'remarks': item.remarks
                        })
                    
                    # Delete existing items if updating
                    if pr.id:
                        self.supabase.table('purchase_request_items')\
                            .delete()\
                            .eq('purchase_request_id', str(pr_id))\
                            .execute()
                    
                    # Insert new items
                    self.supabase.table('purchase_request_items')\
                        .insert(items_data)\
                        .execute()
                
                # Add audit entry
                action = "Updated purchase request" if pr.id else "Created purchase request"
                self._add_audit_entry(pr_id, action)
                
                return self.get_purchase_request(pr_id)
                
            except Exception as e:
                error_str = str(e)
                if "'code': '23505'" in error_str and 'purchase_requests_form_number_key' in error_str:
                    # Duplicate form number, retry with a new one
                    retry_count += 1
                    pr.form_number = None  # Reset form number to generate a new one
                    continue
                else:
                    # Some other error occurred
                    print(f"Error creating/updating purchase request: {error_str}")
                    return None
        
        print("Failed to create purchase request after multiple retries")
        return None
    
    def get_purchase_request(self, pr_id: UUID) -> Optional[PurchaseRequest]:
        """Get a purchase request by ID"""
        try:
            # Get purchase request
            result = self.supabase.table('purchase_requests')\
                .select('*')\
                .eq('id', str(pr_id))\
                .single()\
                .execute()
            
            if not result.data:
                return None
            
            # Get items
            items_result = self.supabase.table('purchase_request_items')\
                .select('*')\
                .eq('purchase_request_id', str(pr_id))\
                .execute()
            
            pr_data = result.data
            
            # Convert items to PurchaseRequestItem objects
            if items_result.data:
                pr_data['items'] = [
                    PurchaseRequestItem(
                        purchase_request_id=UUID(item['purchase_request_id']),
                        item_description=item['item_description'],
                        quantity=Decimal(str(item['quantity'])),
                        unit=item['unit'],
                        unit_price=Decimal(str(item['unit_price'])),
                        total_price=Decimal(str(item['total_price'])),
                        account_code=item.get('account_code'),
                        remarks=item.get('remarks'),
                        id=UUID(item['id']) if item.get('id') else None,
                        created_at=datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) if item.get('created_at') else None,
                        updated_at=datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00')) if item.get('updated_at') else None
                    )
                    for item in items_result.data
                ]
            else:
                pr_data['items'] = []
            
            # Convert datetime strings to datetime objects
            if pr_data.get('created_at'):
                pr_data['created_at'] = datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00'))
            if pr_data.get('updated_at'):
                pr_data['updated_at'] = datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00'))
            
            return PurchaseRequest(**pr_data)
            
        except Exception as e:
            print(f"Error getting purchase request: {str(e)}")
            return None
    
    def get_purchase_requests(self, filters=None, page=1, page_size=10) -> Tuple[List[PurchaseRequest], int]:
        """Get purchase requests with pagination and filters.
        
        Args:
            filters (dict, optional): Filter conditions for PRFs. Defaults to None.
            page (int, optional): Page number, starting from 1. Defaults to 1.
            page_size (int, optional): Number of items per page. Defaults to 10.
            
        Returns:
            tuple[list[PurchaseRequest], int]: List of PRFs and total count
        """
        try:
            # First get total count
            count_query = self.supabase.table('purchase_requests').select('id', count='exact')
            
            if filters:
                if filters.get('status'):
                    # Convert status values to list if not already
                    status_values = filters['status']
                    if isinstance(status_values, str):
                        status_values = [status_values]
                    count_query = count_query.in_('status', status_values)
                if filters.get('start_date'):
                    count_query = count_query.gte('created_at', filters['start_date'].isoformat())
                if filters.get('end_date'):
                    count_query = count_query.lte('created_at', filters['end_date'].isoformat())
                if filters.get('search'):
                    count_query = count_query.or_(
                        f"form_number.ilike.%{filters['search']}%,"
                        f"supplier_id.eq.{filters['search']}"
                    )
                if filters.get('requestor_id'):
                    count_query = count_query.eq('requestor_id', str(filters['requestor_id']))
            
            count_result = count_query.execute()
            total_count = len(count_result.data) if count_result.data else 0
            
            # Now get the actual data with pagination
            query = self.supabase.table('purchase_requests').select('*')
            
            if filters:
                if filters.get('status'):
                    query = query.in_('status', status_values)
                if filters.get('start_date'):
                    query = query.gte('created_at', filters['start_date'].isoformat())
                if filters.get('end_date'):
                    query = query.lte('created_at', filters['end_date'].isoformat())
                if filters.get('search'):
                    query = query.or_(
                        f"form_number.ilike.%{filters['search']}%,"
                        f"supplier_id.eq.{filters['search']}"
                    )
                if filters.get('requestor_id'):
                    query = query.eq('requestor_id', str(filters['requestor_id']))
            
            # Add pagination
            query = query\
                .range((page - 1) * page_size, page * page_size - 1)\
                .order('created_at', desc=True)
            
            result = query.execute()
            
            if not result.data:
                return [], total_count
            
            # Get all items for these PRFs
            pr_ids = [pr['id'] for pr in result.data]
            items_result = self.supabase.table('purchase_request_items')\
                .select('*')\
                .in_('purchase_request_id', pr_ids)\
                .execute()
            
            # Group items by PR ID
            items_by_pr = {}
            if items_result.data:
                for item in items_result.data:
                    pr_id = item['purchase_request_id']
                    if pr_id not in items_by_pr:
                        items_by_pr[pr_id] = []
                    items_by_pr[pr_id].append(
                        PurchaseRequestItem(
                            purchase_request_id=UUID(item['purchase_request_id']),
                            item_description=item['item_description'],
                            quantity=Decimal(str(item['quantity'])),
                            unit=item['unit'],
                            unit_price=Decimal(str(item['unit_price'])),
                            total_price=Decimal(str(item['total_price'])),
                            account_code=item.get('account_code'),
                            remarks=item.get('remarks'),
                            id=UUID(item['id']) if item.get('id') else None,
                            created_at=datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) if item.get('created_at') else None,
                            updated_at=datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00')) if item.get('updated_at') else None
                        )
                    )
            
            # Create PurchaseRequest objects
            purchase_requests = []
            for pr_data in result.data:
                # Convert datetime strings to datetime objects
                if pr_data.get('created_at'):
                    pr_data['created_at'] = datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00'))
                if pr_data.get('updated_at'):
                    pr_data['updated_at'] = datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00'))
                    
                pr_data['items'] = items_by_pr.get(pr_data['id'], [])
                purchase_requests.append(PurchaseRequest(**pr_data))
            
            return purchase_requests, total_count
        except Exception as e:
            print(f"Error getting purchase requests: {str(e)}")
            return [], 0
    
    def update_purchase_request_status(
        self,
        pr_id: UUID,
        status: PurchaseRequestStatus,
        remarks: Optional[str] = None
    ) -> bool:
        """Update purchase request status"""
        try:
            # Get current status
            current_pr = self.get_purchase_request(pr_id)
            if not current_pr:
                return False
            
            # Validate status transition
            if not self._is_valid_status_transition(current_pr.status, status):
                return False
            
            update_data = {'status': status.value}
            if remarks:
                update_data['remarks'] = remarks
            
            result = self.supabase.table('purchase_requests')\
                .update(update_data)\
                .eq('id', str(pr_id))\
                .execute()
            
            if result.data:
                # Add audit entry
                self._add_audit_entry(
                    pr_id,
                    f"Updated status to {status.value}",
                    remarks
                )
                return True
            return False
            
        except Exception as e:
            print(f"Error updating purchase request status: {str(e)}")
            return False
    
    def delete_purchase_request(self, pr_id: UUID) -> bool:
        """Delete a purchase request"""
        try:
            # Delete items first
            self.supabase.table('purchase_request_items')\
                .delete()\
                .eq('purchase_request_id', str(pr_id))\
                .execute()
            
            # Delete purchase request
            result = self.supabase.table('purchase_requests')\
                .delete()\
                .eq('id', str(pr_id))\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error deleting purchase request: {str(e)}")
            return False
    
    def get_suppliers(self) -> List[Dict]:
        """Get list of suppliers"""
        result = self.supabase.table('suppliers')\
            .select('id, name')\
            .order('name')\
            .execute()
        
        return result.data if result.data else []

    def get_supplier_name(self, supplier_id: UUID) -> Optional[str]:
        """Get supplier name by ID"""
        if not supplier_id:
            return None
        
        result = self.supabase.table('suppliers')\
            .select('name')\
            .eq('id', str(supplier_id))\
            .limit(1)\
            .execute()
        
        return result.data[0]['name'] if result.data else None

    def get_requestor_name(self, requestor_id: UUID) -> Optional[str]:
        """Get requestor name by ID"""
        if not requestor_id:
            return None
        
        try:
            result = self.supabase.table('profiles')\
                .select('first_name, last_name')\
                .eq('id', str(requestor_id))\
                .limit(1)\
                .execute()
            
            if result.data:
                profile = result.data[0]
                return f"{profile['first_name']} {profile['last_name']}"
            
            return None
            
        except Exception as e:
            print(f"Error getting requestor name: {str(e)}")
            return None
    
    def get_audit_trail(self, pr_id: UUID) -> List[AuditEntry]:
        """Get audit trail for a purchase request"""
        try:
            result = self.supabase.table('purchase_request_audit')\
                .select("*")\
                .eq('purchase_request_id', str(pr_id))\
                .order('created_at', desc=True)\
                .execute()
            
            if not result.data:
                return []
            
            return [AuditEntry(**entry) for entry in result.data]
            
        except Exception as e:
            print(f"Error getting audit trail: {str(e)}")
            return []
    
    def _add_audit_entry(
        self,
        pr_id: UUID,
        action: str,
        details: Optional[str] = None
    ) -> bool:
        """Add an audit entry"""
        try:
            import streamlit as st
            
            if 'user' not in st.session_state:
                print("No user in session")
                return False
                
            audit_data = {
                'purchase_request_id': str(pr_id),
                'action': action,
                'details': details,
                'user_id': str(st.session_state.user['id'])
            }
            
            result = self.supabase.table('purchase_request_audit')\
                .insert(audit_data)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error adding audit entry: {str(e)}")
            return False
    
    def _is_valid_status_transition(
        self,
        current_status: PurchaseRequestStatus,
        new_status: PurchaseRequestStatus
    ) -> bool:
        """Validate status transitions"""
        valid_transitions = {
            PurchaseRequestStatus.DRAFT: [PurchaseRequestStatus.PENDING],
            PurchaseRequestStatus.PENDING: [PurchaseRequestStatus.APPROVED, PurchaseRequestStatus.REJECTED],
            PurchaseRequestStatus.APPROVED: [],  # Final state
            PurchaseRequestStatus.REJECTED: [PurchaseRequestStatus.PENDING]  # Can resubmit
        }
        
        return new_status in valid_transitions.get(current_status, [])
