import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import re
import gotrue

# Page configuration
st.set_page_config(
    page_title="VIVITA Finance",
    page_icon="",
    layout="wide"
)

from src.views.dashboard import render as dashboard_render
from src.views.settings import render as settings_render
from src.views.suppliers import render as suppliers_render
from src.views.expenses import render as expenses_render
from src.views.purchase_requests import render as purchase_requests_render
from src.config import config

# Initialize session state once
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'supabase' not in st.session_state:
    st.session_state.supabase = None
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'last_attempt' not in st.session_state:
    st.session_state.last_attempt = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'
if 'error' not in st.session_state:
    st.session_state.error = None
if 'success' not in st.session_state:
    st.session_state.success = None
if 'session' not in st.session_state:
    st.session_state.session = None

# Initialize Supabase client
try:
    supabase = create_client(
        supabase_url=st.secrets["SUPABASE_URL"],
        supabase_key=st.secrets["SUPABASE_KEY"]
    )
    st.session_state.supabase = supabase
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {str(e)}")

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*()]", password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

def get_user_permissions(role):
    """Get user permissions based on role"""
    permissions = {
        'can_view_reports': False,
        'can_approve': False,
        'can_manage_users': False
    }
    
    if role == 'Admin':
        permissions.update({
            'can_view_reports': True,
            'can_approve': True,
            'can_manage_users': True,
            'can_manage_pcf': True
        })
    elif role == 'Finance':
        permissions.update({
            'can_view_reports': True,
            'can_approve': True,
            'can_manage_users': False
        })
    elif role == 'PCF_Custodian':
        permissions.update({
            'can_manage_pcf': True
        })
    
    return permissions

def check_rate_limit():
    """Check if user has exceeded login attempts"""
    if st.session_state.login_attempts >= 5:
        if st.session_state.last_attempt:
            time_diff = datetime.now() - st.session_state.last_attempt
            if time_diff < timedelta(minutes=15):
                return False
            st.session_state.login_attempts = 0
    return True

def handle_authentication(email, password, remember_me=False):
    """Handle authentication with Supabase"""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user and auth_response.session:
            # Set session in Supabase
            supabase.auth.set_session(
                auth_response.session.access_token,
                auth_response.session.refresh_token
            )
            
            # Get user profile and permissions
            profile = supabase.table('profiles').select("*").eq('id', auth_response.user.id).single().execute()
            
            if not profile.data:
                st.error("User profile not found. Please contact support.")
                return False
                
            role = profile.data.get('role', 'User')
            permissions = get_user_permissions(role)
            
            # Store session info
            st.session_state.session = {
                'access_token': auth_response.session.access_token,
                'refresh_token': auth_response.session.refresh_token,
                'expires_at': auth_response.session.expires_at
            }
            
            # Update session state
            st.session_state.authenticated = True
            st.session_state.user = {
                'id': auth_response.user.id,
                'email': auth_response.user.email,
                'role': role,
                'permissions': permissions,
                'profile': profile.data
            }
            st.session_state.login_attempts = 0
            st.session_state.error = None
            st.session_state.success = "Login successful!"
            
            # Force a rerun to update the UI
            st.rerun()
            
            return True
        return False
    except gotrue.errors.AuthApiError as e:
        st.session_state.login_attempts += 1
        st.session_state.last_attempt = datetime.now()
        
        error_message = str(e).lower()
        if "email not confirmed" in error_message:
            st.error("Please verify your email address before logging in. Check your inbox for the verification link.")
        elif "invalid login credentials" in error_message:
            st.error("Invalid email or password.")
        else:
            st.error(f"Login failed: {str(e)}")
        
        # Add detailed error logging
        import traceback
        st.write(f"Debug: Full error: {traceback.format_exc()}")
        return False
    except Exception as e:
        st.session_state.login_attempts += 1
        st.session_state.last_attempt = datetime.now()
        st.error(f"Login failed: {str(e)}")
        # Add detailed error logging
        import traceback
        st.write(f"Debug: Full error: {traceback.format_exc()}")
        return False

