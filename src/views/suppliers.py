import streamlit as st
from src.crud import SupplierManager
from src.models import Supplier

def render():
    st.title("Supplier Management")
    
    supplier_manager = SupplierManager()
    
    # Add new supplier form
    with st.form("add_supplier"):
        st.subheader("Add New Supplier")
        name = st.text_input("Name")
        contact_person = st.text_input("Contact Person")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        tax_id = st.text_input("Tax ID")
        
        # Payment Information
        payment_method = st.selectbox(
            "Preferred Payment Method",
            ["Bank Transfer", "Check", "Cash", "Other"]
        )
        
        if payment_method == "Bank Transfer":
            bank_name = st.text_input("Bank Name")
            account_name = st.text_input("Account Name")
            account_number = st.text_input("Account Number")
            bank_details = {
                "bank_name": bank_name,
                "account_name": account_name,
                "account_number": account_number
            }
        else:
            bank_details = None
        
        submitted = st.form_submit_button("Add Supplier")
        if submitted:
            if not name:
                st.error("Supplier name is required")
            else:
                supplier = Supplier(
                    name=name,
                    contact_person=contact_person,
                    email=email,
                    phone=phone,
                    address=address,
                    tax_id=tax_id,
                    preferred_payment_method=payment_method,
                    bank_details=bank_details
                )
                
                if supplier_manager.create_supplier(supplier):
                    st.success("Supplier added successfully!")
                    st.rerun()  # Refresh the page to show the new supplier
    
    # Display existing suppliers
    st.subheader("Existing Suppliers")
    suppliers = supplier_manager.get_suppliers()
    
    if suppliers:
        for supplier in suppliers:
            with st.expander(supplier['name']):
                st.write(f"Contact Person: {supplier['contact_person']}")
                st.write(f"Email: {supplier['email']}")
                st.write(f"Phone: {supplier['phone']}")
                st.write(f"Address: {supplier['address']}")
                st.write(f"Tax ID: {supplier['tax_id']}")
                st.write(f"Payment Method: {supplier['preferred_payment_method']}")
                
                if supplier['bank_details']:
                    st.write("Bank Details:")
                    for key, value in supplier['bank_details'].items():
                        st.write(f"  {key.replace('_', ' ').title()}: {value}")
    else:
        st.info("No suppliers found. Add your first supplier using the form above.")
