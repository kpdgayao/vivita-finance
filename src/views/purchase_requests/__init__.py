"""Purchase request views package"""
import streamlit as st
from .list import render_prf_list
from .detail import render_prf_details
from .form import generate_prf

def render():
    """Main entry point for purchase request views"""
    st.title("Purchase Requests")
    
    # Add tabs for different PRF views
    tab1, tab2 = st.tabs(["Create New PRF", "View PRFs"])
    
    with tab1:
        generate_prf()
    
    with tab2:
        render_prf_list()

__all__ = ['render']
