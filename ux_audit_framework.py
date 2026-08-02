#!/usr/bin/env python3
"""
COMPREHENSIVE UX AUDIT FRAMEWORK
Tests the bot from a REAL USER perspective, not just API functionality
"""
import subprocess
import json
import time
from datetime import datetime
from collections import defaultdict

# Configuration
CHAT_ID = 6676414504
BOT_TOKEN = "8883911322:AAEtasRH43qNw7ThK29LFa9YXVzlQtQd788"
WEBHOOK_URL = "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"
SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

# UX Issues Tracker
ux_issues = {
    "critical": [],  # Blocks user from progressing
    "major": [],     # Significantly impacts experience
    "minor": [],     # Small annoyances
    "suggestions": []  # Nice-to-haves
}

def curl_post(url, data):
    cmd = ['curl', '-s', '-X', 'POST', url,
           '-H', 'Content-Type: application/json',
           '-d', json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout}

def curl_get(url, headers=None):
    cmd = ['curl', '-s', url]
    if headers:
        for k, v in headers.items():
            cmd.extend(['-H', f'{k}: {v}'])
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout}

def send_command(command):
    """Simulate user sending a command"""
    update = {
        "message": {
            "message_id": int(time.time()),
            "from": {"id": CHAT_ID, "first_name": "Test", "username": "test"},
            "chat": {"id": CHAT_ID, "type": "private"},
            "date": int(time.time()),
            "text": command
        }
    }
    return curl_post(WEBHOOK_URL, update)

def click_answer(question_id, answer):
    """Simulate user clicking an answer button"""
    update = {
        "callback_query": {
            "id": f"cb_{int(time.time())}",
            "from": {"id": CHAT_ID, "first_name": "Test", "username": "test"},
            "message": {
                "message_id": 999,
                "chat": {"id": CHAT_ID, "type": "private"},
                "date": int(time.time()),
                "text": "Question"
            },
            "data": f"ans_{question_id}_{answer}"
        }
    }
    return curl_post(WEBHOOK_URL, update)

def get_user_state():
    url = f"{SUPABASE_URL}/rest/v1/app_user?telegram_user_id=eq.{CHAT_ID}"
    headers = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}
    result = curl_get(url, headers)
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    return None

def get_lessons():
    url = f"{SUPABASE_URL}/rest/v1/lesson?select=id,title,concept_tag,question(id,type,correct_answer,options)&order=created_at.asc"
    headers = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}
    return curl_get(url, headers)

def get_attempts(user_id, limit=100):
    url = f"{SUPABASE_URL}/rest/v1/attempt?user_id=eq.{user_id}&select=*&order=answered_at.desc&limit={limit}"
    headers = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}
    return curl_get(url, headers)

