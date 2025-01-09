import streamlit as st
from views import dashboard, settings, suppliers
from interfaces.prof import PROFInterface
from crud import UserManager

# Configure the Streamlit page
st.set_page_config(
    page_title="VIVITA Finance",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("VIVITA Finance Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Simple authentication for testing
            if email == "kevin@vivita.ph" and password == "vivita2024":
                if email.endswith('@vivita.ph'):
                    # Get or create user in database
                    user_manager = UserManager()
                    user = user_manager.get_or_create_user(
                        email=email,
                        full_name="Kevin",
                        role="Finance"
                    )
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'id': user['id'],
                            'name': user['full_name'],
                            'email': user['email'],
                            'role': user['role']
                        }
                        st.rerun()
                    else:
                        st.error("Failed to create user profile")
                else:
                    st.error("Only '@vivita.ph' email addresses are allowed for account creation.")
            else:
                st.error("Invalid credentials")
                
    st.button("Sign Up", on_click=signup)

def signup():
    st.title("Sign Up")
    with st.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Create Account")
        if submitted:
            if email.endswith('@vivita.ph'):
                user_manager = UserManager()
                user = user_manager.get_or_create_user(
                    email=email,
                    full_name="New User",
                    role="Finance"
                )
                if user:
                    st.success("Account created successfully! You can now log in.")
                else:
                    st.error("Failed to create user profile")
            else:
                st.error("Only '@vivita.ph' email addresses are allowed for account creation.")

def main():
    # Create the main container
    main_container = st.container()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Go to",
            ["Dashboard", "Purchase Requests", "Suppliers", "Settings"],
            label_visibility="collapsed"
        )
    
    # Page routing in the main container
    with main_container:
        if page == "Dashboard":
            dashboard.render()
        elif page == "Purchase Requests":
            prof_interface = PROFInterface()
            prof_interface.render()
        elif page == "Suppliers":
            suppliers.render()
        elif page == "Settings":
            settings.render()

# Main app logic
if not st.session_state.authenticated:
    login()
else:
    main()
