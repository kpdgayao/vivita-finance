import streamlit as st
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from ...models import PurchaseRequest, PurchaseRequestStatus, PurchaseRequestItem
from ...crud.purchase_request import PurchaseRequestManager
from .utils import format_currency

def fetch_suppliers() -> List[Dict]:
    """Fetch suppliers from database with caching"""
    if 'supplier_cache' not in st.session_state or \
       'last_supplier_fetch' not in st.session_state or \
       (datetime.now() - st.session_state.last_supplier_fetch).total_seconds() > 300:  # Cache for 5 minutes
        
        supabase = st.session_state.supabase
        result = supabase.table('suppliers')\
            .select('id, name')\
            .order('name')\
            .execute()
        
        if result.data:
            st.session_state.supplier_cache = result.data
            st.session_state.last_supplier_fetch = datetime.now()
        else:
            st.session_state.supplier_cache = []
    
    return st.session_state.supplier_cache

def generate_prf():
    """Generate purchase request form"""
    st.title("Create Purchase Request")
    
    if 'user' not in st.session_state:
        st.error("Please log in to access this page")
        return
    
    user = st.session_state.user
    pr_manager = PurchaseRequestManager()
    
    # Initialize session state for items
    if 'prf_items' not in st.session_state:
        st.session_state.prf_items = []
    
    # Form header
    st.markdown("### Basic Information")
    
    # Get suppliers list for dropdown
    suppliers = fetch_suppliers()
    if not suppliers:
        st.error("No suppliers found. Please add suppliers first.")
        return
    
    supplier_options = {s['id']: s['name'] for s in suppliers}
    
    col1, col2 = st.columns(2)
    
    with col1:
        supplier_id = st.selectbox(
            "Supplier",
            options=list(supplier_options.keys()),
            format_func=lambda x: supplier_options[x]
        )
    
    # Items section
    st.markdown("### Items")
    
    # Add new item form
    with st.expander("Add Item", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            item_description = st.text_area("Description")
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
            unit = st.text_input("Unit")
        
        with col2:
            unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01)
            total_price = quantity * unit_price
            st.write(f"Total Price: {format_currency(Decimal(str(total_price)))}")
        
        if st.button("Add Item"):
            if not all([item_description, quantity > 0, unit, unit_price > 0]):
                st.error("Please fill in all item details")
            else:
                st.session_state.prf_items.append({
                    "item_description": item_description,
                    "quantity": quantity,
                    "unit": unit,
                    "unit_price": unit_price,
                    "total_price": total_price
                })
                st.success("Item added")
                st.rerun()
    
    # Display items table
    if st.session_state.prf_items:
        items_data = []
        total_amount = Decimal('0')
        
        for i, item in enumerate(st.session_state.prf_items):
            items_data.append({
                "Description": item["item_description"],
                "Quantity": f"{float(item['quantity']):,.2f}",
                "Unit": item["unit"],
                "Unit Price": format_currency(Decimal(str(item["unit_price"]))),
                "Total": format_currency(Decimal(str(item["total_price"])))
            })
            total_amount += Decimal(str(item["total_price"]))
        
        st.table(items_data)
        st.markdown(f"**Total Amount: {format_currency(total_amount)}**")
        
        if st.button("Clear Items"):
            st.session_state.prf_items = []
            st.rerun()
    else:
        st.info("No items added yet")
    
    # Remarks
    remarks = st.text_area("Remarks", help="Optional notes or comments")
    
    # Submit buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save as Draft"):
            if not st.session_state.prf_items:
                st.error("Please add at least one item")
                return
            
            if save_prf(user['id'], supplier_id, remarks, st.session_state.prf_items, PurchaseRequestStatus.DRAFT):
                st.success("Draft saved successfully")
                clear_form()
                st.rerun()
    
    with col2:
        if st.button("Submit for Approval"):
            if not st.session_state.prf_items:
                st.error("Please add at least one item")
                return
            
            if save_prf(user['id'], supplier_id, remarks, st.session_state.prf_items, PurchaseRequestStatus.PENDING):
                st.success("PRF submitted for approval")
                clear_form()
                st.rerun()

def save_prf(requestor_id: UUID, supplier_id: UUID, remarks: Optional[str], items: List[Dict], status: PurchaseRequestStatus) -> bool:
    """Save PRF with items"""
    pr_manager = PurchaseRequestManager()
    
    # Calculate total amount
    total_amount = sum(Decimal(str(item["total_price"])) for item in items)
    
    # Create initial PRF
    prf = PurchaseRequest(
        requestor_id=requestor_id,
        supplier_id=supplier_id,
        remarks=remarks,
        total_amount=total_amount,
        status=status,
        created_at=datetime.now()
    )
    
    # Generate form number
    form_number = pr_manager.generate_form_number()
    if not form_number:
        st.error("Failed to generate form number")
        return False
    
    # Set form number
    prf.form_number = form_number
    
    # Create the PRF
    created_prf = pr_manager.create_purchase_request(prf)
    if not created_prf:
        return False
    
    # Now create PurchaseRequestItem objects with the PRF ID
    prf_items = []
    for item in items:
        prf_items.append(PurchaseRequestItem(
            purchase_request_id=created_prf.id,
            item_description=item["item_description"],
            quantity=Decimal(str(item["quantity"])),
            unit=item["unit"],
            unit_price=Decimal(str(item["unit_price"])),
            total_price=Decimal(str(item["total_price"]))
        ))
    
    # Update the PRF with items
    created_prf.items = prf_items
    return pr_manager.create_purchase_request(created_prf) is not None

def clear_form():
    """Clear form data from session state"""
    if 'prf_items' in st.session_state:
        del st.session_state.prf_items