def check_session():
    """Check and validate user session"""
    try:
        if not st.session_state.get('session'):
            return False
            
        # Try to refresh the session if it's about to expire
        session = st.session_state.session
        if datetime.fromtimestamp(session['expires_at']) < datetime.now() + timedelta(minutes=5):
            try:
                # Refresh the session
                new_session = supabase.auth.refresh_session(session['refresh_token'])
                if new_session and new_session.session:
                    st.session_state.session = {
                        'access_token': new_session.session.access_token,
                        'refresh_token': new_session.session.refresh_token,
                        'expires_at': new_session.session.expires_at
                    }
                    supabase.auth.set_session(
                        new_session.session.access_token,
                        new_session.session.refresh_token
                    )
            except Exception as e:
                st.write(f"Debug: Session refresh failed: {str(e)}")
                return False
        
        # Verify the session is still valid
        try:
            user = supabase.auth.get_user()
            if not user:
                return False
                
            # Get user profile and permissions
            profile = supabase.table('profiles').select("*").eq('id', user.id).single().execute()
            
            if not profile.data:
                st.error("User profile not found")
                return False
                
            role = profile.data.get('role', 'User')
            permissions = get_user_permissions(role)
            
            # Update session state
            st.session_state.authenticated = True
            st.session_state.user = {
                'id': user.id,
                'email': user.email,
                'role': role,
                'permissions': permissions,
                'profile': profile.data
            }
            return True
        except Exception as e:
            st.write(f"Debug: Session validation failed: {str(e)}")
            return False
            
    except Exception as e:
        st.write(f"Debug: Session check failed: {str(e)}")
        st.session_state.authenticated = False
    return False

def login_page():
    """Render login page"""
    st.title("VIVITA Finance Login")
    
    if not check_rate_limit():
        st.error("Too many login attempts. Please try again in 15 minutes.")
        return

    # Add help text about email verification
    st.info("""
    ℹ️ New Users:
    1. Make sure to verify your email before logging in
    2. Check your inbox for the verification link
    3. Click the link to verify your email
    4. If you don't see the email:
       - Check your spam folder
       - Wait a few minutes
       - Contact support if you still haven't received it
    """)

    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("login_form", clear_on_submit=True):
            email = st.text_input("Email", placeholder="Enter your @vivita.ph email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not email.endswith('@vivita.ph'):
                    st.error("Please use your @vivita.ph email address")
                    return
                
                if handle_authentication(email, password, remember_me):
                    st.rerun()

    with col2:
        st.markdown("### New to VIVITA Finance?")
        st.markdown("Create an account to get started with managing your finances.")
        if st.button("Create Account", key="create_account_btn"):
            set_page('signup')
            st.rerun()

def signup_page():
    """Render signup page"""
    st.title("Create Your Account")
    
    # Add a back button at the top
    if st.button("← Back to Login", key="back_to_login"):
        set_page('login')
        st.rerun()
    
    with st.form("signup_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", placeholder="Enter your first name")
            email = st.text_input("Email", placeholder="Enter your @vivita.ph email")
            password = st.text_input("Password", type="password", 
                                   help="Password must be at least 8 characters long")
            
        with col2:
            last_name = st.text_input("Last Name", placeholder="Enter your last name")
            role = st.selectbox("Role", ["User", "Finance", "Admin", "PCF_Custodian"])
            password_confirm = st.text_input("Confirm Password", type="password")
            
        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        submitted = st.form_submit_button("Create Account", use_container_width=True)
        
        if submitted:
            if not all([first_name, last_name, email, password, password_confirm]):
                st.error("Please fill in all fields")
                return
            
            if not email.endswith('@vivita.ph'):
                st.error("Please use your @vivita.ph email address")
                return
            
            is_valid, msg = validate_password(password)
            if not is_valid:
                st.error(msg)
                return
            
            if password != password_confirm:
                st.error("Passwords do not match")
                return
            
            if not terms:
                st.error("Please accept the Terms of Service and Privacy Policy")
                return
            
            try:
                # Create auth user
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "first_name": first_name,
                            "last_name": last_name,
                            "role": role
                        }
                    }
                })
                
                if auth_response.user:
                    # Create profile record
                    try:
                        profile_data = {
                            'id': auth_response.user.id,
                            'first_name': first_name,
                            'last_name': last_name,
                            'role': role,
                            'email': email
                        }
                        profile_result = supabase.table('profiles').insert(profile_data).execute()
                        
                        success_message = """
                        ✅ Account created successfully!
                        
                        Please check your email ({email}) for a confirmation link.
                        You must confirm your email before you can log in.
                        
                        If you don't see the email:
                        1. Check your spam folder
                        2. Wait a few minutes
                        3. Contact support if you still haven't received it
                        """.format(email=email)
                        
                        st.success(success_message)
                        
                        # Add a button to go back to login
                        if st.button("Go to Login Page", key="goto_login_after_signup"):
                            set_page('login')
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating profile: {str(e)}")
                        # Add detailed error logging
                        import traceback
                        st.write(f"Debug: Profile creation error: {traceback.format_exc()}")
            except Exception as e:
                st.error(f"Error creating account: {str(e)}")
                # Add detailed error logging
                import traceback
                st.write(f"Debug: Account creation error: {traceback.format_exc()}")

