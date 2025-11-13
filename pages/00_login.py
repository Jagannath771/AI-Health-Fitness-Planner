import streamlit as st
from database import authenticate_user, create_user
import re

st.title("Login / Sign Up")
st.markdown("Welcome to FitLife Planner! Please sign in or create a new account.")

# Create tabs for Login and Sign Up
tab1, tab2 = st.tabs(["Login", "Sign Up"])

with tab1:
    st.header("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your@email.com")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login", width="stretch")
        
        if login_button:
            if not email or not password:
                st.error("Please fill in all fields")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Please enter a valid email address")
            else:
                user, message = authenticate_user(email, password)
                if user:
                    st.session_state.user_id = user.user_id
                    st.session_state.email = user.email
                    st.session_state.timezone = user.timezone
                    st.session_state.authenticated = True
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error(message)

with tab2:
    st.header("Sign Up")
    
    with st.form("signup_form"):
        new_email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "CST", "MST"], key="signup_timezone")
        signup_button = st.form_submit_button("Create Account", width="stretch")
        
        if signup_button:
            if not new_email or not new_password or not confirm_password:
                st.error("Please fill in all fields")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                st.error("Please enter a valid email address")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                user, message = create_user(new_email, new_password, timezone)
                if user:
                    st.session_state.user_id = user.user_id
                    st.session_state.email = user.email
                    st.session_state.timezone = user.timezone
                    st.session_state.authenticated = True
                    st.success("Account created successfully! Redirecting...")
                    st.rerun()
                else:
                    st.error(message)

# Demo mode option
st.markdown("---")
st.markdown("### Demo Mode")
if st.button("Continue as Demo User", width="stretch"):
    st.session_state.user_id = "demo_user"
    st.session_state.email = "demo@example.com"
    st.session_state.timezone = "UTC"
    st.session_state.authenticated = True
    st.rerun()
