import streamlit as st
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from src.models import PurchaseRequest, PurchaseRequestStatus, User
from src.crud.purchase_request import PurchaseRequestManager
from decimal import Decimal

def can_approve_prf(user: User) -> bool:
    """Check if user has permission to approve PRFs"""
    return user['role'].lower() in ['finance', 'admin']

def can_delete_prf(user: User, prf: PurchaseRequest) -> bool:
    """Check if user can delete a PRF"""
    # Only draft PRFs can be deleted
    if prf.status != PurchaseRequestStatus.DRAFT:
        return False
    # Users can only delete their own drafts
    # Admins and Finance can delete any draft
    return (user['id'] == prf.requestor_id) or user['role'].lower() in ['finance', 'admin']

def format_currency(amount: Decimal) -> str:
    """Format decimal amount as currency string"""
    return f"₱{float(amount):,.2f}" if amount else "₱0.00"

def render_prf_management():
    """Render the PRF management interface"""
    st.title("Purchase Request Management")
    
    if 'user' not in st.session_state:
        st.error("Please log in to access this page")
        return
        
    user = st.session_state.user
    pr_manager = PurchaseRequestManager()
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            options=[status.value for status in PurchaseRequestStatus],
            default=[]
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now().date(), datetime.now().date()),
            key="date_range"
        )
    
    with col3:
        search_query = st.text_input("Search PRF Number or Supplier", key="search_query")
    
    # Apply filters
    filters = {
        "status": status_filter if status_filter else None,
        "start_date": date_range[0] if len(date_range) > 0 else None,
        "end_date": date_range[1] if len(date_range) > 1 else None,
        "search": search_query if search_query else None
    }
    
    # Get filtered PRFs with pagination
    page = st.session_state.get('prf_page', 1)
    page_size = st.session_state.get('items_per_page', 10)
    
    prfs, total_count = pr_manager.get_purchase_requests(
        filters=filters if filters else None,
        page=page,
        page_size=page_size
    )
    
    if not prfs:
        st.info("No purchase requests found matching the filters")
        return
        
    # Display PRFs in tabs based on status
    tabs = st.tabs(["All", "Draft", "Pending", "Approved", "Rejected"])
    
    for tab, status_group in zip(
        tabs,
        [None, PurchaseRequestStatus.DRAFT, PurchaseRequestStatus.PENDING,
         PurchaseRequestStatus.APPROVED, PurchaseRequestStatus.REJECTED]
    ):
        with tab:
            filtered_prfs = [
                prf for prf in prfs
                if not status_group or prf.status == status_group
            ]
            
            if not filtered_prfs:
                st.info(f"No {'purchase requests' if not status_group else status_group.value + ' requests'} found")
                continue
                
            for prf in filtered_prfs:
                with st.expander(f"PRF #{prf.form_number} - {prf.status.value.upper()}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Basic Information**")
                        st.write(f"Date: {prf.created_at.strftime('%Y-%m-%d')}")
                        st.write(f"Requestor: {pr_manager.get_requestor_name(prf.requestor_id)}")
                        st.write(f"Supplier: {pr_manager.get_supplier_name(prf.supplier_id)}")
                        st.write(f"Total Amount: {format_currency(prf.total_amount)}")
                        
                        if prf.remarks:
                            st.write("**Remarks**")
                            st.write(prf.remarks)
                    
                    with col2:
                        st.write("**Actions**")
                        
                        # View Details Button
                        if st.button("View Details", key=f"view_{prf.id}"):
                            st.session_state.selected_prf = prf.id
                            st.session_state.current_page = 'prf_details'
                            st.rerun()
                        
                        # Draft Actions
                        if prf.status == PurchaseRequestStatus.DRAFT:
                            if can_delete_prf(user, prf):
                                if st.button("Delete Draft", key=f"delete_{prf.id}"):
                                    if pr_manager.delete_purchase_request(prf.id):
                                        st.success("Draft deleted successfully")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete draft")
                            
                            if user['id'] == prf.requestor_id:
                                if st.button("Submit for Approval", key=f"submit_{prf.id}"):
                                    if pr_manager.update_purchase_request_status(
                                        prf.id,
                                        PurchaseRequestStatus.PENDING
                                    ):
                                        st.success("PRF submitted for approval")
                                        st.rerun()
                                    else:
                                        st.error("Failed to submit PRF")
                        
                        # Pending Actions
                        elif prf.status == PurchaseRequestStatus.PENDING:
                            if can_approve_prf(user):
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Approve", key=f"approve_{prf.id}"):
                                        if pr_manager.update_purchase_request_status(
                                            prf.id,
                                            PurchaseRequestStatus.APPROVED
                                        ):
                                            st.success("PRF approved successfully")
                                            st.rerun()
                                        else:
                                            st.error("Failed to approve PRF")
                                
                                with col2:
                                    if st.button("Reject", key=f"reject_{prf.id}"):
                                        reason = st.text_area(
                                            "Rejection Reason",
                                            key=f"reason_{prf.id}"
                                        )
                                        if reason:
                                            if pr_manager.update_purchase_request_status(
                                                prf.id,
                                                PurchaseRequestStatus.REJECTED,
                                                remarks=f"Rejected: {reason}"
                                            ):
                                                st.success("PRF rejected")
                                                st.rerun()
                                            else:
                                                st.error("Failed to reject PRF")
                        
                        # Show audit trail
                        if st.button("View History", key=f"history_{prf.id}"):
                            audit_trail = pr_manager.get_audit_trail(prf.id)
                            if audit_trail:
                                st.write("**Audit Trail**")
                                for entry in audit_trail:
                                    st.write(
                                        f"{entry.timestamp.strftime('%Y-%m-%d %H:%M')} - "
                                        f"{entry.action} by {entry.user_name}"
                                    )
                            else:
                                st.info("No history available")