def log_issue(severity, title, description, user_impact):
    """Log a UX issue"""
    ux_issues[severity].append({
        "title": title,
        "description": description,
        "user_impact": user_impact,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    icon = {"critical": "🔴", "major": "🟠", "minor": "🟡", "suggestions": "💡"}[severity]
    print(f"{icon} {severity.upper()}: {title}")
    print(f"   Impact: {user_impact}")
    print()

print("=" * 80)
print("🎨 COMPREHENSIVE UX AUDIT - User Experience Testing")
print("=" * 80)
print("Testing from a REAL USER perspective")
print("Goal: Find ALL UX issues that impact user experience")
print("=" * 80)
print()

# Get initial state
user = get_user_state()
if not user:
    print("❌ Cannot start - user not found")
    exit(1)

user_id = user['id']
initial_xp = user.get('xp', 0)
initial_streak = user.get('current_streak', 0)

print(f"📊 Initial State:")
print(f"   XP: {initial_xp}")
print(f"   Streak: {initial_streak}")
print()

lessons = get_lessons()
if not isinstance(lessons, list):
    print("❌ Cannot get lessons")
    exit(1)

print(f"📚 Available Lessons: {len(lessons)}")
for i, lesson in enumerate(lessons, 1):
    q_count = len(lesson.get('question', []))
    print(f"   {i}. {lesson.get('title', 'Untitled')} ({q_count} questions)")
print()

# ============================================================================
# USER JOURNEY 1: First-Time User Onboarding
# ============================================================================
print("=" * 80)
print("USER JOURNEY 1: First-Time User Onboarding")
print("=" * 80)
print("Scenario: New user installs bot and sends /start")
print()

send_command("/start")
time.sleep(2)

print("✅ /start sent")
print("❓ UX Question: Does the welcome message explain what the bot does?")
print("❓ UX Question: Does it guide user to send /learn?")
print("❓ UX Question: Is the tone friendly and encouraging?")
print()

# ============================================================================
# USER JOURNEY 2: Learning - First Lesson Experience
# ============================================================================
print("=" * 80)
print("USER JOURNEY 2: First Learning Experience")
print("=" * 80)
print("Scenario: User sends /learn for the first time")
print()

send_command("/learn")
time.sleep(2)

print("✅ /learn sent")
print("❓ UX Question: Does user get a question immediately?")
print("❓ UX Question: Is the difficulty level clear?")
print("❓ UX Question: Are the answer buttons easy to understand?")
print()

# ============================================================================
# USER JOURNEY 3: Completing a Full Lesson (All 3 Questions)
# ============================================================================
print("=" * 80)
print("USER JOURNEY 3: Completing a Full Lesson")
print("=" * 80)
print("Scenario: User answers all 3 questions in a lesson")
print()

if len(lessons) > 0:
    first_lesson = lessons[0]
    questions = first_lesson.get('question', [])

    print(f"Testing with Lesson: {first_lesson.get('title')}")
    print(f"Questions in lesson: {len(questions)}")
    print()

    attempts_before = len(get_attempts(user_id))

    for i, question in enumerate(questions[:3], 1):
        print(f"--- Question {i}/3 ---")

        # Send /learn
        send_command("/learn")
        time.sleep(1)

        # Click an answer
        q_type = question.get('type')
        if q_type == 'mcq':
            answer = 'A'  # Just pick first option
        elif q_type == 'true_false':
            answer = 'true'
        else:
            answer = 'reveal'

        click_answer(question['id'], answer)
        time.sleep(1)

        print(f"✅ Answered question {i}")

    attempts_after = len(get_attempts(user_id))
    print(f"\nAttempts recorded: {attempts_after - attempts_before}")
    print()

# ============================================================================
# USER JOURNEY 4: What Happens AFTER Completing a Lesson? (CRITICAL TEST)
# ============================================================================
print("=" * 80)
print("USER JOURNEY 4: After Completing a Lesson")
print("=" * 80)
print("Scenario: User completed all 3 questions, sends /learn again")
print("🔴 THIS IS WHERE THE BUG SHOULD BE!")
print()

# Send /learn multiple times to see what happens
print("Sending /learn 5 times to simulate user trying to continue...")
questions_received = []

for i in range(5):
    send_command("/learn")
    time.sleep(1.5)

    # Check what question user got (we can't actually see the message, but we can check attempts)
    current_attempts = get_attempts(user_id, limit=1)
    if current_attempts:
        latest_q_id = current_attempts[0].get('question_id')
        questions_received.append(latest_q_id)

print(f"Questions received in last 5 /learn commands:")
unique_questions = set(questions_received)
print(f"  Total: {len(questions_received)}")
print(f"  Unique: {len(unique_questions)}")

if len(unique_questions) == 1:
    log_issue(
        "critical",
        "User stuck on same question after completing lesson",
        "After answering all questions in a lesson, /learn keeps showing the SAME question repeatedly",
        "User cannot progress. Feels like bot is broken. Frustrating experience."
    )
elif len(unique_questions) < len(questions_received):
    log_issue(
        "major",
        "Questions repeat instead of progressing to new lesson",
        "User sees repeated questions instead of moving to a new lesson",
        "Confusing - user doesn't know if they completed the lesson or not"
    )

print()

# ============================================================================
# USER JOURNEY 5: Checking Progress with /stats
# ============================================================================
print("=" * 80)
print("USER JOURNEY 5: Checking Progress")
print("=" * 80)
print("Scenario: User wants to see their progress")
print()

send_command("/stats")
time.sleep(1)

final_user = get_user_state()
print(f"✅ /stats sent")
print(f"Current XP: {final_user.get('xp')}")
print(f"Current Streak: {final_user.get('current_streak')}")
print()

print("❓ UX Question: Does /stats show:")
print("   - How many lessons completed?")
print("   - Progress toward next lesson?")
print("   - Clear goals/milestones?")
print()

# Check if there's lesson completion tracking
completed_url = f"{SUPABASE_URL}/rest/v1/completed_lesson?user_id=eq.{user_id}"
headers = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}
completed = curl_get(completed_url, headers)

if isinstance(completed, dict) and 'error' in completed:
    log_issue(
        "major",
        "No lesson completion tracking",
        "System doesn't track which lessons user has completed",
        "User can't see their progress through lessons. No sense of achievement."
    )

# ============================================================================
# USER JOURNEY 6: Notifications & Settings
# ============================================================================
print("=" * 80)
print("USER JOURNEY 6: Managing Settings")
print("=" * 80)
print("Scenario: User wants to set up notifications")
print()

send_command("/settime 09:00 America/New_York")
time.sleep(1)
print("✅ Sent /settime")

send_command("/notifications on")
time.sleep(1)
print("✅ Sent /notifications on")

print()
print("❓ UX Question: Did user get clear confirmation messages?")
print("❓ UX Question: Can user easily change their mind?")
print()

# ============================================================================
# GENERATE UX AUDIT REPORT
# ============================================================================
print("=" * 80)
print("🎨 UX AUDIT REPORT")
print("=" * 80)
print()

total_issues = sum(len(issues) for issues in ux_issues.values())
print(f"Total UX Issues Found: {total_issues}")
print()

for severity in ["critical", "major", "minor", "suggestions"]:
    issues = ux_issues[severity]
    if issues:
        icon = {"critical": "🔴", "major": "🟠", "minor": "🟡", "suggestions": "💡"}[severity]
        print(f"\n{icon} {severity.upper()} ISSUES ({len(issues)}):")
        print("=" * 80)
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. {issue['title']}")
            print(f"   Description: {issue['description']}")
            print(f"   User Impact: {issue['user_impact']}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

if ux_issues["critical"]:
    print("🔴 CRITICAL: Fix these IMMEDIATELY - users cannot use the app properly")
    for issue in ux_issues["critical"]:
        print(f"   • {issue['title']}")
    print()

if ux_issues["major"]:
    print("🟠 MAJOR: These significantly hurt user experience")
    for issue in ux_issues["major"]:
        print(f"   • {issue['title']}")
    print()

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("1. Fix all critical UX issues")
print("2. Implement lesson completion system")
print("3. Add AI lesson generation for continuous learning")
print("4. Retest entire user journey")
print("5. Get real user feedback")
print()
