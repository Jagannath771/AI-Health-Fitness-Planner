import streamlit as st
from database import SessionLocal, Questionnaire, Equipment, Pantry, Availability
import json

st.title("⚙️ Settings")
st.markdown("Update your profile and preferences.")

db = SessionLocal()

tab1, tab2 = st.tabs(["Profile", "Data Management"])

with tab1:
    st.subheader("👤 Update Profile")
    
    questionnaire = db.query(Questionnaire).filter(
        Questionnaire.user_id == st.session_state.user_id
    ).first()
    
    if questionnaire:
        st.info("You can update your profile information below. Changes will affect future plan generations.")
        
        with st.expander("📋 Edit Questionnaire"):
            st.markdown("Go to the **Onboarding** page to edit your full profile.")
            st.caption(f"Current Gym Frequency: {questionnaire.gym_frequency}")
            st.caption(f"Current Grocery Frequency: {questionnaire.grocery_frequency}")
            st.caption(f"Diet Type: {questionnaire.diet_json.get('type', 'N/A')}")
        
        with st.expander("🏋️ Edit Equipment"):
            st.markdown("Go to the **Equipment** page to manage your equipment list.")
            equipment = db.query(Equipment).filter(Equipment.user_id == st.session_state.user_id).first()
            if equipment:
                items = equipment.items_json.get("items", [])
                st.caption(f"Current Items: {len(items)}")
                st.write(", ".join(items[:10]) + ("..." if len(items) > 10 else ""))
        
        with st.expander("🥗 Edit Pantry"):
            st.markdown("Go to the **Pantry** page to manage your pantry items.")
            pantry = db.query(Pantry).filter(Pantry.user_id == st.session_state.user_id).first()
            if pantry:
                items = pantry.items_json.get("items", [])
                st.caption(f"Current Items: {len(items)}")
                st.caption(f"Next Shopping: {pantry.next_shopping_date}")
        
        with st.expander("📅 Edit Schedule"):
            st.markdown("Go to the **Schedule** page to manage your free time blocks.")
            availability = db.query(Availability).filter(Availability.user_id == st.session_state.user_id).first()
            if availability:
                blocks = availability.free_blocks_json.get("free_blocks", [])
                st.caption(f"Current Free Blocks: {len(blocks)}")
    else:
        st.warning("⚠️ Please complete the **Onboarding** first!")

with tab2:
    st.subheader("🗄️ Data Management")
    
    st.warning("⚠️ **Danger Zone** - These actions cannot be undone!")
    
    with st.expander("🗑️ Clear All Data"):
        st.markdown("""
        This will delete all your data including:
        - Profile and questionnaire
        - Equipment and pantry lists
        - Schedule and free time blocks
        - All weekly plans
        - All adherence logs
        """)
        
        confirm_text = st.text_input("Type 'DELETE ALL' to confirm")
        
        if st.button("🗑️ Delete All My Data", type="secondary"):
            if confirm_text == "DELETE ALL":
                from database import Questionnaire, Equipment, Pantry, Availability, WeeklyPlan, AdherenceLog, Reminder
                
                db.query(Reminder).filter(Reminder.user_id == st.session_state.user_id).delete()
                db.query(AdherenceLog).filter(AdherenceLog.user_id == st.session_state.user_id).delete()
                db.query(WeeklyPlan).filter(WeeklyPlan.user_id == st.session_state.user_id).delete()
                db.query(Availability).filter(Availability.user_id == st.session_state.user_id).delete()
                db.query(Pantry).filter(Pantry.user_id == st.session_state.user_id).delete()
                db.query(Equipment).filter(Equipment.user_id == st.session_state.user_id).delete()
                db.query(Questionnaire).filter(Questionnaire.user_id == st.session_state.user_id).delete()
                
                db.commit()
                st.success("✅ All data deleted. Please refresh the page and start with Onboarding.")
            else:
                st.error("❌ Confirmation text doesn't match. Type 'DELETE ALL' exactly.")

st.markdown("---")
st.caption("FitLife Planner v1.0")
st.caption("Powered by OpenAI GPT-5")

db.close()
