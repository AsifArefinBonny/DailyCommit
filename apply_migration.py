#!/usr/bin/env python3
"""Apply the lesson completion tracking migration"""
import subprocess

SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

print("=" * 80)
print("APPLYING LESSON COMPLETION TRACKING MIGRATION")
print("=" * 80)
print()

# Read migration file
with open('supabase/migrations/add_lesson_completion_tracking.sql', 'r') as f:
    sql = f.read()

print("Migration SQL loaded")
print("Length:", len(sql), "characters")
print()

print("⚠️  Note: This migration should be run in the Supabase SQL Editor")
print()
print("Instructions:")
print("1. Go to: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/sql")
print("2. Copy the contents of: supabase/migrations/add_lesson_completion_tracking.sql")
print("3. Paste and run in the SQL editor")
print("4. Verify tables created:")
print("   - completed_lesson")
print("   - app_user.current_lesson_id column")
print("   - lesson.is_ai_generated column")
print()

# For now, let's try using supabase CLI if available
import shutil
if shutil.which('supabase'):
    print("✅ Supabase CLI found - attempting to run migration...")
    try:
        result = subprocess.run(
            ['supabase', 'db', 'push'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Migration applied successfully!")
            print(result.stdout)
        else:
            print("❌ Error applying migration:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Supabase CLI not found")
    print("Install with: npm install -g supabase")
    print("Then link project: supabase link --project-ref ybblpzymovvngtllrsbn")
    print()
