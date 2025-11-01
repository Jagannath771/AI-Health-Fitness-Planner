import json
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import jsonschema
import requests
import base64

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it to your Google AI API key.")

def analyze_grocery_receipt(image_bytes):
    """Analyze grocery receipt image using Google Cloud Vision API"""
    # Convert the image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Prepare the request
    url = 'https://vision.googleapis.com/v1/images:annotate'
    headers = {
        'x-goog-api-key': GOOGLE_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'requests': [{
            'image': {
                'content': base64_image
            },
            'features': [{
                'type': 'TEXT_DETECTION',
                'maxResults': 50
            }]
        }]
    }
    
    # Make the request
    response = requests.post(url, headers=headers, json=payload)
    if not response.ok:
        raise Exception(f"Error calling Vision API: {response.text}")
    
    result = response.json()
    
    if 'responses' not in result or not result['responses'] or 'fullTextAnnotation' not in result['responses'][0]:
        return []
    
    # Process the detected text
    full_text = result['responses'][0]['fullTextAnnotation']['text']
    items = []
    
    # Split text into lines and process each line
    for line in full_text.split('\n'):
        # Basic filtering for likely product lines (contains numbers, etc.)
        if any(c.isdigit() for c in line):
            # Extract quantity and name using some basic heuristics
            parts = line.split()
            if len(parts) >= 2:
                try:
                    # Try to find number-like parts
                    qty = next((p for p in parts if any(c.isdigit() for c in p)), "1")
                    # Remove the quantity part and join the rest as the name
                    name = " ".join(p for p in parts if p != qty)
                    items.append({"name": name.strip(), "qty_unit": qty.strip()})
                except:
                    continue
    
    return items

def analyze_gym_equipment(image_bytes):
    """Analyze gym equipment image using Google Cloud Vision API"""
    # Convert the image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Prepare the request for both object detection and label detection
    url = 'https://vision.googleapis.com/v1/images:annotate'
    headers = {
        'x-goog-api-key': GOOGLE_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'requests': [{
            'image': {
                'content': base64_image
            },
            'features': [
                {
                    'type': 'OBJECT_LOCALIZATION',
                    'maxResults': 50
                },
                {
                    'type': 'LABEL_DETECTION',
                    'maxResults': 50
                }
            ]
        }]
    }
    
    # Make the request
    response = requests.post(url, headers=headers, json=payload)
    if not response.ok:
        raise Exception(f"Error calling Vision API: {response.text}")
    
    result = response.json()
    
    if 'responses' not in result or not result['responses']:
        return []
    
    response = result['responses'][0]
    detected_equipment = set()  # Use set to avoid duplicates

    # Common gym equipment keywords and mappings
    gym_equipment_keywords = {
        # Strength Training
        'dumbbell': 'Dumbbells',
        'barbell': 'Barbell',
        'weight': 'Free Weights',
        'kettlebell': 'Kettlebells',
        'plate': 'Weight Plates',
        'rack': 'Equipment Rack',
        'bench': 'Exercise Bench',
        'smith machine': 'Smith Machine',
        'cable': 'Cable Machine',
        
        # Cardio Equipment
        'treadmill': 'Treadmill',
        'bicycle': 'Stationary Bike',
        'bike': 'Stationary Bike',
        'elliptical': 'Elliptical Machine',
        'rowing': 'Rowing Machine',
        'rower': 'Rowing Machine',
        'stair': 'Stair Climber',
        
        # Functional Training
        'mat': 'Yoga Mat',
        'foam roller': 'Foam Roller',
        'resistance band': 'Resistance Bands',
        'ball': 'Exercise Ball',
        'medicine ball': 'Medicine Ball',
        'boxing': 'Boxing Equipment',
        'trx': 'TRX Suspension',
        'pull-up bar': 'Pull-up Bar',
        'pullup bar': 'Pull-up Bar',
        
        # Generic Terms
        'gym': 'Exercise Equipment',
        'fitness': 'Exercise Equipment',
        'exercise': 'Exercise Equipment',
        'sports equipment': 'Exercise Equipment',
        'machine': 'Exercise Machine'
    }

    # Process object detection results
    if 'localizedObjectAnnotations' in response:
        for obj in response['localizedObjectAnnotations']:
            name = obj['name'].lower()
            # Check if the object name matches any of our equipment keywords
            for keyword, equipment in gym_equipment_keywords.items():
                if keyword in name:
                    detected_equipment.add(equipment)
                    break

    # Process label detection results
    if 'labelAnnotations' in response:
        for label in response['labelAnnotations']:
            description = label['description'].lower()
            # Only consider labels with confidence above 0.5
            if label['score'] >= 0.5:
                # Check if the label matches any of our equipment keywords
                for keyword, equipment in gym_equipment_keywords.items():
                    if keyword in description:
                        detected_equipment.add(equipment)
                        break
    
    # Special case: If we detect general gym/fitness equipment but no specifics
    if len(detected_equipment) <= 1 and 'Exercise Equipment' in detected_equipment:
        # Try to look for specific equipment in the raw text
        if 'textAnnotations' in response and response['textAnnotations']:
            full_text = response['textAnnotations'][0]['description'].lower()
            for keyword, equipment in gym_equipment_keywords.items():
                if keyword in full_text and equipment != 'Exercise Equipment':
                    detected_equipment.add(equipment)

    return list(detected_equipment)

