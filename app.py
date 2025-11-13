import streamlit as st
import os
from database import (
    init_db, get_or_create_profile, SessionLocal,
    Questionnaire, Equipment, Pantry, Availability, WeeklyPlan
)
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

# Check user progress
db = SessionLocal()
user_progress = {
    'onboarding': db.query(Questionnaire).filter(Questionnaire.user_id == st.session_state.user_id).first() is not None,
    'equipment': db.query(Equipment).filter(Equipment.user_id == st.session_state.user_id).first() is not None,
    'pantry': db.query(Pantry).filter(Pantry.user_id == st.session_state.user_id).first() is not None,
    'schedule': db.query(Availability).filter(Availability.user_id == st.session_state.user_id).first() is not None,
    'weekly_plan': db.query(WeeklyPlan).filter(WeeklyPlan.user_id == st.session_state.user_id).first() is not None
}
db.close()

# Main hero section with full width and progress guidance
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

# Progress guidance section
if not all(user_progress.values()):
    st.markdown("""
    <div style='padding: 1.5rem; margin-bottom: 2rem; border-radius: 10px; background: rgba(20,176,143,0.1); border: 1px solid rgba(20,176,143,0.2);'>
        <h3 style='margin-bottom: 1rem;'>🎯 Complete Your Setup</h3>
    </div>
    """, unsafe_allow_html=True)

    # Determine next step
    next_step = None
    if not user_progress['onboarding']:
        next_step = ('onboarding', "Let's start by setting up your profile and goals", "pages/01_onboarding.py")
    elif not user_progress['equipment']:
        next_step = ('equipment', "Next, let's add your available workout equipment", "pages/02_equipment.py")
    elif not user_progress['pantry']:
        next_step = ('pantry', "Now, let's set up your pantry items", "pages/03_pantry.py")
    elif not user_progress['schedule']:
        next_step = ('schedule', "Let's configure your weekly schedule", "pages/04_schedule.py")
    elif not user_progress['weekly_plan']:
        next_step = ('weekly_plan', "You're all set! Let's create your first weekly plan", "pages/05_weekly_plan.py")

    if next_step:
        st.info(f"👉 **Next Step**: {next_step[1]}")
        if st.button("Continue Setup →"):
            st.switch_page(next_step[2])

