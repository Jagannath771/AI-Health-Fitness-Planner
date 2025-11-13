import streamlit as st
from database import SessionLocal, Questionnaire
from datetime import time
import json

st.title("📋 Onboarding")
st.markdown("Tell us about yourself to get personalized fitness and meal plans.")

db = SessionLocal()

existing = db.query(Questionnaire).filter(
    Questionnaire.user_id == st.session_state.user_id
).first()

if existing:
    st.success("✅ Profile already exists! Update below if needed.")
    default_bio = existing.bio_json
    default_goals = existing.goals_json
    default_diet = existing.diet_json
    default_allergens = existing.allergens_json
    default_cuisine = existing.cuisine_json
    default_work = existing.work_hours_json
    default_gym = existing.gym_frequency
    default_grocery = existing.grocery_frequency
    default_reminder = existing.reminder_prefs_json
else:
    default_bio = {}
    default_goals = {}
    default_diet = {}
    default_allergens = []
    default_cuisine = {}
    default_work = {}
    default_gym = "never"
    default_grocery = "weekly"
    default_reminder = {"time": "06:00", "channels": []}

st.subheader("👤 Bio Information")
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", min_value=10, max_value=100, value=default_bio.get("age", 30))
    height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=default_bio.get("height_cm", 170))
    weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=200, value=default_bio.get("weight_kg", 70))

with col2:
    sex = st.selectbox("Sex", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(default_bio.get("sex", "Male")))
    activity_level = st.selectbox(
        "Activity Level",
        ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
        index=["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"].index(default_bio.get("activity_level", "Moderately Active"))
    )

injuries = st.text_area(
    "Injuries or Physical Limitations (comma-separated)",
    value=", ".join(default_bio.get("injuries", []))
)

st.subheader("🎯 Goals")
col1, col2 = st.columns(2)
with col1:
    weight_goal = st.selectbox(
        "Weight Goal",
        ["Maintain", "Lose Weight", "Gain Weight"],
        index=["Maintain", "Lose Weight", "Gain Weight"].index(default_goals.get("weight_goal", "Maintain"))
    )
    muscle_goal = st.selectbox(
        "Muscle Goal",
        ["Maintain", "Build Muscle", "Tone"],
        index=["Maintain", "Build Muscle", "Tone"].index(default_goals.get("muscle_goal", "Maintain"))
    )

with col2:
    cardio_goal = st.selectbox(
        "Cardio Goal",
        ["Maintain", "Improve VO2 Max", "General Fitness"],
        index=["Maintain", "Improve VO2 Max", "General Fitness"].index(default_goals.get("cardio_goal", "Maintain"))
    )

st.subheader("🍽️ Diet & Nutrition")
col1, col2 = st.columns(2)
with col1:
    diet_type = st.selectbox(
        "Diet Type",
        ["Omnivore", "Vegetarian", "Vegan", "Pescatarian"],
        index=["Omnivore", "Vegetarian", "Vegan", "Pescatarian"].index(default_diet.get("type", "Omnivore"))
    )

with col2:
    allergens_input = st.text_area(
        "Allergens (comma-separated)",
        value=", ".join(default_allergens) if default_allergens else ""
    )

cuisine_prefs = st.text_area(
    "Cuisine Preferences (comma-separated, e.g., Italian, Indian, Mexican)",
    value=", ".join(default_cuisine.get("preferences", []))
)

budget_sensitivity = st.select_slider(
    "Budget Sensitivity",
    options=["Low", "Medium", "High"],
    value=default_cuisine.get("budget_sensitivity", "Medium")
)

st.subheader("🏋️ Gym Access & Shopping Patterns")
col1, col2 = st.columns(2)
with col1:
    gym_frequency = st.selectbox(
        "How often do you have gym access?",
        ["never", "weekends_only", "daily"],
        index=["never", "weekends_only", "daily"].index(default_gym),
        help="This determines when you'll get gym-based vs at-home workouts"
    )
    st.caption("• **never**: All workouts will be at-home")
    st.caption("• **weekends_only**: Gym workouts Sat-Sun, home workouts Mon-Fri")
    st.caption("• **daily**: Gym workouts can be scheduled any day")

with col2:
    grocery_frequency = st.selectbox(
        "How often do you buy groceries?",
        ["daily", "2-3x_weekly", "weekly"],
        index=["daily", "2-3x_weekly", "weekly"].index(default_grocery),
        help="This helps plan meals and manage your pantry"
    )
    st.caption("• **daily**: Fresh meal plans daily")
    st.caption("• **2-3x weekly**: Meal plans account for mid-week restocking")
    st.caption("• **weekly**: Full week planned with one shopping trip")

