"""
Authentication utilities for Streamlit frontend
Handles user registration, login, token management, and session state
"""
import streamlit as st
import requests
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import control

# Use API URL from control.py
API_URL = control.API_BASE_URL

def init_auth_state():
    """Initialize authentication session state"""
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

def is_authenticated() -> bool:
    """Check if user is currently authenticated"""
    return st.session_state.access_token is not None

def register_user(email: str, password: str) -> tuple[bool, str]:
    """
    Register a new user
    Returns: (success: bool, message: str)
    """
    try:
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 201:
            return True, "Registration successful! Please login."
        else:
            error_detail = response.json().get("detail", "Registration failed")
            return False, error_detail
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Is it running on port 8026?"
    except Exception as e:
        return False, f"Error: {str(e)}"

def login_user(email: str, password: str) -> tuple[bool, str]:
    """
    Login user and store access token
    Returns: (success: bool, message: str)
    """
    try:
        # OAuth2 expects form data with username/password fields
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={"username": email, "password": password},  # username field is used for email
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            
            # Fetch user details
            success, user_data = get_current_user()
            if success and user_data:
                st.session_state.user_email = user_data.get("email")
                st.session_state.user_id = user_data.get("id")
                return True, f"Welcome back, {user_data.get('email')}!"
            else:
                return True, "Login successful!"
        else:
            error_detail = response.json().get("detail", "Login failed")
            return False, error_detail
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Is it running on port 8026?"
    except Exception as e:
        return False, f"Error: {str(e)}"

def logout_user():
    """Clear authentication session state"""
    st.session_state.access_token = None
    st.session_state.user_email = None
    st.session_state.user_id = None

def get_current_user() -> tuple[bool, Optional[dict]]:
    """
    Fetch current authenticated user details
    Returns: (success: bool, user_data: dict or None)
    """
    if not is_authenticated():
        return False, None
    
    try:
        response = requests.get(
            f"{API_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            # Token might be expired or invalid
            logout_user()
            return False, None
            
    except Exception as e:
        return False, None

def get_auth_headers() -> dict:
    """Get authorization headers for API requests"""
    if is_authenticated():
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}
