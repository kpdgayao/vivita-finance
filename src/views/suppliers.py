import streamlit as st
from src.crud import SupplierManager
from src.models import Supplier
from uuid import UUID

def render():
    st.title("Supplier Management")
    
    supplier_manager = SupplierManager()
    
    # Initialize session state
    if 'editing_supplier_id' not in st.session_state:
        st.session_state.editing_supplier_id = None
    if 'show_add_form' not in st.session_state:
        st.session_state.show_add_form = False
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'deleting_supplier_id' not in st.session_state:
        st.session_state.deleting_supplier_id = None
    
    # Top bar with search and add button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.search_query = st.text_input("🔍 Search suppliers", value=st.session_state.search_query)
    with col2:
        if not st.session_state.editing_supplier_id and not st.session_state.show_add_form:
            if st.button("➕ Add Supplier", type="primary"):
                st.session_state.show_add_form = True
                st.rerun()
    
    # Add new supplier form
    if st.session_state.show_add_form and not st.session_state.editing_supplier_id:
        st.divider()
        with st.container():
            st.subheader("Add New Supplier")
            with st.form("add_supplier", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Name*")
                    email = st.text_input("Email")
                    phone = st.text_input("Phone")
                with col2:
                    contact_person = st.text_input("Contact Person")
                    tax_id = st.text_input("Tax ID")
                    payment_method = st.selectbox(
                        "Payment Method",
                        ["Bank Transfer", "Check", "Cash", "Other"]
                    )
                
                address = st.text_area("Address", height=100)
                
                if payment_method == "Bank Transfer":
                    st.write("Bank Details:")
                    col1, col2 = st.columns(2)
                    with col1:
                        bank_name = st.text_input("Bank Name")
                        account_name = st.text_input("Account Name")
                    with col2:
                        account_number = st.text_input("Account Number")
                    bank_details = {
                        "bank_name": bank_name,
                        "account_name": account_name,
                        "account_number": account_number
                    }
                else:
                    bank_details = None
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    submitted = st.form_submit_button("Save", type="primary", use_container_width=True)
                with col2:
                    cancelled = st.form_submit_button("Cancel", use_container_width=True)
                
                if submitted:
                    if not name:
                        st.error("Supplier name is required")
                    else:
                        supplier = Supplier(
                            name=name,
                            contact_person=contact_person,
                            phone=phone,
                            email=email,
                            address=address,
                            tax_id=tax_id,
                            preferred_payment_method=payment_method,
                            bank_details=bank_details
                        )
                        
                        if supplier_manager.create_supplier(supplier):
                            st.success("Supplier added successfully!")
                            st.session_state.show_add_form = False
                            st.rerun()
                
                if cancelled:
                    st.session_state.show_add_form = False
                    st.rerun()
    
    # Edit supplier form
    elif st.session_state.editing_supplier_id:
        current_supplier = supplier_manager.get_supplier(UUID(st.session_state.editing_supplier_id))
        if current_supplier:
            st.divider()
            with st.container():
                st.subheader(f"Edit Supplier: {current_supplier.name}")
                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Name*", value=current_supplier.name)
                        email = st.text_input("Email", value=current_supplier.email or "")
                        phone = st.text_input("Phone", value=current_supplier.phone or "")
                    with col2:
                        contact_person = st.text_input("Contact Person", value=current_supplier.contact_person or "")
                        tax_id = st.text_input("Tax ID", value=current_supplier.tax_id or "")
                        current_payment_method = current_supplier.preferred_payment_method or "Bank Transfer"
                        payment_method = st.selectbox(
                            "Payment Method",
                            ["Bank Transfer", "Check", "Cash", "Other"],
                            index=["Bank Transfer", "Check", "Cash", "Other"].index(current_payment_method)
                        )
                    
                    address = st.text_area("Address", value=current_supplier.address or "", height=100)
                    
                    current_bank_details = current_supplier.bank_details or {}
                    if payment_method == "Bank Transfer":
                        st.write("Bank Details:")
                        col1, col2 = st.columns(2)
                        with col1:
                            bank_name = st.text_input("Bank Name", value=current_bank_details.get('bank_name', ''))
                            account_name = st.text_input("Account Name", value=current_bank_details.get('account_name', ''))
                        with col2:
                            account_number = st.text_input("Account Number", value=current_bank_details.get('account_number', ''))
                        bank_details = {
                            "bank_name": bank_name,
                            "account_name": account_name,
                            "account_number": account_number
                        }
                    else:
                        bank_details = None
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        submitted = st.form_submit_button("Save", type="primary", use_container_width=True)
                    with col2:
                        cancelled = st.form_submit_button("Cancel", use_container_width=True)
                    
                    if submitted:
                        if not name:
                            st.error("Supplier name is required")
                        else:
                            supplier = Supplier(
                                id=current_supplier.id,
                                name=name,
                                contact_person=contact_person,
                                phone=phone,
                                email=email,
                                address=address,
                                tax_id=tax_id,
                                preferred_payment_method=payment_method,
                                bank_details=bank_details
                            )
                            
                            if supplier_manager.update_supplier(supplier):
                                st.success("Supplier updated successfully!")
                                st.session_state.editing_supplier_id = None
                                st.rerun()
                    
                    if cancelled:
                        st.session_state.editing_supplier_id = None
                        st.rerun()
    
    # Display existing suppliers
    st.divider()
    suppliers = supplier_manager.get_suppliers()
    
    # Filter suppliers based on search query
    if st.session_state.search_query:
        query = st.session_state.search_query.lower()
        suppliers = [
            s for s in suppliers 
            if query in s['name'].lower() 
            or query in (s['contact_person'] or '').lower()
            or query in (s['email'] or '').lower()
            or query in (s['phone'] or '').lower()
        ]
    
    if not suppliers:
        st.info("No suppliers found. Add your first supplier using the button above.")
    else:
        # Display suppliers in a grid
        for supplier in suppliers:
            with st.container(border=True):
                # Header row
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.subheader(supplier['name'])
                with header_col2:
                    if st.session_state.deleting_supplier_id == supplier['id']:
                        if st.button("⚠️ Confirm", key=f"confirm_delete_{supplier['id']}", type="primary"):
                            if supplier_manager.delete_supplier(UUID(supplier['id'])):
                                st.success("Supplier deleted successfully!")
                                st.session_state.deleting_supplier_id = None
                                st.rerun()
                        if st.button("Cancel", key=f"cancel_delete_{supplier['id']}"):
                            st.session_state.deleting_supplier_id = None
                            st.rerun()
                    else:
                        if st.button("🗑️", key=f"delete_{supplier['id']}", help="Delete supplier"):
                            st.session_state.deleting_supplier_id = supplier['id']
                            st.rerun()
                
                # Contact info row
                info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                with info_col1:
                    if supplier['contact_person']:
                        st.write(f"👤 {supplier['contact_person']}")
                with info_col2:
                    if supplier['phone']:
                        st.write(f"📞 {supplier['phone']}")
                with info_col3:
                    if supplier['email']:
                        st.write(f"📧 {supplier['email']}")
                with info_col4:
                    if st.button("✏️", key=f"edit_{supplier['id']}", help="Edit supplier"):
                        st.session_state.editing_supplier_id = supplier['id']
                        st.rerun()
                
                # Additional details in expander
                with st.expander("More Details"):
                    if supplier['address']:
                        st.write("📍 Address:")
                        st.write(supplier['address'])
                    if supplier['tax_id']:
                        st.write(f"🏢 Tax ID: {supplier['tax_id']}")
                    st.write(f"💳 Payment: {supplier['preferred_payment_method']}")
                    if supplier['bank_details']:
                        st.write("🏦 Bank Details:")
                        st.write(f"Bank: {supplier['bank_details'].get('bank_name', '')}")
                        st.write(f"Account: {supplier['bank_details'].get('account_name', '')}")
                        st.write(f"Number: {supplier['bank_details'].get('account_number', '')}")
