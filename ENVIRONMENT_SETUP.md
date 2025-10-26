# Environment Setup for Gemini Integration

## Required Environment Variables

The application now uses Google Gemini 2.0 Flash instead of OpenAI GPT. You need to set up the following environment variable:

### Google AI API Key
```bash
export GOOGLE_API_KEY="your_google_ai_api_key_here"
```

Or create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_ai_api_key_here
```

## Getting a Google AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key and set it as the `GOOGLE_API_KEY` environment variable

## Installation

Install the new dependencies:
```bash
pip install -r requirements.txt
```

Or if using uv:
```bash
uv sync
```

## Changes Made

- Replaced OpenAI GPT-4.1 with Google Gemini 2.0 Flash
- Updated all model calls to use the Gemini API
- Modified dependencies in `requirements.txt` and `pyproject.toml`
- Updated documentation to reflect the model change

The application functionality remains the same, but now uses Google's Gemini model for generating fitness and meal plans.
