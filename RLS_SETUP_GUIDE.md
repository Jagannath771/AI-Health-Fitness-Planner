# Row Level Security (RLS) Setup Guide

This guide will help you implement Row Level Security policies for your FitLife Planner application to ensure proper data isolation between users.

## 🔒 What is Row Level Security?

Row Level Security (RLS) is a PostgreSQL feature that restricts which rows users can access in a table. It ensures that users can only see and modify their own data, providing strong data isolation and security.

## 📋 Prerequisites

- Supabase project with PostgreSQL database
- Admin access to your Supabase project
- Database connection working in your app

## 🚀 Step 1: Apply RLS Policies

1. **Open Supabase Dashboard**
   - Go to your Supabase project dashboard
   - Navigate to **SQL Editor**

2. **Run the RLS Script**
   - Copy the contents of `database_policies.sql`
   - Paste it into the SQL Editor
   - Click **Run** to execute the script

3. **Verify Policies Applied**
   - Go to **Authentication** → **Policies**
   - You should see policies for all tables
   - Each policy should show "Users can view/update/insert own [table_name]"

## 🔧 Step 2: Update Your Application

The database functions have been updated to work with RLS. The key changes:

### User Context Setting
```python
# Each database operation now sets the user context
db.execute(f"SET app.current_user_id = '{user_id}'")
```

### Updated Functions
- `get_or_create_profile()` - Sets user context
- `get_user_db()` - New helper for user-scoped database sessions
- All database operations now respect RLS policies

## 🧪 Step 3: Test the Policies

### Test 1: User Isolation
1. Create two different user accounts
2. Login as User A, create some data
3. Login as User B, verify you can't see User A's data
4. Verify User B can only see their own data

### Test 2: Data Access
1. Login as any user
2. Try to access different pages (Onboarding, Equipment, etc.)
3. Verify all data operations work correctly
4. Verify you can only see your own data

## 🔍 How RLS Works

### Policy Structure
```sql
CREATE POLICY "Users can view own data" ON table_name
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));
```

### User Context
- Each database session sets `app.current_user_id`
- Policies check this setting against the `user_id` column
- Only matching rows are accessible

### Table Coverage
All tables now have RLS enabled:
- ✅ `profiles` - User profiles
- ✅ `questionnaire` - User questionnaire data
- ✅ `equipment` - User equipment lists
- ✅ `pantry` - User pantry items
- ✅ `availability` - User schedule data
- ✅ `weekly_plans` - User workout/meal plans
- ✅ `adherence_logs` - User progress tracking
- ✅ `reminders` - User reminders

## 🛡️ Security Benefits

1. **Data Isolation** - Users can only access their own data
2. **Prevents Data Leaks** - No accidental cross-user data access
3. **Database-Level Security** - Security enforced at the database level
4. **Audit Trail** - All access is logged and traceable
5. **Compliance Ready** - Meets data privacy requirements

## 🚨 Important Notes

### Before Applying RLS
- **Backup your data** - Always backup before making schema changes
- **Test in development** - Apply to a test environment first
- **Verify app functionality** - Ensure all features still work

### After Applying RLS
- **Monitor logs** - Check for any access denied errors
- **Test thoroughly** - Verify all user flows work correctly
- **Update documentation** - Document the security changes

## 🔧 Troubleshooting

### Common Issues

1. **Access Denied Errors**
   - Check if user context is being set correctly
   - Verify the user_id matches the policy condition

2. **Data Not Visible**
   - Ensure RLS policies are applied correctly
   - Check if user context is set before queries

3. **Performance Issues**
   - RLS can add overhead to queries
   - Consider adding indexes on user_id columns

### Debug Commands
```sql
-- Check if RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Check current user context
SELECT current_setting('app.current_user_id', true);

-- List all policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';
```

## ✅ Verification Checklist

- [ ] RLS policies applied to all tables
- [ ] User context setting works correctly
- [ ] Users can only see their own data
- [ ] All app functionality works with RLS
- [ ] No access denied errors in logs
- [ ] Performance is acceptable
- [ ] Data isolation is working properly

## 🎯 Next Steps

1. Apply the RLS policies using the SQL script
2. Test the application thoroughly
3. Monitor for any issues
4. Consider adding additional security measures (rate limiting, etc.)
5. Document the security implementation

Your FitLife Planner app will now have enterprise-grade data security! 🔒
