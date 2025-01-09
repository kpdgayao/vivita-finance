import streamlit as st
from src.views import dashboard, settings, suppliers, expenses
from src.interfaces.prof import PROFInterface
from supabase import create_client
from src.config import config

# Initialize Supabase client
try:
    st.write("Initializing Supabase with:")
    st.write("URL:", config.SUPABASE_URL)
    st.write("Key:", config.SUPABASE_KEY[:10] + "..." if config.SUPABASE_KEY else "None")
    
    supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    # Test the connection
    response = supabase.auth.get_user()
    st.write("Supabase initialized successfully")
except Exception as e:
    st.error(f"Failed to initialize Supabase: {str(e)}")
    supabase = None

# Configure the Streamlit page
st.set_page_config(
    page_title="VIVITA Finance",
    page_icon="",
    layout="wide"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    st.title("VIVITA Finance Login")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("login_form", clear_on_submit=True):
            email = st.text_input("Email", placeholder="Enter your @vivita.ph email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields")
                    return
                    
                if not email.endswith('@vivita.ph'):
                    st.error("Please use your @vivita.ph email address")
                    return
                
                try:
                    # Authenticate with Supabase
                    auth_response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    user = auth_response.user
                    if user:
                        # Get user profile from database
                        profile = supabase.table('profiles').select("*").eq('id', user.id).single().execute()
                        
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'id': user.id,
                            'email': user.email,
                            'role': profile.data.get('role', 'User') if profile.data else 'User'
                        }
                        if remember_me:
                            st.session_state.remember_me = True
                        st.success("Login successful!")
                        st.rerun()
                except Exception as e:
                    st.error("Invalid email or password")
                    
        st.markdown("---")
        st.button("Forgot Password?", on_click=forgot_password, type="secondary", use_container_width=True)

    with col2:
        st.markdown("### New to VIVITA Finance?")
        st.markdown("Create an account to get started with managing your finances.")
        st.button("Create Account", on_click=signup, type="primary", use_container_width=True)

def signup():
    st.title("Create Your Account")
    
    # Debug: Show Supabase status
    if not supabase:
        st.error("Supabase client is not initialized")
        return
    
    with st.form("signup_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", placeholder="Enter your first name")
            email = st.text_input("Email", placeholder="Enter your @vivita.ph email")
            password = st.text_input("Password", type="password", 
                                   help="Password must be at least 8 characters long and contain letters and numbers")
        with col2:
            last_name = st.text_input("Last Name", placeholder="Enter your last name")
            role = st.selectbox("Role", ["Finance", "Admin", "User"])
            password_confirm = st.text_input("Confirm Password", type="password")
            
        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            st.write("Form submitted with:")
            st.write({
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "role": role
            })
            
            if not all([first_name, last_name, email, password, password_confirm]):
                st.error("Please fill in all fields")
                return
                
            if not email.endswith('@vivita.ph'):
                st.error("Please use your @vivita.ph email address")
                return
                
            if len(password) < 8:
                st.error("Password must be at least 8 characters long")
                return
                
            if not terms:
                st.error("Please accept the Terms of Service and Privacy Policy")
                return
                
            if password == password_confirm:
                try:
                    st.info("Creating your account...")
                    
                    # Create user in Supabase Auth - profile will be created automatically by trigger
                    auth_data = {
                        "email": email,
                        "password": password,
                        "options": {
                            "data": {
                                "first_name": first_name,
                                "last_name": last_name,
                                "role": role
                            }
                        }
                    }
                    st.write("Sending auth data to Supabase:", auth_data)
                    
                    auth_response = supabase.auth.sign_up(auth_data)
                    st.write("Received auth response:", auth_response)
                    
                    if hasattr(auth_response, 'user') and auth_response.user:
                        st.success(f"Account created successfully! User ID: {auth_response.user.id}")
                        if st.button("Go to Login"):
                            login()
                    else:
                        st.error("Failed to create account. Please try again.")
                        st.write("Debug - Auth Response:", auth_response)
                        
                except Exception as e:
                    st.error(f"Error creating account: {str(e)}")
                    st.write("Debug - Error details:", e)
                    import traceback
                    st.write("Traceback:", traceback.format_exc())
            else:
                st.error("Passwords do not match")

    if st.button("Back to Login", type="secondary"):
        login()

def forgot_password():
    st.title("Reset Your Password")
    
    with st.form("forgot_password_form", clear_on_submit=True):
        st.markdown("Enter your email address below and we'll send you instructions to reset your password.")
        email = st.text_input("Email", placeholder="Enter your @vivita.ph email")
        submitted = st.form_submit_button("Send Reset Link", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
                return
                
            if not email.endswith('@vivita.ph'):
                st.error("Please enter a valid @vivita.ph email address")
                return
                
            try:
                # Send password reset email through Supabase
                supabase.auth.reset_password_email(email)
                st.success("If an account exists for this email, you will receive password reset instructions.")
            except Exception as e:
                st.error("An error occurred while sending the reset link. Please try again later.")
            
    st.button("Back to Login", on_click=login, type="secondary")

def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()

def main():
    # Create the main container
    main_container = st.container()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Select Page",
            ["Dashboard", "Purchase Requests", "Expenses", "Suppliers", "Settings"],
            label_visibility="collapsed"
        )
        if st.button("Logout"):
            logout()
    
    # Page routing in the main container
    with main_container:
        if page == "Dashboard":
            dashboard.render()
        elif page == "Purchase Requests":
            prof = PROFInterface()
            prof.render()
        elif page == "Expenses":
            expenses.render()
        elif page == "Suppliers":
            suppliers.render()
        elif page == "Settings":
            settings.render()

# Main app logic
if not st.session_state.authenticated:
    login()
else:
    main()
