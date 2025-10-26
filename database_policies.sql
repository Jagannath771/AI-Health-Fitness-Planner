-- Row Level Security (RLS) Policies for FitLife Planner
-- Run this script in your Supabase SQL editor to enable RLS and add policies

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionnaire ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;
ALTER TABLE pantry ENABLE ROW LEVEL SECURITY;
ALTER TABLE availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE adherence_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for clean re-runs)
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;

DROP POLICY IF EXISTS "Users can view own questionnaire" ON questionnaire;
DROP POLICY IF EXISTS "Users can update own questionnaire" ON questionnaire;
DROP POLICY IF EXISTS "Users can insert own questionnaire" ON questionnaire;

DROP POLICY IF EXISTS "Users can view own equipment" ON equipment;
DROP POLICY IF EXISTS "Users can update own equipment" ON equipment;
DROP POLICY IF EXISTS "Users can insert own equipment" ON equipment;

DROP POLICY IF EXISTS "Users can view own pantry" ON pantry;
DROP POLICY IF EXISTS "Users can update own pantry" ON pantry;
DROP POLICY IF EXISTS "Users can insert own pantry" ON pantry;

DROP POLICY IF EXISTS "Users can view own availability" ON availability;
DROP POLICY IF EXISTS "Users can update own availability" ON availability;
DROP POLICY IF EXISTS "Users can insert own availability" ON availability;

DROP POLICY IF EXISTS "Users can view own weekly_plans" ON weekly_plans;
DROP POLICY IF EXISTS "Users can update own weekly_plans" ON weekly_plans;
DROP POLICY IF EXISTS "Users can insert own weekly_plans" ON weekly_plans;

DROP POLICY IF EXISTS "Users can view own adherence_logs" ON adherence_logs;
DROP POLICY IF EXISTS "Users can update own adherence_logs" ON adherence_logs;
DROP POLICY IF EXISTS "Users can insert own adherence_logs" ON adherence_logs;

DROP POLICY IF EXISTS "Users can view own reminders" ON reminders;
DROP POLICY IF EXISTS "Users can update own reminders" ON reminders;
DROP POLICY IF EXISTS "Users can insert own reminders" ON reminders;

-- PROFILES TABLE POLICIES
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- QUESTIONNAIRE TABLE POLICIES
CREATE POLICY "Users can view own questionnaire" ON questionnaire
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own questionnaire" ON questionnaire
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own questionnaire" ON questionnaire
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- EQUIPMENT TABLE POLICIES
CREATE POLICY "Users can view own equipment" ON equipment
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own equipment" ON equipment
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own equipment" ON equipment
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- PANTRY TABLE POLICIES
CREATE POLICY "Users can view own pantry" ON pantry
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own pantry" ON pantry
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own pantry" ON pantry
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- AVAILABILITY TABLE POLICIES
CREATE POLICY "Users can view own availability" ON availability
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own availability" ON availability
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own availability" ON availability
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- WEEKLY_PLANS TABLE POLICIES
CREATE POLICY "Users can view own weekly_plans" ON weekly_plans
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own weekly_plans" ON weekly_plans
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own weekly_plans" ON weekly_plans
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- ADHERENCE_LOGS TABLE POLICIES
CREATE POLICY "Users can view own adherence_logs" ON adherence_logs
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own adherence_logs" ON adherence_logs
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own adherence_logs" ON adherence_logs
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- REMINDERS TABLE POLICIES
CREATE POLICY "Users can view own reminders" ON reminders
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own reminders" ON reminders
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert own reminders" ON reminders
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- Grant necessary permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
