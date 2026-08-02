#!/usr/bin/env python3
"""Check current lesson structure and user progress"""
import subprocess
import json

SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"
USER_ID = "05591089-d051-4eb4-af34-746b0838437e"

def curl_get(url):
    cmd = ['curl', '-s', url,
           '-H', f'apikey: {SERVICE_KEY}',
           '-H', f'Authorization: Bearer {SERVICE_KEY}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout}

# Get lessons
print("=" * 80)
print("CURRENT LESSON STRUCTURE")
print("=" * 80)
lessons = curl_get(f"{SUPABASE_URL}/rest/v1/lesson?select=id,title,concept_tag,question(id,type,prompt)&limit=5")
if isinstance(lessons, list):
    for i, lesson in enumerate(lessons, 1):
        print(f"\nLesson {i}: {lesson.get('title')}")
        print(f"  Concept: {lesson.get('concept_tag')}")
        questions = lesson.get('question', [])
        print(f"  Questions: {len(questions)}")
        for j, q in enumerate(questions[:3], 1):
            print(f"    {j}. [{q['type']}] {q['prompt'][:60]}...")

# Get user attempts
print("\n" + "=" * 80)
print("USER ATTEMPT HISTORY")
print("=" * 80)
attempts = curl_get(f"{SUPABASE_URL}/rest/v1/attempt?user_id=eq.{USER_ID}&select=lesson_id,question_id,is_correct,answered_at&order=answered_at.desc&limit=20")
if isinstance(attempts, list):
    print(f"Total attempts: {len(attempts)}")

    # Group by lesson
    lesson_attempts = {}
    for att in attempts:
        lid = att.get('lesson_id')
        if lid not in lesson_attempts:
            lesson_attempts[lid] = []
        lesson_attempts[lid].append(att)

    print(f"\nAttempts per lesson:")
    for lid, atts in lesson_attempts.items():
        print(f"  Lesson {lid[:8]}...: {len(atts)} attempts")

# Check if there's a completed_lesson table
print("\n" + "=" * 80)
print("CHECKING FOR LESSON COMPLETION TRACKING")
print("=" * 80)
completed = curl_get(f"{SUPABASE_URL}/rest/v1/completed_lesson?user_id=eq.{USER_ID}&select=*")
if isinstance(completed, dict) and 'error' in completed:
    print("❌ No completed_lesson table found")
elif isinstance(completed, list):
    print(f"✅ Found {len(completed)} completed lessons")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)
print("The issue: Bot is in 'practice mode' because all questions have been attempted.")
print("Current behavior: Randomly repeats old questions")
print("Desired behavior: Generate NEW lessons with 3 NEW questions each")