# Quick action cards showing progress
st.markdown("<div style='margin-bottom: 3rem;'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

def get_status_color(is_complete):
    return "rgba(20,176,143,1)" if is_complete else "#b8c0cc"

def get_status_icon(is_complete):
    return "✓" if is_complete else "○"

with c1:
    onboarding_status = get_status_icon(user_progress['onboarding'])
    st.markdown(
        f"""<div style='background: rgba(20,176,143,0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(20,176,143,0.2);'>
            <h3 style='margin-bottom: 1rem;'>Profile & Goals {onboarding_status}</h3>
            <p style='margin-bottom: 1rem; color: {get_status_color(user_progress['onboarding'])};'>Set your fitness and wellness objectives.</p>
        </div>""",
        unsafe_allow_html=True
    )
    if st.button("Update Goals →", key="goals_btn"):
        st.switch_page("pages/01_onboarding.py")

with c2:
    equipment_status = get_status_icon(user_progress['equipment'])
    pantry_status = get_status_icon(user_progress['pantry'])
    st.markdown(
        f"""<div style='background: rgba(122,168,255,0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(122,168,255,0.2);'>
            <h3 style='margin-bottom: 1rem;'>Equipment {equipment_status} & Pantry {pantry_status}</h3>
            <p style='margin-bottom: 1rem; color: {get_status_color(user_progress['equipment'] and user_progress['pantry'])};'>Manage your available resources and groceries.</p>
        </div>""",
        unsafe_allow_html=True
    )
    if not user_progress['equipment']:
        if st.button("Add Equipment →", key="equipment_btn"):
            st.switch_page("pages/02_equipment.py")
    elif not user_progress['pantry']:
        if st.button("Set Up Pantry →", key="pantry_btn"):
            st.switch_page("pages/03_pantry.py")
    else:
        if st.button("Manage Resources →", key="resources_btn"):
            st.switch_page("pages/02_equipment.py")

with c3:
    schedule_status = get_status_icon(user_progress['schedule'])
    plan_status = get_status_icon(user_progress['weekly_plan'])
    st.markdown(
        f"""<div style='background: rgba(255,122,122,0.1); padding: 1.5rem; border-radius: 10px; border: 1px solid rgba(255,122,122,0.2);'>
            <h3 style='margin-bottom: 1rem;'>Schedule {schedule_status} & Plan {plan_status}</h3>
            <p style='margin-bottom: 1rem; color: {get_status_color(user_progress['schedule'] and user_progress['weekly_plan'])};'>Set your availability and get personalized plans.</p>
        </div>""",
        unsafe_allow_html=True
    )
    if not user_progress['schedule']:
        if st.button("Set Schedule →", key="schedule_btn"):
            st.switch_page("pages/04_schedule.py")
    elif not user_progress['weekly_plan']:
        if st.button("Create Plan →", key="plan_btn"):
            st.switch_page("pages/05_weekly_plan.py")
    else:
        if st.button("View Plan →", key="view_plan_btn"):
            st.switch_page("pages/05_weekly_plan.py")

st.markdown("</div>", unsafe_allow_html=True)

# Getting Started section - show progress
st.markdown("""
<div style='background: rgba(0,0,0,0.2); padding: 2rem; border-radius: 10px; margin: 2rem 0;'>
    <h2 style='margin-bottom: 2rem;'>Your Progress</h2>
</div>
""", unsafe_allow_html=True)

steps = st.columns([1,1,1])

with steps[0]:
    profile_color = "rgba(20,176,143,1)" if user_progress['onboarding'] else "#b8c0cc"
    st.markdown(f"""
    <div style='background: rgba(20,176,143,0.1); padding: 1.5rem; border-radius: 10px; height: 100%;'>
        <h3 style='margin-bottom: 1rem;'>1. Set Up Your Profile</h3>
        <ul style='list-style-type: none; padding-left: 0;'>
            <li style='color: {profile_color};'>{get_status_icon(user_progress['onboarding'])} Complete onboarding</li>
            <li style='color: {profile_color};'>{get_status_icon(user_progress['onboarding'])} Define your goals</li>
            <li style='color: {profile_color};'>{get_status_icon(user_progress['onboarding'])} Set preferences</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with steps[1]:
    st.markdown(f"""
    <div style='background: rgba(122,168,255,0.1); padding: 1.5rem; border-radius: 10px; height: 100%;'>
        <h3 style='margin-bottom: 1rem;'>2. Configure Resources</h3>
        <ul style='list-style-type: none; padding-left: 0;'>
            <li style='color: {get_status_color(user_progress['equipment'])};'>{get_status_icon(user_progress['equipment'])} Add available equipment</li>
            <li style='color: {get_status_color(user_progress['pantry'])};'>{get_status_icon(user_progress['pantry'])} Update pantry items</li>
            <li style='color: {get_status_color(user_progress['schedule'])};'>{get_status_icon(user_progress['schedule'])} Set schedule availability</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with steps[2]:
    plan_color = "rgba(255,122,122,1)" if user_progress['weekly_plan'] else "#b8c0cc"
    st.markdown(f"""
    <div style='background: rgba(255,122,122,0.1); padding: 1.5rem; border-radius: 10px; height: 100%;'>
        <h3 style='margin-bottom: 1rem;'>3. Start Your Journey</h3>
        <ul style='list-style-type: none; padding-left: 0;'>
            <li style='color: {plan_color};'>{get_status_icon(user_progress['weekly_plan'])} Generate weekly plan</li>
            <li style='color: {plan_color};'>{get_status_icon(user_progress['weekly_plan'])} Track daily progress</li>
            <li style='color: {plan_color};'>{get_status_icon(user_progress['weekly_plan'])} Adapt and improve</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Navigation Menu
st.markdown("""
<div style='background: rgba(0,0,0,0.2); padding: 2rem; border-radius: 10px; margin: 2rem 0;'>
    <h2 style='margin-bottom: 2rem;'>Navigation Menu</h2>
</div>
""", unsafe_allow_html=True)

menu_cols = st.columns(4)

# Define the navigation items with their status and paths
nav_items = [
    {
        'name': '1. Profile & Goals',
        'icon': '👤',
        'path': 'pages/01_onboarding.py',
        'status': user_progress['onboarding'],
        'description': 'Set up your profile and fitness goals'
    },
    {
        'name': '2. Equipment',
        'icon': '🏋️',
        'path': 'pages/02_equipment.py',
        'status': user_progress['equipment'],
        'description': 'Add your available workout equipment'
    },
    {
        'name': '3. Pantry',
        'icon': '🥗',
        'path': 'pages/03_pantry.py',
        'status': user_progress['pantry'],
        'description': 'Manage your pantry items'
    },
    {
        'name': '4. Schedule',
        'icon': '📅',
        'path': 'pages/04_schedule.py',
        'status': user_progress['schedule'],
        'description': 'Set your weekly availability'
    }
]

# Render the first row of navigation items
for i, item in enumerate(nav_items):
    with menu_cols[i]:
        status_icon = "✓" if item['status'] else "○"
        status_color = "rgba(20,176,143,1)" if item['status'] else "#b8c0cc"
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 10px; text-align: center;'>
            <div style='font-size: 2rem;'>{item['icon']}</div>
            <h4>{item['name']} <span style='color: {status_color}'>{status_icon}</span></h4>
            <p style='color: #b8c0cc; font-size: 0.9rem; min-height: 40px;'>{item['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"Go to {item['name'].split('.')[1].strip()} →",
                key=f"nav_{i}",
                width="stretch",
                type="primary" if not item['status'] else "secondary"
            ):
                st.switch_page(item['path'])

# Add some spacing between rows
st.markdown("<br>", unsafe_allow_html=True)

# Second row of navigation items
menu_cols2 = st.columns(4)
nav_items2 = [
    {
        'name': '5. Weekly Plan',
        'icon': '📊',
        'path': 'pages/05_weekly_plan.py',
        'status': user_progress['weekly_plan'],
        'description': 'View your personalized weekly plan'
    },
    {
        'name': '6. Today',
        'icon': '📋',
        'path': 'pages/06_today.py',
        'status': user_progress['weekly_plan'],
        'description': "Today's workout and meals"
    },
    {
        'name': '7. Progress',
        'icon': '📈',
        'path': 'pages/07_progress.py',
        'status': user_progress['weekly_plan'],
        'description': 'Track your fitness journey'
    },
    {
        'name': '8. Settings',
        'icon': '⚙️',
        'path': 'pages/08_settings.py',
        'status': True,  # Settings are always available
        'description': 'Adjust your preferences'
    }
]

# Render the second row of navigation items
for i, item in enumerate(nav_items2):
    with menu_cols2[i]:
        status_icon = "✓" if item['status'] else "○"
        status_color = "rgba(20,176,143,1)" if item['status'] else "#b8c0cc"
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 10px; text-align: center;'>
            <div style='font-size: 2rem;'>{item['icon']}</div>
            <h4>{item['name']} <span style='color: {status_color}'>{status_icon}</span></h4>
            <p style='color: #b8c0cc; font-size: 0.9rem; min-height: 40px;'>{item['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"Go to {item['name'].split('.')[1].strip()} →",
                key=f"nav2_{i}",
                width="stretch",
                type="primary" if not item['status'] else "secondary"
            ):
                st.switch_page(item['path'])