st.subheader("⏰ Work Schedule & Timezone")
col1, col2 = st.columns(2)
with col1:
    start_default = default_work.get("start", "09:00")
    if isinstance(start_default, str):
        try:
            start_h, start_m = map(int, start_default.split(":"))
            start_default = time(start_h, start_m)
        except (ValueError, TypeError):
            start_default = time(9, 0)  # fallback to 9:00 AM
    elif not isinstance(start_default, time):
        start_default = time(9, 0)  # fallback to 9:00 AM
    work_start = st.time_input("Work Start Time", value=start_default)
    
    end_default = default_work.get("end", "17:00")
    if isinstance(end_default, str):
        try:
            end_h, end_m = map(int, end_default.split(":"))
            end_default = time(end_h, end_m)
        except (ValueError, TypeError):
            end_default = time(17, 0)  # fallback to 5:00 PM
    elif not isinstance(end_default, time):
        end_default = time(17, 0)  # fallback to 5:00 PM
    work_end = st.time_input("Work End Time", value=end_default)

with col2:
    timezone = st.selectbox(
        "Timezone",
        ["UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", 
         "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai"],
        index=0 if not hasattr(st.session_state, 'timezone') else 0
    )
    st.session_state.timezone = timezone

st.subheader("🔔 Reminder Preferences")
reminder_default = default_reminder.get("time", "06:00")
if isinstance(reminder_default, str):
    try:
        parts = reminder_default.split(":")
        rem_h, rem_m = map(int, parts[:2])  # Take only the first two parts
        reminder_default = time(rem_h, rem_m)
    except (ValueError, IndexError):
        # If there's any error, fallback to 6:00 AM
        reminder_default = time(6, 0)
reminder_time = st.time_input(
    "Daily Reminder Time",
    value=reminder_default
)
reminder_channels = st.multiselect(
    "Reminder Channels (future feature)",
    ["Email", "SMS"],
    default=default_reminder.get("channels", [])
)

if st.button("💾 Save Profile", type="primary", width="stretch"):
    bio_json = {
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "sex": sex,
        "activity_level": activity_level,
        "injuries": [i.strip() for i in injuries.split(",") if i.strip()]
    }
    
    goals_json = {
        "weight_goal": weight_goal,
        "muscle_goal": muscle_goal,
        "cardio_goal": cardio_goal
    }
    
    diet_json = {
        "type": diet_type
    }
    
    allergens_json = [a.strip() for a in allergens_input.split(",") if a.strip()]
    
    cuisine_json = {
        "preferences": [c.strip() for c in cuisine_prefs.split(",") if c.strip()],
        "budget_sensitivity": budget_sensitivity
    }
    
    work_hours_json = {
        "start": str(work_start),
        "end": str(work_end)
    }
    
    reminder_prefs_json = {
        "time": str(reminder_time),
        "channels": reminder_channels
    }
    
    if existing:
        existing.bio_json = bio_json
        existing.goals_json = goals_json
        existing.diet_json = diet_json
        existing.allergens_json = allergens_json
        existing.cuisine_json = cuisine_json
        existing.work_hours_json = work_hours_json
        existing.gym_frequency = gym_frequency
        existing.grocery_frequency = grocery_frequency
        existing.reminder_prefs_json = reminder_prefs_json
    else:
        new_q = Questionnaire(
            user_id=st.session_state.user_id,
            bio_json=bio_json,
            goals_json=goals_json,
            diet_json=diet_json,
            allergens_json=allergens_json,
            cuisine_json=cuisine_json,
            work_hours_json=work_hours_json,
            gym_frequency=gym_frequency,
            grocery_frequency=grocery_frequency,
            reminder_prefs_json=reminder_prefs_json
        )
        db.add(new_q)
    
    db.commit()
    st.success("✅ Profile saved successfully!")
    st.balloons()
    
    # Add navigation section with proper spacing
    st.write("")  # Add some space
    st.markdown("""
    <div style='background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0;'>
        <h3 style='margin-bottom: 1rem;'>🎯 Next Step: Equipment Setup</h3>
        <p style='color: #b8c0cc; margin-bottom: 1rem;'>Add your available workout equipment</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Continue to Equipment →", type="primary", width="stretch"):
            import streamlit as st
            st.switch_page("pages/02_equipment.py")

db.close()
