import streamlit as st
from pathlib import Path

THEME_PATH = Path(__file__).parent / "static" / "theme.css"

def _inject_theme():
    try:
        css = THEME_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def apply_global_ui():
    """Call at the top of EVERY page before drawing content."""
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
    # Hard-disable the Streamlit sidebar so only our top bar is visible
    st.markdown("""
    <style>
      [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display:none !important; }
      [data-testid="stAppViewContainer"] > .main { margin-left:0 !important; }
    </style>
    """, unsafe_allow_html=True)
    _inject_theme()

def show_next_step_button(current_page: str):
    """Shows the next step button based on the current page."""
    # Define the flow sequence with page numbers and names
    flow = {
        "onboarding": ("Equipment Setup", "pages/02_equipment.py"),
        "equipment": ("Pantry Setup", "pages/03_pantry.py"),
        "pantry": ("Schedule Setup", "pages/04_schedule.py"),
        "schedule": ("Weekly Plan", "pages/05_weekly_plan.py"),
        "weekly_plan": ("Today's Plan", "pages/06_today.py"),
        "today": ("Progress Tracking", "pages/07_progress.py")
    }
    
    if current_page in flow:
        next_title, next_page = flow[current_page]
        
        # Add separator and section title
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <h4>🎯 Next Step</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Create a centered container for the button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            # Simple direct navigation
            if st.button(f"Continue to {next_title} →", 
                        type="primary",
                        width="stretch"):
                st.switch_page(next_page)

def top_nav(is_authed: bool = False, on_sign_out=None, current: str = ""):
    """
    Simple horizontal navigation using buttons.
    """
    # Add custom CSS for navigation styling
    st.markdown("""
    <style>
    .stButton button {
        background-color: transparent !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        color: #ffffff !important;
        font-size: 0.9rem !important;
    }
    .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 4px !important;
    }
    div[data-testid="stToolbar"] {
        visibility: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

    items = [
        ("Home", "app.py"),
        ("Profile", "pages/01_onboarding.py"),
        ("Equipment", "pages/02_equipment.py"),
        ("Plan", "pages/05_weekly_plan.py"),
        ("Today", "pages/06_today.py"),
        ("Settings", "pages/08_settings.py"),
    ]

    # Create a single row of navigation
    st.markdown('<div style="background: rgba(15,17,23,.95); padding: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,.1);">', unsafe_allow_html=True)
    
    cols = st.columns(len(items) + (1 if is_authed else 0))
    
    for (label, path), col in zip(items, cols):
        with col:
            if st.button(label, key=f"nav_{path}"):
                st.switch_page(path)
    
    # Add sign out button if authenticated
    if is_authed and len(cols) > len(items):
        with cols[-1]:
            if st.button("Sign Out"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)