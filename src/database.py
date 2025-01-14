import streamlit as st
from supabase import create_client

def get_supabase_client():
    """Get a configured Supabase client instance."""
    client = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    
    # Set session if authenticated
    if 'session' in st.session_state and st.session_state.session:
        client.auth.set_session(
            st.session_state.session['access_token'],
            st.session_state.session['refresh_token']
        )
    
    return client
