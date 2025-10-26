from database import SessionLocal, AdherenceLog, WeeklyPlan, Pantry
from openai_service import adapt_plan
from datetime import date, timedelta
import json


def check_and_adapt_plan(user_id):
    db = SessionLocal()
    
    try:
        current_week_start = date.today() - timedelta(days=date.today().weekday())
        
        plan = db.query(WeeklyPlan).filter(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start_date == current_week_start
        ).order_by(WeeklyPlan.created_at.desc()).first()
        
        if not plan:
            return None, "No current week plan found"
        
        recent_logs = db.query(AdherenceLog).filter(
            AdherenceLog.user_id == user_id,
            AdherenceLog.date >= current_week_start
        ).order_by(AdherenceLog.date.desc()).limit(3).all()
        
        needs_adaptation = False
        adaptation_reasons = []
        
        high_soreness_count = sum(1 for log in recent_logs if log.soreness and log.soreness >= 8)
        if high_soreness_count >= 2:
            needs_adaptation = True
            adaptation_reasons.append("High soreness detected in recent workouts")
        
        high_rpe_count = sum(1 for log in recent_logs if log.rpe and log.rpe >= 9)
        if high_rpe_count >= 2:
            needs_adaptation = True
            adaptation_reasons.append("Consistently high RPE indicating potential overtraining")
        
        if needs_adaptation:
            adherence_data = [
                {
                    "date": str(log.date),
                    "workout_done": log.workout_done,
                    "rpe": log.rpe,
                    "soreness": log.soreness,
                    "meals_done": log.meals_done
                }
                for log in recent_logs
            ]
            
            adapted = adapt_plan(
                current_plan=plan.plan_json,
                adherence_logs=adherence_data
            )
            
            return adapted, adaptation_reasons
        
        return None, "No adaptation needed"
    
    finally:
        db.close()


def check_pantry_depletion(user_id):
    db = SessionLocal()
    
    try:
        pantry = db.query(Pantry).filter(
            Pantry.user_id == user_id
        ).first()
        
        if not pantry:
            return None, []
        
        current_items = pantry.items_json.get("items", [])
        item_names = [item["name"].lower() for item in current_items]
        
        current_week_start = date.today() - timedelta(days=date.today().weekday())
        
        plan = db.query(WeeklyPlan).filter(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start_date == current_week_start
        ).order_by(WeeklyPlan.created_at.desc()).first()
        
        if not plan:
            return None, []
        
        missing_ingredients = []
        plan_data = plan.plan_json
        
        for day in plan_data.get("days", []):
            day_date = date.fromisoformat(day.get("date"))
            if day_date < date.today():
                continue
            
            for meal in day.get("meals", []):
                for ingredient in meal.get("ingredients", []):
                    ingredient_lower = ingredient.lower()
                    found = any(ingredient_lower in item_name or item_name in ingredient_lower 
                              for item_name in item_names)
                    if not found and ingredient not in missing_ingredients:
                        missing_ingredients.append(ingredient)
        
        return pantry, missing_ingredients
    
    finally:
        db.close()


def suggest_meal_swap(missing_ingredient, available_items, meal_context):
    import google.generativeai as genai
    import os
    
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)
    
    system_prompt = """You are a nutrition expert. Suggest a recipe swap that uses available pantry items 
    while maintaining similar macros and meal type (breakfast/lunch/dinner)."""
    
    user_prompt = f"""Missing ingredient: {missing_ingredient}
Available items: {', '.join([item['name'] for item in available_items])}
Original meal context: {meal_context}

Suggest a suitable replacement ingredient or alternative meal using available items."""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.7
            )
        )
        
        # Clean the response text - remove markdown code blocks if present
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        response_text = response_text.strip()
        
        return json.loads(response_text)
    
    except Exception as e:
        return {"error": str(e)}


def auto_replan_after_pantry_update(user_id):
    db = SessionLocal()
    
    try:
        current_week_start = date.today() - timedelta(days=date.today().weekday())
        
        plan = db.query(WeeklyPlan).filter(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.week_start_date == current_week_start
        ).order_by(WeeklyPlan.created_at.desc()).first()
        
        if not plan:
            return None, "No current plan"
        
        pantry = db.query(Pantry).filter(
            Pantry.user_id == user_id
        ).first()
        
        if not pantry:
            return None, "No pantry data"
        
        days_until_next_shopping = (pantry.next_shopping_date - date.today()).days
        
        if days_until_next_shopping <= 0:
            return None, "Shopping day has passed"
        
        pantry_delta = {
            "items": pantry.items_json.get("items", []),
            "days_until_shopping": days_until_next_shopping
        }
        
        adapted = adapt_plan(
            current_plan=plan.plan_json,
            adherence_logs=[],
            pantry_delta=pantry_delta
        )
        
        return adapted, f"Replanned meals for next {days_until_next_shopping} days based on updated pantry"
    
    finally:
        db.close()
