import streamlit as st
from database import SessionLocal, Equipment
from openai_service import analyze_gym_equipment
import json

st.title("🏋️ Equipment")
st.markdown("List all equipment you have access to at home or at the gym. Upload a photo of your gym to automatically detect equipment!")

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
st.subheader("Upload Gym Photo")
st.info("📸 Note: The automatic detection serves as a starting point and may not be 100% accurate. Feel free to add or remove items as needed!")
uploaded_file = st.file_uploader("Upload a photo of your gym to automatically detect equipment", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # Display the uploaded image
    st.image(uploaded_file, caption="Uploaded Gym Image", use_column_width=True)
    
    # Analyze the image when user clicks the button
    if st.button("🔍 Detect Equipment"):
        with st.spinner("Analyzing image..."):
            try:
                # Read the file
                bytes_data = uploaded_file.getvalue()
                # Analyze the image
                detected_items = analyze_gym_equipment(bytes_data)
                
                if detected_items:
                    st.success(f"✅ Detected {len(detected_items)} pieces of equipment!")
                    for item in detected_items:
                        if item not in st.session_state.equipment_items:
                            st.session_state.equipment_items.append(item)
                    st.rerun()
                else:
                    st.warning("No equipment detected in the image. Try uploading a clearer photo or add equipment manually.")
            except Exception as e:
                st.error(f"Error analyzing image: {str(e)}")

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

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save Equipment", type="primary", width="stretch"):
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
        st.session_state.equipment_saved = True
        st.success("✅ Equipment saved successfully!")

with col2:
    # Continue button
    if st.button("Continue to Pantry →", type="primary", width="stretch", key="continue_pantry"):
        st.switch_page("pages/03_pantry.py")

# Add navigation section with proper spacing
st.write("")  # Add some space
st.markdown("""
<div style='background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0;'>
    <h3 style='margin-bottom: 1rem;'>🎯 Next Step: Pantry Setup</h3>
    <p style='color: #b8c0cc; margin-bottom: 1rem;'>Add your available food items and groceries</p>
</div>
""", unsafe_allow_html=True)

db.close()
