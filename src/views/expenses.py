import streamlit as st
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from src.crud import ExpenseManager
from src.models.expense import (
    ExpenseReimbursementForm,
    ExpenseItem,
    ExpenseFormStatus,
    Voucher,
    VoucherEntry
)

def calculate_item_total(amount: Decimal) -> Decimal:
    """Calculate total for an item"""
    return Decimal(str(amount)).quantize(Decimal('0.01'))

def render_erf_form():
    st.title("Expense Reimbursement Form")
    
    expense_manager = ExpenseManager()
    
    # Initialize session state for expense items
    if 'expense_items' not in st.session_state:
        st.session_state.expense_items = []
    
    # Form inputs
    with st.form("erf_form"):
        # Header information
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.now())
        with col2:
            designation = st.text_input("Designation", value=st.session_state.user.get('role', ''))
        
        # Expense items
        st.subheader("Expense Details")
        
        # Display existing items
        grand_total = Decimal('0')
        for i, item in enumerate(st.session_state.expense_items):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 3, 2, 2, 1])
            with col1:
                item.date = st.date_input(f"Date {i}", item.date)
            with col2:
                item.description = st.text_input(f"Description {i}", item.description)
            with col3:
                item.payee = st.text_input(f"Payee {i}", item.payee)
            with col4:
                item.reference_number = st.text_input(f"Reference # {i}", item.reference_number or '')
            with col5:
                amount = st.number_input(f"Amount {i}", value=float(item.amount), step=0.01, format="%.2f")
                item.amount = Decimal(str(amount))
                # Calculate item total
                item_total = calculate_item_total(item.amount)
                grand_total += item_total
                st.write(f"Total: ₱{item_total:,.2f}")
            with col6:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.expense_items.pop(i)
                    st.rerun()
        
        # Display grand total
        st.markdown(f"### Grand Total: ₱{grand_total:,.2f}")
        
        # Add new item button
        if st.button("Add Item"):
            new_item = ExpenseItem(
                date=datetime.now(),
                description="",
                payee="",
                amount=Decimal('0'),
                account="OPEX",  # Default account
                reference_number=None
            )
            st.session_state.expense_items.append(new_item)
            st.rerun()
        
        # Submit button
        if st.form_submit_button("Submit"):
            try:
                if not st.session_state.expense_items:
                    st.error("Please add at least one expense item")
                    return
                
                # Create ERF
                erf = ExpenseReimbursementForm(
                    employee_id=st.session_state.user['id'],
                    designation=designation,
                    date=date,
                    status=ExpenseFormStatus.PENDING,
                    items=st.session_state.expense_items,
                    total_amount=grand_total  # Set the calculated grand total
                )
                
                # Save ERF
                result = expense_manager.create_expense_form(erf)
                
                if result:
                    st.success(f"ERF #{result.form_number} submitted successfully!")
                    st.session_state.expense_items = []  # Clear items
                    st.rerun()
                else:
                    st.error("Failed to submit ERF. Please try again.")
            
            except Exception as e:
                st.error(f"Error submitting ERF: {str(e)}")