def logout():
    """Handle user logout"""
    try:
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")

def main():
    """Main application logic"""
    # Show error/success messages if they exist
    if st.session_state.error:
        st.error(st.session_state.error)
        st.session_state.error = None
    if st.session_state.success:
        st.success(st.session_state.success)
        st.session_state.success = None

    # Check authentication status
    if not st.session_state.authenticated:
        if check_session():
            st.experimental_rerun()  # Rerun after successful session restore
        else:
            # Clear any stale session data
            st.session_state.session = None
            st.session_state.authenticated = False
            st.session_state.user = None
            
            # If no valid session, show login or signup page
            if st.session_state.current_page == 'signup':
                signup_page()
            else:
                login_page()
            return

    # User is authenticated, show the main application
    try:
        # Create the main container
        main_container = st.container()
        
        # Sidebar navigation with role-based access
        with st.sidebar:
            st.title("Navigation")
            st.write(f"Welcome {st.session_state.user['email']}")
            st.write(f"Role: {st.session_state.user['role']}")
            
            # Dynamic menu based on user role
            menu_items = ["Dashboard"]
            if st.session_state.user['permissions']['can_approve']:
                menu_items.extend(["Purchase Requests", "Expenses"])
            if st.session_state.user['permissions'].get('can_manage_pcf', False):
                menu_items.append("Petty Cash Fund")
            if st.session_state.user['permissions']['can_view_reports']:
                menu_items.extend(["Suppliers", "Settings"])
            
            page = st.radio("Select Page", menu_items, label_visibility="collapsed")
            if st.button("Logout", type="secondary", key="logout_btn"):
                logout()
                st.rerun()

        # Page routing with permission checks
        try:
            if page == "Dashboard":
                dashboard_render()
            elif page == "Purchase Requests" and st.session_state.user['permissions']['can_approve']:
                purchase_requests_render()
            elif page == "Expenses" and st.session_state.user['permissions']['can_approve']:
                expenses_render()
            elif page == "Petty Cash Fund" and st.session_state.user['permissions'].get('can_manage_pcf', False):
                pcf.render()  # You'll need to import and implement this
            elif page == "Suppliers" and st.session_state.user['permissions']['can_view_reports']:
                suppliers_render()
            elif page == "Settings" and st.session_state.user['permissions']['can_view_reports']:
                settings_render()
            else:
                st.error("You don't have permission to access this page")
        except Exception as e:
            st.error(f"Error loading page: {str(e)}")
            import traceback
            st.write(f"Debug: Page loading error: {traceback.format_exc()}")
    except Exception as e:
        st.error("Session expired. Please log in again.")
        st.session_state.authenticated = False
        st.session_state.session = None
        st.rerun()

if __name__ == "__main__":
    main()