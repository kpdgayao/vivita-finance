import streamlit as st
from src.crud import PurchaseRequestManager

def render():
    st.title("Dashboard")
    
    pr_manager = PurchaseRequestManager()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pending_prs = pr_manager.get_purchase_requests(status='pending')
        st.metric("Pending PRFs", len(pending_prs))
        
    with col2:
        approved_prs = pr_manager.get_purchase_requests(status='approved')
        st.metric("Approved PRFs", len(approved_prs))
        
    with col3:
        rejected_prs = pr_manager.get_purchase_requests(status='rejected')
        st.metric("Rejected PRFs", len(rejected_prs))
    
    # Display recent PRFs
    st.subheader("Recent Purchase Requests")
    all_prs = pr_manager.get_purchase_requests()
    
    if all_prs:
        for pr in all_prs:
            with st.expander(f"PROF #{pr.form_number} - {pr.status.title()}"):
                st.write(f"Total Amount: ₱{pr.total_amount:,.2f}")
                st.write(f"Status: {pr.status.title()}")
                st.write(f"Remarks: {pr.remarks}")
                
                if pr.items:
                    st.write("Items:")
                    for item in pr.items:
                        st.write(f"- {item.item_description}: {item.quantity} {item.unit} @ ₱{item.unit_price:,.2f}")
    else:
        st.info("No purchase requests found.")
