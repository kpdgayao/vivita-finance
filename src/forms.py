# Form generation logic for purchase requests

import streamlit as st
from datetime import datetime
from decimal import Decimal
from src.config import config
from src.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus
)
from src.crud import PurchaseRequestManager
from supabase import create_client

def generate_prf():
    st.subheader("Purchase Request Form")
    
    # Ensure we have a valid session
    if not st.session_state.get('session') or not st.session_state.get('user'):
        st.error("Your session has expired. Please log in again.")
        st.session_state.current_page = 'login'
        st.rerun()
        return
    
    supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    # Set the session token
    supabase.auth.set_session(
        st.session_state.session['access_token'],
        st.session_state.session['refresh_token']
    )
    
    # Get the next PRF number
    try:
        response = supabase.table('prf_counter').select("current_number").single().execute()
        if response.data:
            prf_number = response.data['current_number'] + 1
        else:
            # Initialize counter if it doesn't exist
            prf_number = 1
            supabase.table('prf_counter').insert({"current_number": 0}).execute()
    except Exception as e:
        st.error(f"Error generating PRF number: {str(e)}")
        return
    
    with st.form("prf_form"):
        st.write(f"PRF Number: {prf_number}")
        
        # Form fields
        requester = st.text_input("Requester Name")
        department = st.selectbox("Department", ["Operations", "Finance", "IT", "HR"])
        date_needed = st.date_input("Date Needed")
        purpose = st.text_area("Purpose")
        
        # Items section
        st.write("Items")
        num_items = st.number_input("Number of items", min_value=1, value=1)
        items = []
        total_amount = Decimal('0.00')
        
        for i in range(int(num_items)):
            st.write(f"Item {i+1}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                item = st.text_input("Item Description", key=f"item_{i}")
            with col2:
                quantity = st.number_input("Quantity", min_value=0.01, value=1.00, step=0.01, key=f"qty_{i}")
            with col3:
                unit = st.text_input("Unit", key=f"unit_{i}")
            with col4:
                unit_price = st.number_input("Unit Price", min_value=0.00, value=0.00, step=0.01, key=f"price_{i}")
            
            # Create PurchaseRequestItem instance for validation
            item_obj = PurchaseRequestItem(
                item_description=item,
                quantity=Decimal(str(quantity)),
                unit=unit,
                unit_price=Decimal(str(unit_price)),
                total_price=Decimal(str(quantity * unit_price)),
                purchase_request_id=None  # Will be set after PR creation
            )
            
            items.append(item_obj)
            total_amount += item_obj.total_price
            
            # Display item total
            st.write(f"Item Total: ₱{item_obj.total_price:,.2f}")
        
        # Display grand total
        st.write(f"Grand Total: ₱{total_amount:,.2f}")
        
        submit_button = st.form_submit_button("Review PRF")
        
        if submit_button:
            # Show review section
            st.subheader("Review Purchase Request")
            st.write("Please review the following details before final submission:")
            
            st.write(f"PRF Number: PRF-{prf_number:04d}")
            st.write(f"Requester: {requester}")
            st.write(f"Department: {department}")
            st.write(f"Date Needed: {date_needed}")
            st.write(f"Purpose: {purpose}")
            st.write(f"Total Amount: ₱{total_amount:,.2f}")
            
            st.write("Items:")
            for idx, item in enumerate(items, 1):
                st.write(f"{idx}. {item.item_description}")
                st.write(f"   Quantity: {item.quantity} {item.unit}")
                st.write(f"   Unit Price: ₱{item.unit_price:,.2f}")
                st.write(f"   Total: ₱{item.total_price:,.2f}")
            
            if st.button("Confirm and Submit"):
                try:
                    # Create PurchaseRequest instance
                    pr = PurchaseRequest(
                        form_number=f"PRF-{prf_number:04d}",
                        requestor_id=st.session_state.user['id'],
                        supplier_id=None,  # TODO: Add supplier selection
                        status=PurchaseRequestStatus.DRAFT,
                        remarks=purpose,
                        total_amount=total_amount,
                        items=items
                    )
                    
                    # Save PRF using PurchaseRequestManager
                    pr_manager = PurchaseRequestManager()
                    result = pr_manager.create_purchase_request(pr)
                    
                    if result:
                        # Update the PRF counter
                        supabase.table('prf_counter').update({"current_number": prf_number}).execute()
                        st.success(f"PRF #{prf_number} submitted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to submit PRF. Please try again.")
                    
                except Exception as e:
                    st.error(f"Error submitting PRF: {str(e)}")
