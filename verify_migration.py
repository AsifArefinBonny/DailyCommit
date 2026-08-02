#!/usr/bin/env python3
import requests

SUPABASE_URL = 'https://ybblpzymovvngtllrsbn.supabase.co'
SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg'

headers = {'apikey': SERVICE_KEY, 'Authorization': f'Bearer {SERVICE_KEY}'}

print("=" * 80)
print("VERIFYING DATABASE MIGRATION")
print("=" * 80)
print()

checks = []

# Check 1: completed_lesson table
r = requests.get(f'{SUPABASE_URL}/rest/v1/completed_lesson?limit=1', headers=headers)
status1 = "EXISTS" if r.status_code == 200 else "MISSING"
checks.append(('completed_lesson table', status1 == "EXISTS"))
print(f"1. completed_lesson table: {status1}")

# Check 2: current_lesson_id column
r = requests.get(f'{SUPABASE_URL}/rest/v1/app_user?select=current_lesson_id&limit=1', headers=headers)
status2 = "EXISTS" if r.status_code == 200 else "MISSING"
checks.append(('current_lesson_id column', status2 == "EXISTS"))
print(f"2. current_lesson_id column: {status2}")

# Check 3: user_progress_stats view
r = requests.get(f'{SUPABASE_URL}/rest/v1/user_progress_stats?limit=1', headers=headers)
status3 = "EXISTS" if r.status_code == 200 else "MISSING"
checks.append(('user_progress_stats view', status3 == "EXISTS"))
print(f"3. user_progress_stats view: {status3}")

# Check 4: lesson.is_ai_generated column
r = requests.get(f'{SUPABASE_URL}/rest/v1/lesson?select=is_ai_generated&limit=1', headers=headers)
status4 = "EXISTS" if r.status_code == 200 else "MISSING"
checks.append(('lesson.is_ai_generated column', status4 == "EXISTS"))
print(f"4. lesson.is_ai_generated column: {status4}")

print()
print("=" * 80)

if all(check[1] for check in checks):
    print("SUCCESS: All migration components verified!")
    print("=" * 80)
else:
    print("FAILURE: Some components missing:")
    for name, passed in checks:
        if not passed:
            print(f"  - {name}")
    print("=" * 80)
