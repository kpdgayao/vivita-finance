import streamlit as st
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID
from ...models import PurchaseRequest, PurchaseRequestStatus
from ...crud.purchase_request import PurchaseRequestManager
from .utils import format_currency, can_approve_prf, can_delete_prf

def render_prf_details():
    """Render detailed view of a purchase request"""
    st.title("Purchase Request Details")
    
    if 'user' not in st.session_state:
        st.error("Please log in to access this page")
        return
    
    if 'selected_prf' not in st.session_state:
        st.error("No purchase request selected")
        st.button("Back to PRF List", on_click=lambda: setattr(st.session_state, 'current_page', 'prf_list'))
        return
    
    user = st.session_state.user
    pr_manager = PurchaseRequestManager()
    
    # Get PRF details
    prf = pr_manager.get_purchase_request(st.session_state.selected_prf)
    if not prf:
        st.error("Purchase request not found")
        st.button("Back to PRF List", on_click=lambda: setattr(st.session_state, 'current_page', 'prf_list'))
        return
    
    # Display PRF header
    st.markdown(f"### PRF #{prf.form_number}")
    st.markdown(f"**Status:** {prf.status.value.upper()}")
    
    # Basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Basic Information**")
        st.write(f"Date: {prf.created_at.strftime('%Y-%m-%d')}")
        st.write(f"Requestor: {pr_manager.get_requestor_name(prf.requestor_id)}")
        st.write(f"Supplier: {pr_manager.get_supplier_name(prf.supplier_id)}")
    
    with col2:
        st.write("**Amount Information**")
        st.write(f"Total Amount: {format_currency(prf.total_amount)}")
        if prf.remarks:
            st.write("**Remarks**")
            st.write(prf.remarks)
    
    # Items table
    st.markdown("### Items")
    if prf.items:
        items_data = []
        for item in prf.items:
            items_data.append({
                "Description": item.item_description,
                "Quantity": f"{float(item.quantity):,.2f}",
                "Unit": item.unit,
                "Unit Price": format_currency(item.unit_price),
                "Total": format_currency(item.total_price)
            })
        st.table(items_data)
    else:
        st.info("No items found")
    
    # Action buttons
    st.markdown("### Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Back to List"):
            st.session_state.current_page = 'prf_list'
            st.rerun()
    
    with col2:
        # Status-specific actions
        if prf.status == PurchaseRequestStatus.DRAFT:
            if can_delete_prf(user, prf):
                if st.button("Delete Draft"):
                    if pr_manager.delete_purchase_request(prf.id):
                        st.success("Draft deleted successfully")
                        st.session_state.current_page = 'prf_list'
                        st.rerun()
                    else:
                        st.error("Failed to delete draft")
            
            if user['id'] == prf.requestor_id:
                if st.button("Submit for Approval"):
                    if pr_manager.update_purchase_request_status(
                        prf.id,
                        PurchaseRequestStatus.PENDING
                    ):
                        st.success("PRF submitted for approval")
                        st.rerun()
                    else:
                        st.error("Failed to submit PRF")
        
        elif prf.status == PurchaseRequestStatus.PENDING:
            if can_approve_prf(user):
                if st.button("Approve"):
                    if pr_manager.update_purchase_request_status(
                        prf.id,
                        PurchaseRequestStatus.APPROVED
                    ):
                        st.success("PRF approved successfully")
                        st.rerun()
                    else:
                        st.error("Failed to approve PRF")
                
                if st.button("Reject"):
                    reason = st.text_area("Rejection Reason")
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
    
    with col3:
        if st.button("Print PRF"):
            # TODO: Implement PRF printing functionality
            st.info("Printing functionality coming soon")
    
    # Audit trail
    st.markdown("### History")
    audit_trail = pr_manager.get_audit_trail(prf.id)
    if audit_trail:
        for entry in audit_trail:
            st.write(
                f"{entry.timestamp.strftime('%Y-%m-%d %H:%M')} - "
                f"{entry.action} by {entry.user_name}"
            )
            if entry.details:
                st.write(f"Details: {entry.details}")
    else:
        st.info("No history available")
