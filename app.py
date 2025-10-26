import streamlit as st
import os
from database import init_db, get_or_create_profile

st.set_page_config(
    page_title="FitLife Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"
    st.session_state.email = "demo@example.com"
    st.session_state.timezone = "UTC"

get_or_create_profile(
    user_id=st.session_state.user_id,
    email=st.session_state.email,
    timezone=st.session_state.timezone
)

st.sidebar.title("💪 FitLife Planner")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📋 Onboarding",
        "🏋️ Equipment",
        "🥗 Pantry",
        "📅 Schedule",
        "📊 Weekly Plan",
        "📆 Today",
        "📈 Progress",
        "⚙️ Settings"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"👤 {st.session_state.email}")
st.sidebar.caption(f"🕐 {st.session_state.timezone}")

if page == "🏠 Home":
    st.title("Welcome to FitLife Planner")
    st.markdown("""
    ### AI-Powered Fitness & Lifestyle Planning
    
    Get personalized weekly workout and meal plans that adapt to your:
    - 🎯 Goals and fitness level
    - 🏋️ Available equipment
    - 🥗 Pantry items and shopping schedule
    - 📅 Free time blocks
    - 🏢 Gym access patterns
    
    #### Getting Started
    1. **Complete Onboarding** - Tell us about yourself, goals, diet, and schedule
    2. **Add Equipment** - List what you have at home or at the gym
    3. **Update Pantry** - Track your groceries and shopping frequency
    4. **Set Schedule** - Define when you're free to work out
    5. **Generate Plan** - Get your AI-powered weekly plan
    6. **Track Progress** - Log daily adherence and watch your plan adapt
    
    Navigate using the sidebar to begin!
    """)
    
    st.info("👈 Start with **Onboarding** to set up your profile")

elif page == "📋 Onboarding":
    exec(open("pages/01_onboarding.py").read())

elif page == "🏋️ Equipment":
    exec(open("pages/02_equipment.py").read())

elif page == "🥗 Pantry":
    exec(open("pages/03_pantry.py").read())

elif page == "📅 Schedule":
    exec(open("pages/04_schedule.py").read())

elif page == "📊 Weekly Plan":
    exec(open("pages/05_weekly_plan.py").read())

elif page == "📆 Today":
    exec(open("pages/06_today.py").read())

elif page == "📈 Progress":
    exec(open("pages/07_progress.py").read())

elif page == "⚙️ Settings":
    exec(open("pages/08_settings.py").read())
