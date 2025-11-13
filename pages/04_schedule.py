import streamlit as st
from database import SessionLocal, Availability
import json

st.title("📅 Schedule")
st.markdown("Define your free time blocks for workout scheduling.")

db = SessionLocal()

existing = db.query(Availability).filter(
    Availability.user_id == st.session_state.user_id
).first()

if "free_blocks" not in st.session_state:
    if existing:
        st.session_state.free_blocks = existing.free_blocks_json.get("free_blocks", [])
    else:
        st.session_state.free_blocks = []

st.subheader("Current Free Blocks")

if st.session_state.free_blocks:
    for idx, block in enumerate(st.session_state.free_blocks):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.text(f"{block['day']}")
        with col2:
            st.text(f"Start: {block['start']}")
        with col3:
            st.text(f"End: {block['end']}")
        with col4:
            if st.button("🗑️", key=f"delete_{idx}"):
                st.session_state.free_blocks.pop(idx)
                st.rerun()
else:
    st.info("No free blocks added yet. Add your first time block below!")

st.markdown("---")
st.subheader("Add Free Time Block")

days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
with col1:
    day = st.selectbox("Day", days_of_week, key="day_select")

with col2:
    start_time = st.time_input("Start Time", value=None, key="start_time")

with col3:
    end_time = st.time_input("End Time", value=None, key="end_time")

with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Block", width="stretch"):
        if start_time and end_time:
            new_block = {
                "day": day,
                "start": str(start_time),
                "end": str(end_time)
            }
            st.session_state.free_blocks.append(new_block)
            st.rerun()

st.markdown("---")
st.subheader("Quick Add Templates")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🌅 Morning Person (6-8 AM weekdays)", width="stretch"):
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            st.session_state.free_blocks.append({"day": day, "start": "06:00", "end": "08:00"})
        st.rerun()

with col2:
    if st.button("🌆 Evening Person (6-8 PM weekdays)", width="stretch"):
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            st.session_state.free_blocks.append({"day": day, "start": "18:00", "end": "20:00"})
        st.rerun()

with col3:
    if st.button("🎯 Weekend Warrior (Sat-Sun mornings)", width="stretch"):
        st.session_state.free_blocks.append({"day": "Saturday", "start": "08:00", "end": "12:00"})
        st.session_state.free_blocks.append({"day": "Sunday", "start": "08:00", "end": "12:00"})
        st.rerun()

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save Schedule", type="primary", width="stretch"):
        free_blocks_json = {"free_blocks": st.session_state.free_blocks}
        
        if existing:
            existing.free_blocks_json = free_blocks_json
        else:
            new_avail = Availability(
                user_id=st.session_state.user_id,
                free_blocks_json=free_blocks_json,
                calendar_connected=False
            )
            db.add(new_avail)
        
        db.commit()
        st.session_state.schedule_saved = True
        st.success("✅ Schedule saved successfully!")

with col2:
    if st.button("Continue to Weekly Plan →", type="primary", width="stretch", key="continue_plan"):
        st.switch_page("pages/05_weekly_plan.py")

# Add navigation section with proper spacing
st.write("")  # Add some space
st.markdown("""
<div style='background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0;'>
    <h3 style='margin-bottom: 1rem;'>🎯 Next Step: Weekly Plan</h3>
    <p style='color: #b8c0cc; margin-bottom: 1rem;'>Get your personalized fitness and nutrition plan</p>
</div>
""", unsafe_allow_html=True)

db.close()
