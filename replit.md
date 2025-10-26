# FitLife Planner

## Overview

FitLife Planner is an AI-powered fitness and lifestyle planning application that generates personalized weekly workout and meal plans based on user constraints, preferences, and available resources. The application adapts dynamically to user adherence, pantry availability, recovery metrics, and schedule changes. It leverages Google's Gemini 2.0 Flash to create contextual, constraint-aware plans that respect equipment limitations, dietary restrictions, and time availability.

The system collects user data through a structured onboarding flow, tracks daily adherence with subjective metrics (RPE, soreness), and triggers adaptive re-planning when conditions warrant intervention.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
**Technology**: Streamlit  
**Design Pattern**: Multi-page application with session-based state management  
**Rationale**: Streamlit provides rapid development of interactive data applications with minimal frontend code. The multi-page structure (`pages/` directory) organizes distinct user journeys (onboarding, equipment setup, pantry management, schedule configuration, plan generation, daily tracking, progress visualization, settings).

**Key Design Decisions**:
- **Session State**: User identity (`user_id`, `email`, `timezone`) persists across page navigation via `st.session_state`
- **Page Flow**: Linear onboarding required before plan generation (questionnaire → equipment → pantry → schedule → weekly plan)
- **Validation**: Pages check for prerequisite data and block access with warnings if dependencies are missing
- **Temporary State**: Form inputs stored in session state before database commits to enable multi-step editing

### Backend Architecture
**Technology**: SQLAlchemy ORM with PostgreSQL (via DATABASE_URL environment variable)  
**Design Pattern**: Repository pattern with session-based database access  
**Rationale**: SQLAlchemy provides database-agnostic ORM capabilities while maintaining type safety and relationship management. The `SessionLocal` factory pattern ensures proper connection lifecycle management.

**Data Model**:
- **Profile**: Central user entity (user_id, email, timezone)
- **Questionnaire**: User bio, goals, dietary preferences, allergens, work hours, gym/grocery frequency
- **Equipment**: Available workout equipment (JSON array)
- **Pantry**: Current food inventory with shopping schedule (items, last/next shopping dates)
- **Availability**: Free time blocks per week (day, start time, end time)
- **WeeklyPlan**: Generated workout/meal plan (week_start_date, plan_json containing 7 days)
- **AdherenceLog**: Daily tracking (date, workout_done, RPE, soreness, meals_done, notes)
- **Reminder**: Scheduled notifications (not fully implemented in provided code)

**Relationships**: One-to-one for questionnaire/equipment/pantry/availability, one-to-many for plans/logs/reminders

### AI Planning System
**Technology**: Google Gemini 2.0 Flash  
**Design Pattern**: Schema-driven prompt engineering with strict I/O contracts  
**Rationale**: LLM generates holistic weekly plans that fuse multiple constraint dimensions (time, equipment, pantry, goals, recovery needs) which would be complex to hard-code algorithmically.

**Input Contract (`INPUT_CONTRACT_V1`)**:
- User profile data
- Questionnaire responses
- Equipment list
- Pantry inventory with quantities
- Available time blocks
- Week start date and timezone

**Output Contract (`WEEKLY_PLAN_V1`)**:
- 7-day array with structured daily data:
  - **Workout**: start time, duration, location (home/gym), exercise blocks (name, sets, reps, rest), intensity notes, fallback alternatives
  - **Meals**: breakfast, lunch, dinner, snacks (each with ingredients from pantry, recipe, macros)
  - **Recovery**: hydration target, sleep recommendation, stretching/foam rolling guidance
- Plan summary and justification

**Validation**: JSON schemas enforce strict structure; invalid outputs trigger self-correction loops

### Adaptive Logic System
**Module**: `adaptive_logic.py`  
**Design Pattern**: Rule-based trigger system with LLM-powered re-planning  
**Rationale**: Static plans become obsolete when conditions change. The system monitors adherence logs and pantry status to detect when intervention is needed.

**Adaptation Triggers**:
1. **High Soreness**: ≥2 recent logs with soreness ≥8/10 → reduce intensity
2. **High RPE**: ≥2 recent logs with RPE ≥9/10 → potential overtraining, deload recommended
3. **Pantry Depletion**: (Implied by `auto_replan_after_pantry_update` function) → regenerate meals with current inventory

**Process**:
1. Query recent adherence logs (last 3 entries in current week)
2. Evaluate trigger conditions
3. If triggered, call `adapt_plan()` with adherence data and current plan
4. LLM generates modified plan preserving structure but adjusting intensity/volume/meals
5. Store adapted plan as new `WeeklyPlan` record

### Data Persistence
**Database**: PostgreSQL (assumed from DATABASE_URL pattern)  
**Schema Management**: SQLAlchemy declarative models with automatic table creation via `init_db()`  
**Data Types**:
- **JSON columns**: Flexible storage for questionnaire responses, equipment lists, pantry items, availability blocks, full plan structures
- **Date/DateTime**: Temporal tracking for plans (week_start_date), logs (date), shopping schedules
- **Foreign Keys**: Enforce referential integrity between profiles and dependent entities

**Pros**: JSON columns provide schema flexibility for evolving data structures; relational foreign keys ensure data consistency  
**Cons**: JSON queries less performant than normalized columns; requires application-level validation

### Authentication & User Management
**Current Implementation**: Demo mode with hardcoded user (`demo_user`, `demo@example.com`)  
**Planned Integration**: Supabase auth (mentioned in requirements but not implemented in provided code)  
**Profile Management**: `get_or_create_profile()` ensures user record exists on app initialization

## External Dependencies

### AI Services
- **OpenAI API** (GPT-4.1): Weekly plan generation and adaptive re-planning
  - Environment variable: `OPENAI_API_KEY`
  - Client library: `openai` Python SDK
  - Usage: Structured JSON outputs with schema validation

### Database
- **PostgreSQL**: Primary data store
  - Connection: `DATABASE_URL` environment variable
  - ORM: SQLAlchemy 2.x
  - Tables: profiles, questionnaire, equipment, pantry, availability, weekly_plans, adherence_logs, reminders

### Notification Services (Planned)
- **SendGrid**: Email notifications for daily reminders
- **Twilio**: SMS notifications for workout/meal reminders
- **Implementation Status**: Schema includes `Reminder` table; actual integration not present in provided code

### Calendar Integration (Planned)
- **Google Calendar / Microsoft Calendar**: Automatic availability import
- **Implementation Status**: Manual time block entry currently required

### Python Dependencies
- **streamlit**: Web UI framework
- **sqlalchemy**: Database ORM
- **openai**: LLM API client
- **pandas**: Data manipulation for progress visualization
- **plotly**: Interactive charts for adherence tracking
- **jsonschema**: Contract validation for LLM outputs

### Infrastructure
- **Deployment Target**: Replit (inferred from repl context)
- **Environment Management**: OS environment variables for secrets (API keys, database URL)
- **Session Management**: Streamlit session state (in-memory, non-persistent)