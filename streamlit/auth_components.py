"""
Reusable authentication UI components for Streamlit
Provides login and registration forms
"""
import streamlit as st
import re
from auth_utils import register_user, login_user, logout_user

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid: bool, message: str)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def render_login_form():
    """Render login form"""
    st.subheader("🔐 Login")
    
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="user@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submit:
            # Validate inputs
            if not email or not password:
                st.error("Please fill in all fields")
                return
            
            if not validate_email(email):
                st.error("Please enter a valid email address")
                return
            
            # Attempt login
            with st.spinner("Logging in..."):
                success, message = login_user(email, password)
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def render_register_form():
    """Render registration form"""
    st.subheader("📝 Register")
    
    with st.form("register_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="user@example.com")
        password = st.text_input("Password", type="password", placeholder="Min 8 chars, 1 uppercase, 1 number")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
        submit = st.form_submit_button("Register", type="primary", use_container_width=True)
        
        if submit:
            # Validate inputs
            if not email or not password or not confirm_password:
                st.error("Please fill in all fields")
                return
            
            if not validate_email(email):
                st.error("Please enter a valid email address")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            # Validate password strength
            is_valid, pwd_message = validate_password(password)
            if not is_valid:
                st.error(pwd_message)
                return
            
            # Attempt registration
            with st.spinner("Creating account..."):
                success, message = register_user(email, password)
            
            if success:
                st.success(message)
                st.info("Please login with your new credentials")
            else:
                st.error(message)

def render_auth_page():
    """Render full authentication page with tabs"""
    st.title("🤖 Chronos AI")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_register_form()
    
    st.markdown("---")
    st.caption("💡 Secure authentication powered by JWT")

def render_user_menu():
    """Render user menu in sidebar for authenticated users"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 Account")
        
        if st.session_state.user_email:
            st.write(f"**Email:** {st.session_state.user_email}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.success("Logged out successfully")
            st.rerun()
