import streamlit as st

def render():
    st.title("Settings")
    
    # User Information
    st.subheader("User Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Name:", st.session_state.user['name'])
        st.write("Email:", st.session_state.user['email'])
    
    with col2:
        st.write("Role:", st.session_state.user['role'])
        
    # App Settings
    st.subheader("App Settings")
    st.info("More settings will be added in future updates.")
