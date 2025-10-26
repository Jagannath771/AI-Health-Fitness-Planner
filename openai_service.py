import json
import os
from openai import OpenAI
from datetime import datetime, timedelta
import jsonschema

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

INPUT_CONTRACT_V1 = {
    "type": "object",
    "required": ["user", "questionnaire", "equipment", "pantry", "availability", "week_start", "timezone"],
    "properties": {
        "user": {"type": "object", "required": ["id", "email"], "properties": {"id": {"type": "string"}, "email": {"type": "string"}}},
        "questionnaire": {"type": "object"},
        "equipment": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "string"}}}},
        "pantry": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "required": ["name", "qty_unit"], "properties": {"name": {"type": "string"}, "qty_unit": {"type": "string"}}}}}},
        "availability": {"type": "object", "properties": {"free_blocks": {"type": "array", "items": {"type": "object", "required": ["day", "start", "end"], "properties": {"day": {"type": "string"}, "start": {"type": "string"}, "end": {"type": "string"}}}}}},
        "week_start": {"type": "string"},
        "timezone": {"type": "string"}
    }
}

WEEKLY_PLAN_V1 = {
    "type": "object",
    "required": ["week_start", "days", "summary", "justification"],
    "properties": {
        "week_start": {"type": "string"},
        "days": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {
                "type": "object",
                "required": ["date", "workout", "meals", "recovery"],
                "properties": {
                    "date": {"type": "string"},
                    "workout": {
                        "type": "object",
                        "required": ["start", "duration_min", "blocks", "intensity_note", "fallbacks", "location"],
                        "properties": {
                            "start": {"type": "string"},
                            "duration_min": {"type": "integer"},
                            "location": {"type": "string"},
                            "blocks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "sets", "reps", "rest_sec"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "sets": {"type": "integer"},
                                        "reps": {"type": "string"},
                                        "rest_sec": {"type": "integer"}
                                    }
                                }
                            },
                            "intensity_note": {"type": "string"},
                            "fallbacks": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "meals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["time", "name", "ingredients", "macro_note"],
                            "properties": {
                                "time": {"type": "string"},
                                "name": {"type": "string"},
                                "ingredients": {"type": "array", "items": {"type": "string"}},
                                "macro_note": {"type": "string"},
                                "recipe_steps": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "recovery": {
                        "type": "object",
                        "properties": {
                            "sleep_target_hr": {"type": "number"},
                            "mobility_min": {"type": "integer"},
                            "hydration_l": {"type": "number"}
                        }
                    }
                }
            }
        },
        "summary": {
            "type": "object",
            "properties": {
                "grocery_gap": {"type": "array", "items": {"type": "string"}},
                "total_training_min": {"type": "integer"},
                "notes": {"type": "string"}
            }
        },
        "justification": {"type": "string"}
    }
}


def validate_input(input_data):
    try:
        jsonschema.validate(instance=input_data, schema=INPUT_CONTRACT_V1)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        missing_fields = []
        if e.validator == 'required':
            missing_fields = e.message.split("'")
        return False, {"status": "INFO_NEEDED", "missing_fields": missing_fields, "message": str(e)}