def render_voucher_form():
    st.title("Voucher")
    
    expense_manager = ExpenseManager()
    
    # Initialize session state for voucher entries
    if 'voucher_entries' not in st.session_state:
        st.session_state.voucher_entries = []
    
    # Form inputs
    with st.form("voucher_form"):
        # Header information
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.now())
            payee = st.text_input("Payee")
            particulars = st.text_area("Particulars")
        with col2:
            bank_name = st.text_input("Bank")
            transaction_type = st.selectbox("Transaction Type", ["Fund Transfer", "Check", "Cash"])
            reference_number = st.text_input("Reference Number")
        
        # Voucher entries
        st.subheader("Distribution of Account")
        
        # Display existing entries
        for i, entry in enumerate(st.session_state.voucher_entries):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            with col1:
                entry.account_title = st.text_input(f"Account Title {i}", entry.account_title)
            with col2:
                entry.activity = st.text_input(f"Activity {i}", entry.activity or '')
            with col3:
                debit = st.number_input(f"Debit {i}", value=float(entry.debit_amount) if entry.debit_amount else 0.0, step=0.01)
                entry.debit_amount = Decimal(str(debit)) if debit else None
            with col4:
                credit = st.number_input(f"Credit {i}", value=float(entry.credit_amount) if entry.credit_amount else 0.0, step=0.01)
                entry.credit_amount = Decimal(str(credit)) if credit else None
            with col5:
                if st.button("Remove", key=f"remove_entry_{i}"):
                    st.session_state.voucher_entries.pop(i)
                    st.rerun()
        
        # Add new entry button
        if st.button("Add Entry"):
            st.session_state.voucher_entries.append(
                VoucherEntry(
                    account_title="",
                    activity="",
                    debit_amount=None,
                    credit_amount=None
                )
            )
            st.rerun()
        
        # Calculate totals
        total_debit = sum(entry.debit_amount or Decimal('0') for entry in st.session_state.voucher_entries)
        total_credit = sum(entry.credit_amount or Decimal('0') for entry in st.session_state.voucher_entries)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Total Debit: ₱{total_debit:,.2f}")
        with col2:
            st.write(f"Total Credit: ₱{total_credit:,.2f}")
        
        if total_debit != total_credit:
            st.warning("Debit and Credit totals must be equal")
        
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not st.session_state.voucher_entries:
                st.error("Please add at least one entry")
                return
            
            if total_debit != total_credit:
                st.error("Debit and Credit totals must be equal")
                return
            
            # Create voucher
            voucher = Voucher(
                date=datetime.combine(date, datetime.min.time()),
                payee=payee,
                total_amount=total_debit,  # or total_credit, they should be equal
                particulars=particulars,
                prepared_by=UUID(st.session_state.user['id']),
                bank_name=bank_name,
                transaction_type=transaction_type,
                reference_number=reference_number,
                entries=st.session_state.voucher_entries
            )
            
            result = expense_manager.create_voucher(voucher)
            if result:
                st.success(f"Voucher {result.voucher_number} created successfully!")
                # Clear form
                st.session_state.voucher_entries = []
                st.rerun()
            else:
                st.error("Failed to create voucher. Please try again.")

def render():
    st.sidebar.title("Expenses")
    page = st.sidebar.radio(
        "Select Form",
        ["Expense Reimbursement Form", "Voucher", "View ERFs"]
    )
    
    if page == "Expense Reimbursement Form":
        render_erf_form()
    elif page == "Voucher":
        render_voucher_form()
    else:
        st.subheader("Expense Reimbursement Forms")
        
        # Filter by status
        status_filter = st.selectbox(
            "Filter by Status",
            [None] + [status.value for status in ExpenseFormStatus],
            format_func=lambda x: "All" if x is None else x.title()
        )
        
        # Get ERFs
        status = ExpenseFormStatus(status_filter) if status_filter else None
        erfs = expense_manager.get_expense_forms(status=status)
        
        if erfs:
            for erf in erfs:
                with st.expander(f"ERF #{erf.form_number} - {erf.status.value.title()}"):
                    st.write(f"Date: {erf.date.strftime('%Y-%m-%d')}")
                    st.write(f"Designation: {erf.designation}")
                    st.write(f"Total Amount: ₱{erf.total_amount:,.2f}")
                    st.write(f"Status: {erf.status.value.title()}")
                    
                    if erf.items:
                        st.write("Items:")
                        for item in erf.items:
                            st.write(f"- {item.description}: {item.payee} - ₱{item.amount:,.2f}")
                    
                    # Show approval buttons for pending ERFs if user has permission
                    if (erf.status == ExpenseFormStatus.PENDING and 
                        st.session_state.user['permissions'].get('can_approve', False)):
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Approve", key=f"approve_{erf.id}"):
                                if expense_manager.update_expense_form_status(
                                    erf.id,
                                    ExpenseFormStatus.APPROVED,
                                    st.session_state.user['id']
                                ):
                                    st.success("ERF approved successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to approve ERF")
                        with col2:
                            if st.button("Reject", key=f"reject_{erf.id}"):
                                if expense_manager.update_expense_form_status(
                                    erf.id,
                                    ExpenseFormStatus.REJECTED,
                                    st.session_state.user['id']
                                ):
                                    st.success("ERF rejected successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to reject ERF")
        else:
            st.info("No expense forms found.")