genai.configure(api_key=GOOGLE_API_KEY)

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


def clean_json_response(response_text):
    """Clean markdown formatting from API response text"""
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]  # Remove ```json
    if response_text.startswith("```"):
        response_text = response_text[3:]  # Remove ```
    if response_text.endswith("```"):
        response_text = response_text[:-3]  # Remove trailing ```
    return response_text.strip()


def transform_api_response(plan):
    """Transform API response to match our expected schema"""
    # Handle nested structure
    if "weekly_plan" in plan:
        plan = plan["weekly_plan"]
    
    # Fix field name mapping
    if "start_date" in plan and "week_start" not in plan:
        plan["week_start"] = plan["start_date"]
    
    # Transform days structure
    if "days" in plan:
        for i, day in enumerate(plan["days"]):
            # Fix date field - convert day name to actual date or add missing date
            if "date" not in day:
                if "day" in day:
                    # Calculate the actual date based on week_start and day index
                    try:
                        week_start_str = plan.get("week_start", "2025-10-20")
                        week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
                        day_date = week_start + timedelta(days=i)
                        day["date"] = day_date.strftime("%Y-%m-%d")
                    except Exception as e:
                        # Fallback to a default date
                        print(f"Date calculation error: {e}")
                        day["date"] = f"2025-10-{20 + i}"
                else:
                    # No day field either, create a default date
                    try:
                        week_start_str = plan.get("week_start", "2025-10-20")
                        week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
                        day_date = week_start + timedelta(days=i)
                        day["date"] = day_date.strftime("%Y-%m-%d")
                    except:
                        day["date"] = f"2025-10-{20 + i}"
            
            # Transform workout structure
            if "workouts" in day:  # Handle case where API returns array of workouts
                # Take the first workout if multiple are provided
                workout = day["workouts"][0] if isinstance(day["workouts"], list) and len(day["workouts"]) > 0 else {
                    "start": "18:00",
                    "duration_min": 60,
                    "location": "home",
                    "blocks": [],
                    "intensity_note": "Rest day",
                    "fallbacks": []
                }
                day["workout"] = workout
                del day["workouts"]
            elif "workout" not in day:  # Create default workout if none exists
                day["workout"] = {
                    "start": "18:00",
                    "duration_min": 60,
                    "location": "home",
                    "blocks": [],
                    "intensity_note": "Rest day",
                    "fallbacks": []
                }
            
            workout = day["workout"]
            # Convert exercises to blocks format
            if "exercises" in workout and "blocks" not in workout:
                blocks = []
                for exercise in workout["exercises"]:
                    block = {
                        "name": exercise["name"],
                        "sets": exercise.get("sets", 3),
                        "reps": str(exercise.get("reps", "10")),
                        "rest_sec": exercise.get("rest_sec", 60)
                    }
                    blocks.append(block)
                workout["blocks"] = blocks
                
                # Ensure blocks have correct data types
                if "blocks" in workout:
                    for block in workout["blocks"]:
                        if "reps" in block and not isinstance(block["reps"], str):
                            block["reps"] = str(block["reps"])
                        if "sets" in block and not isinstance(block["sets"], int):
                            try:
                                block["sets"] = int(block["sets"])
                            except:
                                block["sets"] = 3  # Default
                        if "rest_sec" in block and not isinstance(block["rest_sec"], int):
                            try:
                                block["rest_sec"] = int(block["rest_sec"])
                            except:
                                block["rest_sec"] = 60  # Default
                
                # Add missing required fields and ensure correct types
                if "start" not in workout:
                    workout["start"] = "18:00"  # Default time
                if "duration_min" not in workout:
                    workout["duration_min"] = 60  # Default duration
                elif not isinstance(workout["duration_min"], int):
                    try:
                        workout["duration_min"] = int(workout["duration_min"])
                    except:
                        workout["duration_min"] = 60
                if "intensity_note" not in workout:
                    workout["intensity_note"] = "Moderate intensity"
                elif not isinstance(workout["intensity_note"], str):
                    workout["intensity_note"] = str(workout["intensity_note"])
                if "location" not in workout:
                    workout["location"] = "home"  # Default location
                elif not isinstance(workout["location"], str):
                    workout["location"] = str(workout["location"]).lower()
                if "blocks" not in workout:
                    workout["blocks"] = []  # Default empty blocks for rest day
                # Ensure fallbacks is always a properly formatted array of strings
                if "fallbacks" not in workout:
                    workout["fallbacks"] = []
                elif isinstance(workout["fallbacks"], str):
                    # Split string by commas or convert single string to array
                    if "," in workout["fallbacks"]:
                        workout["fallbacks"] = [s.strip() for s in workout["fallbacks"].split(",")]
                    else:
                        workout["fallbacks"] = [workout["fallbacks"]]
                elif isinstance(workout["fallbacks"], list):
                    # Ensure all items in the array are strings
                    workout["fallbacks"] = [str(item) for item in workout["fallbacks"]]
                else:
                    # Convert any other type to a string and wrap in array
                    workout["fallbacks"] = [str(workout["fallbacks"])]
            
            # Transform meals structure
            if "meals" in day:
                for meal in day["meals"]:
                    # Convert ingredients from objects to strings
                    if "ingredients" in meal:
                        ingredients = meal["ingredients"]
                        if isinstance(ingredients, list) and len(ingredients) > 0:
                            if isinstance(ingredients[0], dict):
                                # Convert from object format to string format
                                ingredient_strings = []
                                for ing in ingredients:
                                    if "name" in ing:
                                        qty = ing.get("qty", "1")
                                        unit = ing.get("unit", "")
                                        if unit:
                                            ingredient_strings.append(f"{ing['name']} ({qty} {unit})")
                                        else:
                                            ingredient_strings.append(ing['name'])
                                meal["ingredients"] = ingredient_strings
                    
                    # Add missing required fields
                    if "time" not in meal:
                        meal["time"] = "Breakfast"  # Default time
                    if "macro_note" not in meal:
                        meal["macro_note"] = "Balanced macros"
                    
                    # Ensure ingredients is always an array
                    if "ingredients" not in meal:
                        meal["ingredients"] = []
                    elif isinstance(meal["ingredients"], str):
                        meal["ingredients"] = [meal["ingredients"]]
                    elif not isinstance(meal["ingredients"], list):
                        meal["ingredients"] = []
            
            # Transform recovery structure
            if "recovery" in day:
                recovery = day["recovery"]
                if "sleep_hours" in recovery and "sleep_target_hr" not in recovery:
                    recovery["sleep_target_hr"] = recovery["sleep_hours"]
                if "hydration_liters" in recovery and "hydration_l" not in recovery:
                    recovery["hydration_l"] = recovery["hydration_liters"]
                if "mobility_min" not in recovery:
                    recovery["mobility_min"] = 10  # Default mobility time
                
                # Ensure correct data types for recovery fields
                if "sleep_target_hr" in recovery and not isinstance(recovery["sleep_target_hr"], (int, float)):
                    try:
                        recovery["sleep_target_hr"] = float(recovery["sleep_target_hr"])
                    except:
                        recovery["sleep_target_hr"] = 8.0
                if "mobility_min" in recovery and not isinstance(recovery["mobility_min"], int):
                    try:
                        recovery["mobility_min"] = int(recovery["mobility_min"])
                    except:
                        recovery["mobility_min"] = 10
                if "hydration_l" in recovery and not isinstance(recovery["hydration_l"], (int, float)):
                    try:
                        recovery["hydration_l"] = float(recovery["hydration_l"])
                    except:
                        recovery["hydration_l"] = 3.0
    
    # Transform summary structure
    if "summary" not in plan:
        plan["summary"] = {}
    
    summary = plan["summary"]
    if "grocery_gap" not in summary:
        summary["grocery_gap"] = []
    elif isinstance(summary["grocery_gap"], str):
        summary["grocery_gap"] = [summary["grocery_gap"]]
    elif not isinstance(summary["grocery_gap"], list):
        summary["grocery_gap"] = []
    
    if "total_training_min" not in summary:
        # Calculate total training time
        total_min = 0
        if "days" in plan:
            for day in plan["days"]:
                if "workout" in day and "duration_min" in day["workout"]:
                    total_min += day["workout"]["duration_min"]
        summary["total_training_min"] = total_min
    elif not isinstance(summary["total_training_min"], int):
        try:
            summary["total_training_min"] = int(summary["total_training_min"])
        except:
            summary["total_training_min"] = 0
    
    if "notes" not in summary:
        summary["notes"] = "Generated weekly plan"
    elif not isinstance(summary["notes"], str):
        summary["notes"] = str(summary["notes"])
    
    # Add justification if missing
    if "justification" not in plan:
        plan["justification"] = "AI-generated personalized fitness and nutrition plan based on your profile and preferences."
    
    return plan


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
1. Return ONLY valid JSON - no markdown formatting, no code blocks, no explanations
2. The JSON must have this EXACT structure at the root level:
   {{
     "week_start": "YYYY-MM-DD",
     "days": [...],
     "summary": {{...}},
     "justification": "..."
   }}
