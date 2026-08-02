#!/usr/bin/env python3
"""
Apply migration directly to Supabase database
"""
import subprocess
import json

# Read migration file
with open('supabase/migrations/add_lesson_completion_tracking.sql', 'r') as f:
    sql = f.read()

# Split into individual statements
statements = []
current_statement = []
in_function = False

for line in sql.split('\n'):
    stripped = line.strip()

    # Track if we're inside a function
    if 'CREATE OR REPLACE FUNCTION' in line:
        in_function = True
    if in_function and stripped.endswith('$$'):
        in_function = False

    # Skip comments and empty lines at the beginning
    if not current_statement and (not stripped or stripped.startswith('--')):
        continue

    current_statement.append(line)

    # End of statement
    if not in_function and stripped.endswith(';') and not stripped.startswith('--'):
        stmt = '\n'.join(current_statement)
        if stmt.strip():
            statements.append(stmt)
        current_statement = []

print(f"Found {len(statements)} SQL statements to execute")
print()

# Execute each statement
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

for i, stmt in enumerate(statements, 1):
    # Print first 100 chars of statement
    preview = stmt.replace('\n', ' ')[:100]
    print(f"Statement {i}/{len(statements)}: {preview}...")

    # Execute via pg_advisory_xact_lock endpoint
    # Note: This is a workaround - normally you'd use psql or Supabase dashboard
    print(f"   ⚠️  Manual execution required in Supabase SQL Editor")

print()
print("=" * 80)
print("MIGRATION INSTRUCTIONS")
print("=" * 80)
print()
print("Please run the following in the Supabase SQL Editor:")
print("https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/sql")
print()
print("Copy and paste the entire file:")
print("supabase/migrations/add_lesson_completion_tracking.sql")
print()
print("Then click 'RUN' to apply the migration.")
print()
