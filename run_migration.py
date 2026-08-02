#!/usr/bin/env python3
"""
Execute database migration directly via Supabase
"""
import subprocess
import sys

print("=" * 80)
print("APPLYING DATABASE MIGRATION")
print("=" * 80)
print()

# Read migration SQL
with open('supabase/migrations/add_lesson_completion_tracking.sql', 'r') as f:
    migration_sql = f.read()

print("Migration loaded. Executing via Supabase CLI...")
print()

# Save SQL to temp file for execution
temp_file = '/tmp/migration.sql'
with open(temp_file, 'w') as f:
    f.write(migration_sql)

# Execute via supabase db execute (if linked)
try:
    # Try using Supabase CLI directly
    result = subprocess.run(
        ['supabase', 'db', 'execute', '--file', temp_file, '--project-ref', 'ybblpzymovvngtllrsbn'],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0:
        print("✅ Migration executed successfully!")
        print(result.stdout)
    else:
        print("❌ Migration failed:")
        print(result.stderr)
        print()
        print("Please run manually in Supabase SQL Editor:")
        print("https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/sql")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Please run manually in Supabase SQL Editor:")
    print("https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/sql")
    sys.exit(1)

print()
print("=" * 80)
print("VERIFYING MIGRATION")
print("=" * 80)
print()

# Verify tables created
import requests

SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}"
}

# Check completed_lesson table
response = requests.get(f"{SUPABASE_URL}/rest/v1/completed_lesson?limit=1", headers=headers)
if response.status_code == 200:
    print("✅ completed_lesson table exists")
else:
    print(f"❌ completed_lesson table check failed: {response.status_code}")

# Check app_user.current_lesson_id column
response = requests.get(f"{SUPABASE_URL}/rest/v1/app_user?select=current_lesson_id&limit=1", headers=headers)
if response.status_code == 200:
    print("✅ app_user.current_lesson_id column exists")
else:
    print(f"❌ current_lesson_id column check failed: {response.status_code}")

print()
print("✅ Migration complete!")
print()