3. Only use equipment from the provided list: {equipment.get('items', [])}
4. Only use ingredients from pantry: {pantry.get('items', [])}
5. Respect dietary restrictions: {questionnaire.get('diet_json', {})}
6. Avoid allergens: {questionnaire.get('allergens_json', [])}
7. Respect injuries/limitations: {questionnaire.get('bio_json', {}).get('injuries', [])}
8. Gym access pattern: {gym_frequency}
   - If "weekends_only": gym workouts Saturday-Sunday, home workouts Monday-Friday
   - If "daily": gym workouts available any day based on schedule
   - If "never": all workouts must be at-home with available equipment only
9. Grocery shopping frequency: {grocery_frequency}
   - Plan meals using pantry items prioritizing freshness
   - Generate grocery gap list for items needed until next shopping day
10. Free time blocks: {availability.get('free_blocks', [])}
11. User goals: {questionnaire.get('goals_json', {})}
12. Cuisine preferences: {questionnaire.get('cuisine_json', {})}

WORKOUT STRUCTURE:
Each workout must have: start, duration_min, location, blocks, intensity_note, fallbacks
Each block must have: name, sets, reps, rest_sec

MEAL STRUCTURE:
Each meal must have: time, name, ingredients (array of strings), macro_note
Optional: recipe_steps (array of strings)

