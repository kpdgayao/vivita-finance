import streamlit as st
from ..crud import PurchaseRequestManager
from ..models.purchase_request import PurchaseRequestStatus

def render():
    st.title("Dashboard")
    
    pr_manager = PurchaseRequestManager()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pending_filter = {"status": [PurchaseRequestStatus.PENDING.value]}
        pending_prs, pending_count = pr_manager.get_purchase_requests(filters=pending_filter)
        st.metric("Pending PRFs", pending_count)
        
    with col2:
        approved_filter = {"status": [PurchaseRequestStatus.APPROVED.value]}
        approved_prs, approved_count = pr_manager.get_purchase_requests(filters=approved_filter)
        st.metric("Approved PRFs", approved_count)
        
    with col3:
        rejected_filter = {"status": [PurchaseRequestStatus.REJECTED.value]}
        rejected_prs, rejected_count = pr_manager.get_purchase_requests(filters=rejected_filter)
        st.metric("Rejected PRFs", rejected_count)
    
    # Display recent PRFs
    st.subheader("Recent Purchase Requests")
    
    # Get last 5 PRFs, sorted by created_at
    recent_prs, _ = pr_manager.get_purchase_requests(page=1, page_size=5)
    
    if recent_prs:
        for pr in recent_prs:
            with st.expander(f"PRF #{pr.form_number} - {pr.status.value.title()}"):
                st.write(f"Date: {pr.created_at.strftime('%Y-%m-%d')}")
                st.write(f"Total Amount: ₱{pr.total_amount:,.2f}" if pr.total_amount else "Total Amount: ₱0.00")
                
                if pr.items:
                    st.write("Items:")
                    for item in pr.items:
                        st.write(f"- {item.item_description}: {item.quantity} {item.unit} @ ₱{item.unit_price:,.2f}")
    else:
        st.info("No purchase requests found.")
