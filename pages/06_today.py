import streamlit as st
from database import SessionLocal, WeeklyPlan, AdherenceLog
from datetime import date, timedelta
from adaptive_logic import check_and_adapt_plan
import json

st.title("📆 Today")
st.markdown(f"**{date.today().strftime('%A, %B %d, %Y')}**")

db = SessionLocal()

current_week_start = date.today() - timedelta(days=date.today().weekday())

plan = db.query(WeeklyPlan).filter(
    WeeklyPlan.user_id == st.session_state.user_id,
    WeeklyPlan.week_start_date <= date.today(),
    WeeklyPlan.week_start_date > date.today() - timedelta(days=7)
).order_by(WeeklyPlan.created_at.desc()).first()

if not plan:
    st.warning("⚠️ No plan for this week. Generate one in the **Weekly Plan** page!")
    db.close()
    st.stop()

plan_data = plan.plan_json
days = plan_data.get("days", [])

today_str = str(date.today())
today_data = None
for day in days:
    if day.get("date") == today_str:
        today_data = day
        break

if not today_data:
    st.info("No plan data for today.")
    db.close()
    st.stop()

workout = today_data.get("workout", {})
meals = today_data.get("meals", [])
recovery = today_data.get("recovery", {})

st.markdown("---")
st.subheader("🏋️ Today's Workout")

location = workout.get("location", "home")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Location", location.upper() + (" 🏢" if location == "gym" else " 🏠"))
with col2:
    st.metric("Time", workout.get("start", "N/A"))
with col3:
    st.metric("Duration", f"{workout.get('duration_min', 0)} min")

st.info(f"**Intensity:** {workout.get('intensity_note', 'N/A')}")

blocks = workout.get("blocks", [])
if blocks:
    st.markdown("**Exercises:**")
    for block in blocks:
        st.write(f"• **{block['name']}**: {block['sets']} sets × {block['reps']} reps (Rest: {block['rest_sec']}s)")

fallbacks = workout.get("fallbacks", [])
if fallbacks:
    with st.expander("Alternative Exercises"):
        for fb in fallbacks:
            st.write(f"• {fb}")

st.markdown("---")
st.subheader("🍽️ Today's Meals")

for meal_idx, meal in enumerate(meals):
    with st.expander(f"**{meal.get('time', 'N/A')} - {meal.get('name', 'Meal')}**", expanded=True):
        st.write(f"*Macros: {meal.get('macro_note', 'N/A')}*")
        
        ingredients = meal.get("ingredients", [])
        st.markdown("**Ingredients:**")
        for ing in ingredients:
            st.write(f"• {ing}")
        
        recipe_steps = meal.get("recipe_steps", [])
        if recipe_steps:
            st.markdown("**Recipe:**")
            for step_idx, step in enumerate(recipe_steps):
                st.write(f"{step_idx + 1}. {step}")

st.markdown("---")
st.subheader("😴 Recovery Goals")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Sleep Target", f"{recovery.get('sleep_target_hr', 'N/A')} hr")
with col2:
    st.metric("Mobility", f"{recovery.get('mobility_min', 0)} min")
with col3:
    st.metric("Hydration", f"{recovery.get('hydration_l', 'N/A')} L")

st.markdown("---")
st.subheader("📝 Log Today's Adherence")

existing_log = db.query(AdherenceLog).filter(
    AdherenceLog.user_id == st.session_state.user_id,
    AdherenceLog.date == date.today()
).first()

if existing_log:
    st.success("✅ You've already logged today!")
    default_workout_done = existing_log.workout_done
    default_rpe = existing_log.rpe or 5
    default_soreness = existing_log.soreness or 5
    default_meals_done = existing_log.meals_done or 0
    default_notes = existing_log.notes or ""
else:
    default_workout_done = False
    default_rpe = 5
    default_soreness = 5
    default_meals_done = 0
    default_notes = ""

col1, col2 = st.columns(2)
with col1:
    workout_done = st.checkbox("Workout Completed?", value=default_workout_done)
    rpe = st.slider("RPE (Rate of Perceived Exertion)", 1, 10, default_rpe, help="1=Very Easy, 10=Maximum Effort")

with col2:
    soreness = st.slider("Soreness Level", 1, 10, default_soreness, help="1=No Soreness, 10=Very Sore")
    meals_done = st.number_input("Meals Completed", 0, len(meals), default_meals_done)

notes = st.text_area("Notes (optional)", value=default_notes, placeholder="How did you feel? Any challenges?")

if st.button("💾 Save Adherence Log", type="primary", width="stretch"):
    if existing_log:
        existing_log.workout_done = workout_done
        existing_log.rpe = rpe
        existing_log.soreness = soreness
        existing_log.meals_done = meals_done
        existing_log.notes = notes
    else:
        new_log = AdherenceLog(
            user_id=st.session_state.user_id,
            date=date.today(),
            workout_done=workout_done,
            rpe=rpe,
            soreness=soreness,
            meals_done=meals_done,
            notes=notes
        )
        db.add(new_log)
    
    db.commit()
    st.success("✅ Adherence logged successfully!")
    
    if soreness >= 8:
        st.warning("⚠️ High soreness detected! Checking if plan adaptation is needed...")
        adapted, reasons = check_and_adapt_plan(st.session_state.user_id)
        if adapted and "days_patch" in adapted:
            st.info(f"🔄 Plan adapted: {adapted.get('reason', 'Adjusted for recovery')}")
    
    if rpe >= 9:
        st.info("💪 Great effort! Recovery is important - stay hydrated and rest well.")
        adapted, reasons = check_and_adapt_plan(st.session_state.user_id)
        if adapted and "days_patch" in adapted:
            st.info(f"🔄 Plan adapted: {adapted.get('reason', 'Intensity adjusted based on high effort')}")

db.close()