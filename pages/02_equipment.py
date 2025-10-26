import streamlit as st
from database import SessionLocal, Equipment
import json

st.title("🏋️ Equipment")
st.markdown("List all equipment you have access to at home or at the gym.")

db = SessionLocal()

existing = db.query(Equipment).filter(
    Equipment.user_id == st.session_state.user_id
).first()

if "equipment_items" not in st.session_state:
    if existing:
        st.session_state.equipment_items = existing.items_json.get("items", [])
    else:
        st.session_state.equipment_items = []

st.subheader("Current Equipment")

if st.session_state.equipment_items:
    for idx, item in enumerate(st.session_state.equipment_items):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"• {item}")
        with col2:
            if st.button("🗑️", key=f"delete_{idx}"):
                st.session_state.equipment_items.pop(idx)
                st.rerun()
else:
    st.info("No equipment added yet. Add your first item below!")

st.markdown("---")
st.subheader("Add New Equipment")

common_equipment = [
    "Dumbbells",
    "Resistance Bands",
    "Pull-up Bar",
    "Yoga Mat",
    "Kettlebell",
    "Jump Rope",
    "Bench",
    "Barbell",
    "Squat Rack",
    "Treadmill",
    "Stationary Bike",
    "Foam Roller",
    "Medicine Ball",
    "TRX Straps",
    "Chair (for exercises)",
    "Floor Space"
]

col1, col2 = st.columns([3, 1])
with col1:
    selected_common = st.selectbox(
        "Select from common equipment",
        [""] + common_equipment,
        key="common_select"
    )

with col2:
    if st.button("➕ Add Selected") and selected_common:
        if selected_common not in st.session_state.equipment_items:
            st.session_state.equipment_items.append(selected_common)
            st.rerun()

st.markdown("**Or add custom equipment:**")
col1, col2 = st.columns([3, 1])
with col1:
    custom_item = st.text_input("Custom equipment name", key="custom_input")

with col2:
    if st.button("➕ Add Custom") and custom_item:
        if custom_item not in st.session_state.equipment_items:
            st.session_state.equipment_items.append(custom_item)
            st.rerun()

st.markdown("---")

if st.button("💾 Save Equipment", type="primary", use_container_width=True):
    items_json = {"items": st.session_state.equipment_items}
    
    if existing:
        existing.items_json = items_json
    else:
        new_eq = Equipment(
            user_id=st.session_state.user_id,
            items_json=items_json
        )
        db.add(new_eq)
    
    db.commit()
    st.success("✅ Equipment saved successfully!")
    st.info("👉 Next: Update your pantry in the **Pantry** page")

db.close()