def generate_weekly_plan(input_data):
    is_valid, error = validate_input(input_data)
    if not is_valid:
        return error
    
    questionnaire = input_data.get("questionnaire", {})
    equipment = input_data.get("equipment", {})
    pantry = input_data.get("pantry", {})
    availability = input_data.get("availability", {})
    week_start = input_data.get("week_start")
    timezone = input_data.get("timezone")
    
    gym_frequency = questionnaire.get("gym_frequency", "never")
    grocery_frequency = questionnaire.get("grocery_frequency", "weekly")
    
    system_prompt = f"""You are a fitness and nutrition planning expert. Generate a 7-day weekly plan with workouts and meals.

CRITICAL REQUIREMENTS:
1. Validate all outputs against the JSON schema. Return valid JSON only.
2. Only use equipment from the provided list: {equipment.get('items', [])}
3. Only use ingredients from pantry: {pantry.get('items', [])}
4. Respect dietary restrictions: {questionnaire.get('diet_json', {})}
5. Avoid allergens: {questionnaire.get('allergens_json', [])}
6. Respect injuries/limitations: {questionnaire.get('bio_json', {}).get('injuries', [])}
7. Gym access pattern: {gym_frequency}
   - If "weekends_only": gym workouts Saturday-Sunday, home workouts Monday-Friday
   - If "daily": gym workouts available any day based on schedule
   - If "never": all workouts must be at-home with available equipment only
8. Grocery shopping frequency: {grocery_frequency}
   - Plan meals using pantry items prioritizing freshness
   - Generate grocery gap list for items needed until next shopping day
9. Free time blocks: {availability.get('free_blocks', [])}
10. User goals: {questionnaire.get('goals_json', {})}
11. Cuisine preferences: {questionnaire.get('cuisine_json', {})}

WORKOUT LOCATION LOGIC:
- On gym-access days: suggest gym-based exercises if user has gym access
- On non-gym days: suggest at-home calisthenics/bodyweight using available equipment
- Each workout must include "location" field: "gym" or "home"

MEAL PLANNING LOGIC:
- Use pantry items first, especially perishables
- Only add to grocery_gap if truly needed and not in pantry
- Account for {grocery_frequency} shopping pattern

Return JSON matching weekly_plan_v1 schema with 7 days, workouts with location, meals, recovery targets."""

    user_prompt = f"""Generate a weekly plan starting {week_start} for timezone {timezone}.

User profile:
- Bio: {questionnaire.get('bio_json', {})}
- Goals: {questionnaire.get('goals_json', {})}
- Diet: {questionnaire.get('diet_json', {})}
- Allergens: {questionnaire.get('allergens_json', [])}
- Gym frequency: {gym_frequency}
- Grocery frequency: {grocery_frequency}

Equipment: {equipment.get('items', [])}
Pantry: {json.dumps(pantry.get('items', []), indent=2)}
Free blocks: {availability.get('free_blocks', [])}

Return valid JSON following weekly_plan_v1 schema with all 7 days populated."""

    try:
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=8192
        )
        
        plan = json.loads(response.choices[0].message.content)
        
        try:
            jsonschema.validate(instance=plan, schema=WEEKLY_PLAN_V1)
        except jsonschema.exceptions.ValidationError as e:
            return {"status": "ERROR", "message": f"Generated plan invalid: {str(e)}"}
        
        return plan
    
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to generate plan: {str(e)}"}


def adapt_plan(current_plan, adherence_logs, pantry_delta=None, schedule_delta=None):
    system_prompt = """You are adapting an existing weekly plan based on user adherence and changes.

ADAPTATION RULES:
1. If soreness > 7 or RPE consistently > 8: reduce next workout intensity by 20%, swap HIIT for LISS
2. If pantry items depleted: swap recipes with available pantry alternatives maintaining macros
3. If schedule changed: reschedule workouts to new free blocks
4. Maintain weekly training volume when possible
5. Return JSON with days_patch array and reason

Return format:
{
  "days_patch": [
    {
      "date": "2025-01-15",
      "workout_delta": {"intensity_note": "Reduced due to high soreness"},
      "meals_delta": {"meal_0": {"ingredients": ["new", "items"]}}
    }
  ],
  "reason": "Brief explanation"
}"""

    user_prompt = f"""Current plan summary: {json.dumps(current_plan.get('summary', {}), indent=2)}

Recent adherence: {json.dumps(adherence_logs, indent=2)}
Pantry changes: {json.dumps(pantry_delta, indent=2) if pantry_delta else 'None'}
Schedule changes: {json.dumps(schedule_delta, indent=2) if schedule_delta else 'None'}

Adapt the plan for remaining days."""

    try:
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=4096
        )
        
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to adapt plan: {str(e)}"}


def regenerate_day(input_data, target_date, reason=""):
    system_prompt = f"""Generate a single day's workout and meals.

Follow same constraints as weekly plan generation.
Reason for regeneration: {reason}

Return JSON matching single day from weekly_plan_v1 schema."""

    user_prompt = f"""Regenerate plan for date {target_date}.

Context: {json.dumps(input_data, indent=2)}"""

    try:
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=4096
        )
        
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to regenerate day: {str(e)}"}
