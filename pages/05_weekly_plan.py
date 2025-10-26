import streamlit as st
from database import SessionLocal, Questionnaire, Equipment, Pantry, Availability, WeeklyPlan
from openai_service import generate_weekly_plan
from datetime import date, timedelta
import json

st.title("📊 Weekly Plan")
st.markdown("Generate your AI-powered weekly workout and meal plan.")

db = SessionLocal()

questionnaire = db.query(Questionnaire).filter(
    Questionnaire.user_id == st.session_state.user_id
).first()

equipment = db.query(Equipment).filter(
    Equipment.user_id == st.session_state.user_id
).first()

pantry = db.query(Pantry).filter(
    Pantry.user_id == st.session_state.user_id
).first()

availability = db.query(Availability).filter(
    Availability.user_id == st.session_state.user_id
).first()

if not questionnaire:
    st.warning("⚠️ Please complete the **Onboarding** first!")
    db.close()
    st.stop()

if not equipment:
    st.warning("⚠️ Please add your **Equipment** first!")
    db.close()
    st.stop()

if not pantry:
    st.warning("⚠️ Please set up your **Pantry** first!")
    db.close()
    st.stop()

if not availability:
    st.warning("⚠️ Please define your **Schedule** first!")
    db.close()
    st.stop()

st.subheader("Plan Configuration")
col1, col2 = st.columns(2)
with col1:
    week_start = st.date_input(
        "Week Start Date",
        value=date.today() - timedelta(days=date.today().weekday())
    )

with col2:
    st.info(f"🏋️ Gym Access: **{questionnaire.gym_frequency}**")
    st.info(f"🛒 Grocery Frequency: **{questionnaire.grocery_frequency}**")

if st.button("🤖 Generate Weekly Plan", type="primary", use_container_width=True):
    with st.spinner("🔮 AI is crafting your personalized plan..."):
        input_data = {
            "user": {
                "id": st.session_state.user_id,
                "email": st.session_state.email
            },
            "questionnaire": {
                "bio_json": questionnaire.bio_json,
                "goals_json": questionnaire.goals_json,
                "diet_json": questionnaire.diet_json,
                "allergens_json": questionnaire.allergens_json,
                "cuisine_json": questionnaire.cuisine_json,
                "work_hours_json": questionnaire.work_hours_json,
                "gym_frequency": questionnaire.gym_frequency,
                "grocery_frequency": questionnaire.grocery_frequency,
                "reminder_prefs_json": questionnaire.reminder_prefs_json
            },
            "equipment": equipment.items_json,
            "pantry": pantry.items_json,
            "availability": availability.free_blocks_json,
            "week_start": str(week_start),
            "timezone": st.session_state.timezone
        }
        
        plan = generate_weekly_plan(input_data)
        
        if "status" in plan and plan["status"] == "INFO_NEEDED":
            st.error(f"❌ Missing information: {plan['message']}")
            st.json(plan)
        elif "status" in plan and plan["status"] == "ERROR":
            st.error(f"❌ Error: {plan['message']}")
        else:
            new_plan = WeeklyPlan(
                user_id=st.session_state.user_id,
                week_start_date=week_start,
                plan_json=plan
            )
            db.add(new_plan)
            db.commit()
            
            st.session_state.current_plan = plan
            st.success("✅ Weekly plan generated successfully!")
            st.balloons()

st.markdown("---")

existing_plans = db.query(WeeklyPlan).filter(
    WeeklyPlan.user_id == st.session_state.user_id
).order_by(WeeklyPlan.created_at.desc()).all()

if existing_plans:
    st.subheader("📅 Your Plans")
    
    plan_options = [f"Week of {p.week_start_date} (created {p.created_at.strftime('%Y-%m-%d %H:%M')})" for p in existing_plans]
    selected_plan_idx = st.selectbox("Select a plan to view", range(len(plan_options)), format_func=lambda x: plan_options[x])
    
    if selected_plan_idx is not None:
        selected_plan = existing_plans[selected_plan_idx]
        plan_data = selected_plan.plan_json
        
        st.markdown(f"### Week Starting: {selected_plan.week_start_date}")
        st.markdown(f"**Justification:** {plan_data.get('justification', 'N/A')}")
        
        summary = plan_data.get("summary", {})
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Training Time", f"{summary.get('total_training_min', 0)} min")
        with col2:
            grocery_gap = summary.get('grocery_gap', [])
            st.metric("Grocery Items Needed", len(grocery_gap))
        
        if grocery_gap:
            with st.expander("🛒 Grocery Gap List"):
                for item in grocery_gap:
                    st.write(f"• {item}")
        
        if summary.get('notes'):
            st.info(f"📝 **Notes:** {summary['notes']}")
        
        st.markdown("---")
        
        days = plan_data.get("days", [])
        for day_idx, day in enumerate(days):
            day_date = day.get("date", "Unknown")
            
            with st.expander(f"**Day {day_idx + 1}: {day_date}**", expanded=(day_idx == 0)):
                workout = day.get("workout", {})
                meals = day.get("meals", [])
                recovery = day.get("recovery", {})
                
                st.markdown("#### 🏋️ Workout")
                location = workout.get("location", "home")
                st.write(f"**Location:** {location.upper()} {'🏢' if location == 'gym' else '🏠'}")
                st.write(f"**Time:** {workout.get('start', 'N/A')} ({workout.get('duration_min', 0)} min)")
                st.write(f"**Intensity:** {workout.get('intensity_note', 'N/A')}")
                
                blocks = workout.get("blocks", [])
                if blocks:
                    st.markdown("**Exercises:**")
                    for block in blocks:
                        st.write(f"• {block['name']}: {block['sets']} sets × {block['reps']} reps (Rest: {block['rest_sec']}s)")
                
                fallbacks = workout.get("fallbacks", [])
                if fallbacks:
                    st.caption(f"*Fallbacks: {', '.join(fallbacks)}*")
                
                st.markdown("#### 🍽️ Meals")
                for meal_idx, meal in enumerate(meals):
                    st.write(f"**{meal.get('time', 'N/A')} - {meal.get('name', 'Meal')}**")
                    st.write(f"*Macros: {meal.get('macro_note', 'N/A')}*")
                    
                    ingredients = meal.get("ingredients", [])
                    st.caption(f"Ingredients: {', '.join(ingredients)}")
                    
                    recipe_steps = meal.get("recipe_steps", [])
                    if recipe_steps:
                        with st.expander(f"Recipe for {meal.get('name', 'meal')}"):
                            for step_idx, step in enumerate(recipe_steps):
                                st.write(f"{step_idx + 1}. {step}")
                
                st.markdown("#### 😴 Recovery")
                st.write(f"• Sleep Target: {recovery.get('sleep_target_hr', 'N/A')} hours")
                st.write(f"• Mobility: {recovery.get('mobility_min', 0)} minutes")
                st.write(f"• Hydration: {recovery.get('hydration_l', 'N/A')} liters")

else:
    st.info("No plans generated yet. Click 'Generate Weekly Plan' to create your first plan!")

db.close()
