import json
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import jsonschema
import requests
import base64
import logging

# Configure basic logging (optional enhancement for debugging)
logging.basicConfig(level=logging.INFO)

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
    
    items = set()
    
    # Process object detection results
    localized_objects = result['responses'][0].get('localizedObjectAnnotations', [])
    for obj in localized_objects:
        name = obj.get('name', '').lower()
        if any(keyword in name for keyword in ['dumbbell', 'weight', 'bench', 'mat', 'ball', 'rack', 'machine']):
            items.add(name)
    
    # Process label detection results
    labels = result['responses'][0].get('labelAnnotations', [])
    for label in labels:
        name = label.get('description', '').lower()
        if any(keyword in name for keyword in ['dumbbell', 'weight', 'bench', 'mat', 'ball', 'rack', 'machine', 'gym']):
            items.add(name)
    
    return list(items)

def setup_genai():
    """Configure the Google GenerativeAI client and return a usable model with fallback logic.

    Order of precedence:
    1. Explicit env var GEMINI_MODEL
    2. Known stable models list fallback
    Returns (model, chosen_model_name)
    """
    genai.configure(api_key=GOOGLE_API_KEY)

    generation_config = {
        "temperature": 0.6,  # slightly lower for more deterministic JSON
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,  # larger plans sometimes exceed 3k tokens
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    # Current Google Gemini model names (2025) — gemini-pro deprecated in favor of versioned names
    preferred = os.environ.get("GEMINI_MODEL")
    strict = os.environ.get("GEMINI_STRICT") in ["1", "true", "True"]

    if strict and preferred:
        # Only attempt the preferred model and raise if it fails
        try:
            model = genai.GenerativeModel(
                model_name=preferred,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            logging.info(f"Using STRICT Gemini model: {preferred}")
            return model, preferred
        except Exception as e:
            raise RuntimeError(f"Strict model '{preferred}' initialization failed: {e}")

    # Try experimental 2.0 flash first if available, then 1.5 variants, then legacy
    fallback_models = [m for m in [
        preferred,
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro"
    ] if m]

    last_err = None
    for name in fallback_models:
        try:
            model = genai.GenerativeModel(
                model_name=name,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
            logging.info(f"Using Gemini model: {name}")
            return model, name
        except Exception as e:
            logging.warning(f"Failed to init model '{name}': {e}")
            last_err = e

    # If no model succeeded, raise the last error for upstream handling
    raise RuntimeError(f"Unable to initialize any Gemini model. Last error: {last_err}")

# ====== Legacy/Expanded Schema & Transformation Utilities (from prior implementation) ======
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

def clean_json_response(response_text: str) -> str:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return response_text.strip()

def transform_api_response(plan: dict) -> dict:
    # Unwrap nested key if present
    if "weekly_plan" in plan:
        plan = plan["weekly_plan"]

    if "start_date" in plan and "week_start" not in plan:
        plan["week_start"] = plan["start_date"]

    if "days" in plan:
        for i, day in enumerate(plan["days"]):
            # Ensure date exists
            if "date" not in day:
                try:
                    ws = plan.get("week_start") or datetime.utcnow().strftime("%Y-%m-%d")
                    base = datetime.strptime(ws, "%Y-%m-%d")
                    day["date"] = (base + timedelta(days=i)).strftime("%Y-%m-%d")
                except Exception:
                    day["date"] = datetime.utcnow().strftime("%Y-%m-%d")

            # Normalize workout
            if "workouts" in day and "workout" not in day:
                wk = day["workouts"][0] if isinstance(day["workouts"], list) and day["workouts"] else {}
                day["workout"] = wk
                del day["workouts"]
            if "workout" not in day:
                day["workout"] = {
                    "start": "18:00",
                    "duration_min": 60,
                    "location": "home",
                    "blocks": [],
                    "intensity_note": "Rest day",
                    "fallbacks": []
                }
            wk = day["workout"]
            for fld, default in [
                ("start", "18:00"),
                ("duration_min", 60),
                ("location", "home"),
                ("blocks", []),
                ("intensity_note", "Moderate intensity"),
                ("fallbacks", [])
            ]:
                if fld not in wk:
                    wk[fld] = default
            # Normalize fallbacks
            if isinstance(wk.get("fallbacks"), str):
                fb = wk["fallbacks"]
                wk["fallbacks"] = [s.strip() for s in fb.split(",")] if "," in fb else [fb]
            elif not isinstance(wk.get("fallbacks"), list):
                wk["fallbacks"] = [str(wk["fallbacks"])]

            # Convert exercises -> blocks if needed
            if "exercises" in wk and not wk.get("blocks"):
                blocks = []
                for ex in wk["exercises"]:
                    blocks.append({
                        "name": ex.get("name", "Exercise"),
                        "sets": int(ex.get("sets", 3)) if str(ex.get("sets", "")).isdigit() else 3,
                        "reps": str(ex.get("reps", "10")),
                        "rest_sec": int(ex.get("rest_sec", 60)) if str(ex.get("rest_sec", "")).isdigit() else 60
                    })
                wk["blocks"] = blocks

            # Ensure blocks types
            for b in wk.get("blocks", []):
                if not isinstance(b.get("reps"), str):
                    b["reps"] = str(b.get("reps"))
                if not isinstance(b.get("sets"), int):
                    try:
                        b["sets"] = int(b.get("sets", 3))
                    except Exception:
                        b["sets"] = 3
                if not isinstance(b.get("rest_sec"), int):
                    try:
                        b["rest_sec"] = int(b.get("rest_sec", 60))
                    except Exception:
                        b["rest_sec"] = 60

            # Meals normalization
            for meal in day.get("meals", []):
                if "ingredients" in meal and meal["ingredients"] and isinstance(meal["ingredients"][0], dict):
                    ing_strings = []
                    for ing in meal["ingredients"]:
                        nm = ing.get("name")
                        qty = ing.get("qty") or ing.get("qty_unit") or "1"
                        unit = ing.get("unit", "")
                        if nm:
                            ing_strings.append(f"{nm} ({qty}{(' ' + unit) if unit else ''})".strip())
                    meal["ingredients"] = ing_strings
                if "ingredients" not in meal:
                    meal["ingredients"] = []
                elif isinstance(meal["ingredients"], str):
                    meal["ingredients"] = [meal["ingredients"]]
                if "time" not in meal:
                    meal["time"] = "Breakfast"
                if "macro_note" not in meal:
                    meal["macro_note"] = "Balanced macros"

            # Recovery normalization
            rec = day.get("recovery") or {}
            day["recovery"] = rec
            if "sleep_hours" in rec and "sleep_target_hr" not in rec:
                rec["sleep_target_hr"] = rec["sleep_hours"]
            if "hydration_liters" in rec and "hydration_l" not in rec:
                rec["hydration_l"] = rec["hydration_liters"]
            rec.setdefault("mobility_min", 10)
            # type coercion
            try:
                if "sleep_target_hr" in rec and not isinstance(rec["sleep_target_hr"], (int, float)):
                    rec["sleep_target_hr"] = float(rec["sleep_target_hr"])
            except Exception:
                rec["sleep_target_hr"] = 8.0
            try:
                if not isinstance(rec.get("mobility_min"), int):
                    rec["mobility_min"] = int(rec.get("mobility_min", 10))
            except Exception:
                rec["mobility_min"] = 10
            try:
                if "hydration_l" in rec and not isinstance(rec["hydration_l"], (int, float)):
                    rec["hydration_l"] = float(rec["hydration_l"])
            except Exception:
                rec["hydration_l"] = 3.0

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
        total = 0
        for d in plan.get("days", []):
            try:
                total += int(d.get("workout", {}).get("duration_min", 0))
            except Exception:
                pass
        summary["total_training_min"] = total
    else:
        try:
            summary["total_training_min"] = int(summary.get("total_training_min", 0))
        except Exception:
            summary["total_training_min"] = 0
    if "notes" not in summary:
        summary["notes"] = "Generated weekly plan"
    if "justification" not in plan:
        plan["justification"] = "AI-generated personalized fitness and nutrition plan based on your profile and preferences."
    return plan

def validate_input(input_data):
    """Primary validation using JSON Schema; returns (bool, error_dict_or_None)."""
    try:
        # Build an input wrapper to match schema requirement of 'user'
        jsonschema.validate(instance=input_data, schema=INPUT_CONTRACT_V1)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, {"status": "INFO_NEEDED", "message": str(e)}

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

    user_prompt = f"""Generate a weekly plan starting {week_start} for timezone {timezone}."""
    
    try:
        model, model_name = setup_genai()

        # Newer SDKs don't require explicit role structs for simple generation; keep system context concise.
        composite_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(composite_prompt)

        # Defensive extraction of text
        raw_text = None
        try:
            # Prefer aggregated text property if available
            raw_text = getattr(response, "text", None)
            if not raw_text and response.candidates and response.candidates[0].content.parts:
                # Fallback to first part text
                raw_text = response.candidates[0].content.parts[0].text
        except Exception:
            pass

        if not raw_text:
            return {
                "status": "ERROR",
                "message": "No response text generated",
                "model": model_name
            }

        # Attempt to isolate JSON if model added stray commentary
        cleaned = raw_text.strip()
        # If fenced code block exists, extract inside
        if cleaned.startswith("```"):
            # Remove triple backticks and possible language hint
            cleaned_lines = cleaned.splitlines()
            # Drop first and last fence line
            cleaned_core = [ln for ln in cleaned_lines[1:-1] if not ln.startswith("```")]
            cleaned = "\n".join(cleaned_core).strip()

        # Trim any leading non-json preamble
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1:
            candidate_json = cleaned[first_brace:last_brace+1]
        else:
            candidate_json = cleaned

        try:
            plan_json = json.loads(candidate_json)
        except json.JSONDecodeError as e:
            return {
                "status": "ERROR",
                "message": f"Invalid JSON response: {e}",
                "model": model_name,
                "raw_response": raw_text[:2000]  # truncate for safety
            }

        # Lightweight schema sanity (presence of required top-level keys)
        required_top = ["week_start", "days", "summary", "justification"]
        missing = [k for k in required_top if k not in plan_json]
        if missing:
            return {
                "status": "ERROR",
                "message": f"JSON missing required keys: {', '.join(missing)}",
                "model": model_name,
                "raw_response": raw_text[:2000]
            }

        # Transform & validate against extended schema for robustness
        transformed = transform_api_response(plan_json)
        try:
            jsonschema.validate(instance=transformed, schema=WEEKLY_PLAN_V1)
        except jsonschema.exceptions.ValidationError as e:
            return {
                "status": "ERROR",
                "message": f"Generated plan invalid schema: {e.message}",
                "model": model_name,
                "raw_response": raw_text[:1000]
            }
        return transformed

    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Error generating plan: {str(e)}",
            "model_attempt": os.environ.get("GEMINI_MODEL")
        }

def adapt_plan(current_plan, adherence_logs=None, pantry_delta=None):
    """
    Lightweight local adaptation function for weekly plans.
    - current_plan: dict (the plan JSON produced by generate_weekly_plan)
    - adherence_logs: list of dicts with keys: date, workout_done, rpe, soreness, meals_done
    - pantry_delta: optional dict with pantry info, e.g. {"items": [...], "days_until_shopping": N}

    Returns dict with keys:
    - status: "ADAPTED" or "NO_CHANGE" or "ERROR"
    - reason: human-readable reason
    - days_patch: list of { "date": "YYYY-MM-DD", "patch": {...} } (partial updates)
    - new_plan (optional): full updated plan (only included when convenient)
    """
    try:
        if adherence_logs is None:
            adherence_logs = []

        days_patch = []
        reason_parts = []

        # Simple rule: if many recent high soreness or high RPE -> reduce intensity/duration
        high_soreness_count = sum(1 for l in adherence_logs if l.get("soreness") and l.get("soreness") >= 8)
        high_rpe_count = sum(1 for l in adherence_logs if l.get("rpe") and l.get("rpe") >= 9)

        # Helper to reduce a workout block
        def reduce_workout_block(block):
            new_block = dict(block)
            # Reduce sets by 1 if >1, otherwise reduce reps by ~20%
            try:
                if isinstance(new_block.get("sets"), int) and new_block["sets"] > 1:
                    new_block["sets"] = max(1, new_block["sets"] - 1)
                else:
                    # try to reduce reps (could be "8-12" or int)
                    reps = new_block.get("reps")
                    if isinstance(reps, int):
                        new_block["reps"] = max(1, int(reps * 0.8))
                    elif isinstance(reps, str) and "-" in reps:
                        parts = reps.split("-")
                        try:
                            lo = int(parts[0])
                            hi = int(parts[1])
                            new_lo = max(1, int(lo * 0.8))
                            new_hi = max(new_lo, int(hi * 0.8))
                            new_block["reps"] = f"{new_lo}-{new_hi}"
                        except:
                            pass
                # Increase rest if present
                if isinstance(new_block.get("rest_sec"), int):
                    new_block["rest_sec"] = int(new_block["rest_sec"] * 1.25)
            except Exception:
                pass
            return new_block

        # If soreness or RPE flags: create patches for future days
        if high_soreness_count >= 2 or high_rpe_count >= 2:
            reason_parts.append("High recent soreness/RPE detected — reducing upcoming training load.")
            today = datetime.utcnow().date()
            for day in current_plan.get("days", []):
                # Patch only for days >= today
                try:
                    day_date = datetime.fromisoformat(day.get("date")).date()
                except Exception:
                    # if date parsing fails, skip
                    continue
                if day_date >= today:
                    patch = {}
                    workout = day.get("workout", {})
                    if workout:
                        new_workout = dict(workout)
                        # reduce total duration by ~25%
                        if isinstance(new_workout.get("duration_min"), int):
                            new_workout["duration_min"] = max(5, int(new_workout["duration_min"] * 0.75))
                        # reduce blocks
                        new_blocks = []
                        for b in new_workout.get("blocks", []):
                            new_blocks.append(reduce_workout_block(b))
                        new_workout["blocks"] = new_blocks
                        # add a recovery note/intensity change
                        new_workout["intensity_note"] = "Reduced intensity for recovery"
                        patch["workout"] = new_workout
                    if patch:
                        days_patch.append({
                            "date": day.get("date"),
                            "patch": patch
                        })

        # Pantry delta handling: try to detect missing ingredients and produce grocery_gap
        pantry_gaps = []
        if pantry_delta:
            pantry_items = [item.get("name", "").lower() for item in pantry_delta.get("items", [])]
            for day in current_plan.get("days", []):
                for meal in day.get("meals", []):
                    for ing in meal.get("ingredients", []):
                        if isinstance(ing, str):
                            ing_name = ing.lower()
                            # simple containment check
                            found = any(p in ing_name or ing_name in p for p in pantry_items)
                            if not found and ing not in pantry_gaps:
                                pantry_gaps.append(ing)
            if pantry_gaps:
                reason_parts.append("Pantry update indicates missing ingredients.")
                # Build a simple patch that adds grocery_gap to summary
                days_patch.append({
                    "date": None,
                    "patch": {
                        "summary_update": {
                            "grocery_gap": pantry_gaps
                        }
                    }
                })

        if not days_patch:
            return {"status": "NO_CHANGE", "reason": "No adaptation rules triggered", "days_patch": []}

        reason_text = " | ".join(reason_parts) if reason_parts else "Adaptation applied"
        # Optionally build a full new_plan by applying patches (lightweight)
        new_plan = dict(current_plan)
        if any(p.get("date") for p in days_patch):
            # apply only date-specific patches
            for dpatch in days_patch:
                d = dpatch.get("date")
                if not d:
                    continue
                for day in new_plan.get("days", []):
                    if day.get("date") == d:
                        day_patch = dpatch.get("patch", {})
                        # shallow-merge workout if present
                        if "workout" in day_patch:
                            day["workout"] = day_patch["workout"]
                        # could merge other parts as needed

        # If there was a summary update patch (grocery gaps), merge it
        for dpatch in days_patch:
            if dpatch.get("date") is None:
                s_upd = dpatch.get("patch", {}).get("summary_update")
                if s_upd:
                    if "summary" not in new_plan:
                        new_plan["summary"] = {}
                    new_plan["summary"].setdefault("grocery_gap", [])
                    # extend without duplicates
                    for it in s_upd.get("grocery_gap", []):
                        if it not in new_plan["summary"]["grocery_gap"]:
                            new_plan["summary"]["grocery_gap"].append(it)

        return {
            "status": "ADAPTED",
            "reason": reason_text,
            "days_patch": days_patch,
            "new_plan": new_plan
        }

    except Exception as e:
        return {"status": "ERROR", "reason": str(e), "days_patch": []}


def regenerate_day(input_data, target_date, reason=""):
    """Regenerate a single day using the same model selection + schema utilities."""
    # Provide a concise system prompt; reuse constraints for one day
    system_prompt = f"""You are a fitness and nutrition planning expert. Generate one day plan JSON only.
Constraints mirrored from weekly plan: valid JSON, fields: date, workout, meals, recovery.
Workout: start, duration_min, location, blocks[], intensity_note, fallbacks[].
Each block: name, sets, reps, rest_sec.
Meals: time, name, ingredients[], macro_note, optional recipe_steps[].
Recovery: sleep_target_hr, mobility_min, hydration_l.
Return ONLY JSON for a single day, no markdown.
"""

    user_prompt = f"Regenerate date {target_date} (reason: {reason}). Context: {json.dumps(input_data)[:1500]}"

    try:
        model, model_name = setup_genai()
        composite = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(composite)
        raw = getattr(response, "text", "") or ""
        cleaned = clean_json_response(raw)
        first = cleaned.find("{"); last = cleaned.rfind("}")
        if first != -1 and last != -1:
            cleaned = cleaned[first:last+1]
        try:
            day_json = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return {"status": "ERROR", "message": f"Invalid JSON day: {e}", "raw": raw[:800], "model": model_name}

        # Minimal normalization via transform_api_response expecting a full plan; wrap fake container
        wrapper = {"week_start": target_date, "days": [day_json], "summary": {"notes": "Temp"}, "justification": "Single day regen"}
        wrapper = transform_api_response(wrapper)
        try:
            # Validate that the single day now conforms
            jsonschema.validate(instance=wrapper, schema=WEEKLY_PLAN_V1)
        except jsonschema.exceptions.ValidationError as e:
            return {"status": "ERROR", "message": f"Day schema invalid: {e.message}", "model": model_name}
        return {"status": "OK", "day": wrapper["days"][0], "model": model_name}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}