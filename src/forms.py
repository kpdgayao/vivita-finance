# Form generation logic for purchase requests

import streamlit as st
from datetime import datetime
from config import config
from supabase import create_client

def generate_prf():
    st.subheader("Purchase Request Form")
    
    supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
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
        
        for i in range(int(num_items)):
            st.write(f"Item {i+1}")
            col1, col2, col3 = st.columns(3)
            with col1:
                item = st.text_input("Item Description", key=f"item_{i}")
            with col2:
                quantity = st.number_input("Quantity", min_value=1, value=1, key=f"qty_{i}")
            with col3:
                unit_price = st.number_input("Unit Price", min_value=0.0, value=0.0, key=f"price_{i}")
            
            items.append({
                "description": item,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": quantity * unit_price
            })
        
        if st.form_submit_button("Submit PRF"):
            try:
                # Save PRF
                prf_data = {
                    "prf_number": prf_number,
                    "requester": requester,
                    "department": department,
                    "date_needed": str(date_needed),
                    "purpose": purpose,
                    "items": items,
                    "total_amount": sum(item["total"] for item in items),
                    "status": "Pending",
                    "created_at": datetime.now().isoformat()
                }
                
                supabase.table('purchase_requests').insert(prf_data).execute()
                
                # Update PRF counter
                supabase.table('prf_counter').update({"current_number": prf_number}).execute()
                
                st.success(f"PRF #{prf_number} submitted successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error submitting PRF: {str(e)}")
