import streamlit as st
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

# Main hero section with brand and clear value prop
st.markdown("""
<div style='padding: 2rem; margin-bottom: 2rem; border-radius: 10px; background: rgba(0,0,0,0.2);'>
    <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>FitDietGenie</h1>
    <h3 style='font-size: 1.4rem; color: #b8c0cc; margin-bottom: 1rem;'>Smart plans for meals and movement</h3>
    <p style='font-size: 1.05rem; color: #b8c0cc; line-height: 1.6;'>
        Meet your AI Genie for better habits. It learns your goals, schedule, equipment, and pantry to conjure
        weekly workouts and balanced meals that actually fit your life. No overwhelm—just one clear next step,
        every time.
    </p>
    <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 1rem;'>
        <div style='background: rgba(255,255,255,0.04); padding: 0.8rem; border-radius: 8px;'>✨ Personalized weekly plans</div>
        <div style='background: rgba(255,255,255,0.04); padding: 0.8rem; border-radius: 8px;'>🧠 Adapts to your routine</div>
        <div style='background: rgba(255,255,255,0.04); padding: 0.8rem; border-radius: 8px;'>🥗 Uses what you already have</div>
        <div style='background: rgba(255,255,255,0.04); padding: 0.8rem; border-radius: 8px;'>📷 Upload photos → AI auto‑adds gear & pantry</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Helper to determine the next step and CTA label
def determine_next_step(progress):
    if not progress['onboarding']:
        return (
            'onboarding',
            "Let's start by setting up your profile and goals",
            "pages/01_onboarding.py",
            "Get Started"
        )
    if not progress['equipment']:
        return (
            'equipment',
            "Add your available workout equipment",
            "pages/02_equipment.py",
            "Continue setup"
        )
    if not progress['pantry']:
        return (
            'pantry',
            "Set up your pantry items",
            "pages/03_pantry.py",
            "Continue setup"
        )
    if not progress['schedule']:
        return (
            'schedule',
            "Configure your weekly schedule",
            "pages/04_schedule.py",
            "Continue setup"
        )
    if not progress['weekly_plan']:
        return (
            'weekly_plan',
            "You're all set! Create your first weekly plan",
            "pages/05_weekly_plan.py",
            "Create weekly plan"
        )
    return None

next_step = determine_next_step(user_progress)

# Primary CTA section (centered and minimal)
cta_left, cta_center, cta_right = st.columns([1, 2, 1])
with cta_center:
    if next_step:
        st.info(f"👉 {next_step[1]}")
        if st.button(f"{next_step[3]} →", type="primary", use_container_width=True):
            st.switch_page(next_step[2])
    else:
        st.success("You're all set! Pick where to go.")
        go_today, go_plan = st.columns(2)
        with go_today:
            if st.button("Today", use_container_width=True):
                st.switch_page("pages/06_today.py")
        with go_plan:
            if st.button("Weekly Plan", use_container_width=True):
                st.switch_page("pages/05_weekly_plan.py")
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Settings", use_container_width=True):
            st.switch_page("pages/08_settings.py")



# Step-by-step guidance section
st.markdown(
    """
    <div style='background: rgba(0,0,0,0.2); padding: 2rem; border-radius: 10px; margin: 1.5rem 0;'>
        <h2 style='margin-top: 0;'>How it works</h2>
        <ol style='line-height: 1.8; color:#b8c0cc;'>
            <li><strong>Profile & Goals</strong> — Tell the Genie your goals, preferences, and constraints.</li>
            <li><strong>Equipment</strong> — Add what you can train with, from bodyweight to gear.</li>
            <li><strong>Pantry</strong> — List staples you have so meals fit your kitchen.</li>
            <li><strong>Schedule</strong> — Set days/times so plans respect your routine.</li>
            <li><strong>Weekly Plan</strong> — Generate your plan, then use <em>Today</em> to follow along.</li>
        </ol>
        <p style='color:#b8c0cc; margin: 0.75rem 0 0.5rem;'>Pro tip: Snap a <strong>gym photo</strong> or a <strong>grocery bill/pantry photo</strong> and let the AI <em>auto‑detect</em> equipment and pantry items to prefill your lists—an easy way to kickstart setup.</p>
        <p style='color:#8b95a5; margin:0;'>You can update any of these anytime—FitDietGenie adapts your plan automatically.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
