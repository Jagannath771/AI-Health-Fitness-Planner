# FitnessLife Setup Guide

## Quick Fix for "Generate Weekly Plan" Error

The error you're seeing ("Expecting value: line 1 column 1 (char 0)") is caused by a missing Google AI API key. Here's how to fix it:

## Step 1: Get a Google AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key" or "Create API Key"
4. Copy the generated API key

## Step 2: Set Up Environment Variables

### Option A: Create a .env file (Recommended)
Create a file named `.env` in the `FitnessLife` folder with this content:

```
GOOGLE_API_KEY=your_actual_api_key_here
DATABASE_URL=your_database_url_here
```

### Option B: Set Environment Variables
If you're running from command line:

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY="your_actual_api_key_here"
$env:DATABASE_URL="your_database_url_here"
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_API_KEY=your_actual_api_key_here
set DATABASE_URL=your_database_url_here
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="your_actual_api_key_here"
export DATABASE_URL="your_database_url_here"
```

## Step 3: Install Dependencies

Make sure you have all required packages installed:

```bash
pip install -r requirements.txt
```

Or if using uv:
```bash
uv sync
```

## Step 4: Run the Application

```bash
streamlit run app.py
```

## Troubleshooting

### If you still get errors:

1. **Check the Debug Information**: Click the "🔍 Debug Information" expander in the error message to see what data is being sent to the API.

2. **Verify API Key**: Make sure your Google AI API key is valid and has the necessary permissions.

3. **Check Database Connection**: Ensure your `DATABASE_URL` is correct and the database is accessible.

4. **Check Console Output**: Look for any error messages in the terminal/console where you're running the app.

## What Was Fixed

- Added proper error handling for missing API keys
- Improved error messages to show exactly what went wrong
- Added debugging information to help troubleshoot issues
- Added validation to ensure the API key is set before making requests
- **Fixed JSON parsing error**: The Google Gemini API was returning JSON wrapped in markdown code blocks (```json ... ```), which caused parsing errors. This has been fixed by automatically cleaning the response.
- **Fixed schema validation error**: The API was returning data in a different structure than expected (nested under "weekly_plan" with different field names). Added automatic transformation to convert the API response to match our expected schema.
- **Fixed date field error**: The API was returning "day" field (like "Sunday") instead of "date" field (like "2025-10-26"). Added automatic conversion to calculate proper dates based on the week start date.
- **Fixed array type errors**: The API was returning some fields as strings instead of arrays (like fallbacks, ingredients, grocery_gap). Added automatic conversion to ensure all array fields are properly formatted.
- **Fixed data type errors**: The API was returning some fields with incorrect data types (like reps as integers instead of strings, duration_min as strings instead of integers). Added comprehensive type validation and conversion to ensure all fields match the expected schema types.

The application should now work properly once you set up the Google AI API key!