RECOVERY STRUCTURE:
Each recovery must have: sleep_target_hr, mobility_min, hydration_l

SUMMARY STRUCTURE:
Must have: grocery_gap (array of strings), total_training_min (integer), notes (string)

IMPORTANT: Return ONLY the JSON object with the exact structure above. Do not wrap in any container object."""

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

Return ONLY the JSON object following weekly_plan_v1 schema with all 7 days populated. No markdown formatting."""

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=8192,
                temperature=0.7
            )
        )
        
        # Check if response is empty or None
        if not response or not response.text:
            return {"status": "ERROR", "message": "Empty response from Google Gemini API. Please check your API key and try again."}
        
        # Log the raw response for debugging
        print(f"Raw API response: {response.text[:500]}...")  # First 500 chars for debugging
        
        # Clean the response text - remove markdown code blocks if present
        response_text = clean_json_response(response.text)
        
        try:
            plan = json.loads(response_text)
        except json.JSONDecodeError as e:
            return {"status": "ERROR", "message": f"Invalid JSON response from API: {str(e)}. Raw response: {response_text[:200]}..."}
        
        # Transform the API response to match our schema
        print(f"Before transformation - plan keys: {list(plan.keys())}")
        if "days" in plan:
            print(f"First day keys: {list(plan['days'][0].keys()) if plan['days'] else 'No days'}")
        
        plan = transform_api_response(plan)
        
        print(f"After transformation - plan keys: {list(plan.keys())}")
        if "days" in plan:
            print(f"First day keys: {list(plan['days'][0].keys()) if plan['days'] else 'No days'}")
        
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
        model = genai.GenerativeModel('gemini-pro')
        
        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4096,
                temperature=0.7
            )
        )
        
        # Clean the response text - remove markdown code blocks if present
        response_text = clean_json_response(response.text)
        
        return json.loads(response_text)
    
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
        model = genai.GenerativeModel('gemini-pro')
        
        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4096,
                temperature=0.7
            )
        )
        
        # Clean the response text - remove markdown code blocks if present
        response_text = clean_json_response(response.text)
        
        return json.loads(response_text)
    
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to regenerate day: {str(e)}"}
