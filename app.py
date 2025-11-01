import streamlit as st
import os
from database import init_db, get_or_create_profile
from nav import apply_global_ui, top_nav

# Apply global UI settings
apply_global_ui()
init_db()

# Check if user is authenticated
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    # Show login page
    exec(open("pages/00_login.py", encoding="utf-8").read())
    st.stop()

# User is authenticated, continue with the app
get_or_create_profile(
    user_id=st.session_state.user_id,
    email=st.session_state.email,
    timezone=st.session_state.timezone
)

# Add top navigation
top_nav(is_authed=True, current="Home")

# User info in a clean card format
user_info = st.container()
with user_info:
    st.markdown(f"""
    <div style='text-align: right; padding: 10px;'>
        <span style='color: var(--text-dim);'>👤 {st.session_state.email}</span> •
        <span style='color: var(--text-dim);'>🕐 {st.session_state.timezone}</span>
    </div>
    """, unsafe_allow_html=True)

# Main hero section with full width
st.markdown("""
<div style='padding: 2rem; margin-bottom: 2rem; border-radius: 10px; background: rgba(0,0,0,0.2);'>
    <h1 style='font-size: 2.5rem; margin-bottom: 1rem;'>Welcome to FitLife Planner</h1>
    <h3 style='font-size: 1.5rem; color: #b8c0cc; margin-bottom: 1rem;'>AI-Powered Fitness & Lifestyle Planning</h3>
    <p style='font-size: 1.1rem; color: #8b95a5;'>
        Get personalized weekly workout and meal plans that adapt to your:<br>
        • Goals and fitness level<br>
        • Available equipment<br>
        • Schedule and resources
    </p>
</div>
""", unsafe_allow_html=True)

# Quick action cards
st.markdown("<div style='margin-bottom: 3rem;'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """<div style='background: rgba(20,176,143,0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(20,176,143,0.2);'>
            <h3 style='margin-bottom: 1rem;'>Goals</h3>
            <p style='margin-bottom: 1rem; color: #b8c0cc;'>Set and track your fitness and wellness objectives.</p>
        </div>""",
        unsafe_allow_html=True
    )
    if st.button("Update Goals →", key="goals_btn"):
        st.switch_page("pages/01_onboarding.py")

with c2:
    st.markdown(
        """<div style='background: rgba(122,168,255,0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(122,168,255,0.2);'>
            <h3 style='margin-bottom: 1rem;'>Equipment & Pantry</h3>
            <p style='margin-bottom: 1rem; color: #b8c0cc;'>Manage your available resources and groceries.</p>
        </div>""",
        unsafe_allow_html=True
    )
    if st.button("Manage Resources →", key="equipment_btn"):
        st.switch_page("pages/02_equipment.py")

with c3:
    st.markdown(
        """<div style='background: rgba(255,122,122,0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(255,122,122,0.2);'>
            <h3 style='margin-bottom: 1rem;'>Weekly Planning</h3>
            <p style='margin-bottom: 1rem; color: #b8c0cc;'>Get your AI-powered workout and meal schedule.</p>
        </div>""",
        unsafe_allow_html=True
    )
    if st.button("View Plan →", key="plan_btn"):
        st.switch_page("pages/05_weekly_plan.py")

st.markdown("</div>", unsafe_allow_html=True)

# Getting Started section
st.markdown("""
<div style='background: rgba(0,0,0,0.2); padding: 2rem; border-radius: 10px; margin: 2rem 0;'>
    <h2 style='margin-bottom: 2rem;'>Getting Started</h2>
</div>
""", unsafe_allow_html=True)

steps = st.columns([1,1,1])

with steps[0]:
    st.markdown("""
    <div style='background: rgba(20,176,143,0.1); padding: 1.5rem; border-radius: 10px; height: 100%;'>
        <h3 style='margin-bottom: 1rem;'>1. Set Up Your Profile</h3>
        <ul style='color: #b8c0cc; list-style-type: none; padding-left: 0;'>
            <li>✓ Complete onboarding</li>
            <li>✓ Define your goals</li>
            <li>✓ Set preferences</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with steps[1]:
    st.markdown("""
    <div style='background: rgba(122,168,255,0.1); padding: 1.5rem; border-radius: 10px; height: 100%;'>
        <h3 style='margin-bottom: 1rem;'>2. Configure Resources</h3>
        <ul style='color: #b8c0cc; list-style-type: none; padding-left: 0;'>
            <li>🏋️ Add available equipment</li>
            <li>🥗 Update pantry items</li>
            <li>📅 Set schedule availability</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with steps[2]:
    st.markdown("""
    <div style='background: rgba(255,122,122,0.1); padding: 1.5rem; border-radius: 10px; height: 100%;'>
        <h3 style='margin-bottom: 1rem;'>3. Start Your Journey</h3>
        <ul style='color: #b8c0cc; list-style-type: none; padding-left: 0;'>
            <li>📊 Generate weekly plan</li>
            <li>📈 Track daily progress</li>
            <li>🔄 Adapt and improve</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Features section in two columns
st.markdown("""
<div style='background: rgba(0,0,0,0.2); padding: 2rem; border-radius: 10px; margin: 2rem 0;'>
    <h2 style='margin-bottom: 2rem;'>Features</h2>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style='background: rgba(20,176,143,0.1); padding: 1.5rem; border-radius: 10px;'>
        <h3 style='margin-bottom: 1rem;'>Personalized Planning</h3>
        <ul style='color: #b8c0cc; list-style-type: none; padding-left: 0;'>
            <li>🎯 Goals and fitness level based</li>
            <li>🏋️ Available equipment optimized</li>
            <li>🥗 Smart meal planning with your pantry</li>
            <li>📅 Schedule-aware workout times</li>
            <li>🏢 Flexible gym/home workout options</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: rgba(122,168,255,0.1); padding: 1.5rem; border-radius: 10px;'>
        <h3 style='margin-bottom: 1rem;'>Smart Adaptation</h3>
        <ul style='color: #b8c0cc; list-style-type: none; padding-left: 0;'>
            <li>📈 Progress tracking and analytics</li>
            <li>🔄 Plan adjustments based on adherence</li>
            <li>💪 Difficulty progression</li>
            <li>🎮 Interactive daily logging</li>
            <li>📱 Mobile-friendly interface</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
