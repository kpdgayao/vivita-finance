import streamlit as st
from src.crud import PurchaseRequestManager
from src.models.purchase_request import PurchaseRequestStatus

def render():
    st.title("Dashboard")
    
    pr_manager = PurchaseRequestManager()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pending_prs = pr_manager.get_purchase_requests(PurchaseRequestStatus.PENDING)
        st.metric("Pending PRFs", len(pending_prs))
        
    with col2:
        approved_prs = pr_manager.get_purchase_requests(PurchaseRequestStatus.APPROVED)
        st.metric("Approved PRFs", len(approved_prs))
        
    with col3:
        rejected_prs = pr_manager.get_purchase_requests(PurchaseRequestStatus.REJECTED)
        st.metric("Rejected PRFs", len(rejected_prs))
    
    # Display recent PRFs
    st.subheader("Recent Purchase Requests")
    
    recent_prs = pr_manager.get_purchase_requests()[:5]  # Get last 5 PRFs
    
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
