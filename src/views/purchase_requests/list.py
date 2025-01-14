import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal
from src.models.purchase_request import PurchaseRequest, PurchaseRequestStatus
from src.crud.purchase_request import PurchaseRequestManager
from src.views.purchase_requests.utils import format_currency, can_approve_prf, can_delete_prf

def render_prf_list():
    """Render the PRF management interface"""
    st.title("Purchase Request Management")
    
    if 'user' not in st.session_state:
        st.error("Please log in to access this page")
        return
        
    user = st.session_state.user
    pr_manager = PurchaseRequestManager()
    
    # Initialize session state for pagination
    if 'prf_page' not in st.session_state:
        st.session_state.prf_page = 1
    if 'items_per_page' not in st.session_state:
        st.session_state.items_per_page = 10
    
    # Filters section
    with st.expander("Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Status filter
            status_filter = st.multiselect(
                "Status",
                options=[status.value for status in PurchaseRequestStatus],
                default=[]
            )
        
        with col2:
            # Date range filter
            date_options = {
                "Today": (datetime.now().date(), datetime.now().date()),
                "Last 7 Days": (
                    (datetime.now() - timedelta(days=7)).date(),
                    datetime.now().date()
                ),
                "Last 30 Days": (
                    (datetime.now() - timedelta(days=30)).date(),
                    datetime.now().date()
                ),
                "Custom Range": None
            }
            
            date_filter = st.selectbox(
                "Date Range",
                options=list(date_options.keys()),
                index=2
            )
            
            if date_filter == "Custom Range":
                date_range = st.date_input(
                    "Select Date Range",
                    value=(
                        (datetime.now() - timedelta(days=30)).date(),
                        datetime.now().date()
                    ),
                    key="custom_date_range"
                )
            else:
                date_range = date_options[date_filter]
        
        with col3:
            # Search filter
            search_query = st.text_input(
                "Search PRF Number or Supplier",
                key="search_query"
            )
            
            # Option to show only my requests
            show_mine = st.checkbox("Show only my requests")
    
    # Apply filters
    filters = {
        "status": status_filter if status_filter else None,
        "start_date": date_range[0] if date_range else None,
        "end_date": date_range[1] if date_range else None,
        "search": search_query if search_query else None,
        "requestor_id": user['id'] if show_mine else None
    }
    
    # Clean up filters by removing None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # Get filtered PRFs with pagination
    prfs, total_count = pr_manager.get_purchase_requests(
        filters=filters if filters else None,
        page=st.session_state.prf_page,
        page_size=st.session_state.items_per_page
    )
    
    # Calculate total pages
    total_pages = (total_count + st.session_state.items_per_page - 1) // st.session_state.items_per_page
    
    # Display PRFs in tabs
    if total_count > 0:
        st.write(f"Showing {len(prfs)} of {total_count} purchase requests")
        
        # Status tabs
        tab_names = ["All", "Draft", "Pending", "Approved", "Rejected"]
        tabs = st.tabs(tab_names)
        
        for tab, status_name in zip(tabs, tab_names):
            with tab:
                status_filter = None if status_name == "All" else PurchaseRequestStatus(status_name.lower())
                
                filtered_prfs = [
                    prf for prf in prfs
                    if not status_filter or prf.status == status_filter
                ]
                
                if not filtered_prfs:
                    st.info(f"No {status_name.lower()} purchase requests found")
                    continue
                
                # Display PRFs in a table
                prf_data = []
                for prf in filtered_prfs:
                    prf_data.append({
                        "PRF #": prf.form_number,
                        "Date": prf.created_at.strftime("%Y-%m-%d"),
                        "Requestor": pr_manager.get_requestor_name(prf.requestor_id),
                        "Supplier": pr_manager.get_supplier_name(prf.supplier_id),
                        "Amount": format_currency(prf.total_amount),
                        "Status": prf.status.value.upper()
                    })
                
                st.table(prf_data)
                
                # Handle PRF actions
                for prf in filtered_prfs:
                    with st.expander(f"Actions for PRF #{prf.form_number}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # View details button
                            if st.button("View Details", key=f"view_{prf.id}"):
                                st.session_state.selected_prf = prf.id
                                st.session_state.current_page = 'prf_details'
                                st.rerun()
                            
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
                        
                        with col2:
                            # Status-specific actions
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
                            
                            elif prf.status == PurchaseRequestStatus.PENDING:
                                if can_approve_prf(user):
                                    if st.button("Approve", key=f"approve_{prf.id}"):
                                        if pr_manager.update_purchase_request_status(
                                            prf.id,
                                            PurchaseRequestStatus.APPROVED
                                        ):
                                            st.success("PRF approved successfully")
                                            st.rerun()
                                        else:
                                            st.error("Failed to approve PRF")
                                    
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
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.session_state.prf_page > 1:
                if st.button("Previous"):
                    st.session_state.prf_page -= 1
                    st.rerun()
        
        with col2:
            st.write(f"Page {st.session_state.prf_page} of {total_pages}")
        
        with col3:
            if st.session_state.prf_page < total_pages:
                if st.button("Next"):
                    st.session_state.prf_page += 1
                    st.rerun()
    else:
        st.info("No purchase requests found matching your criteria")
