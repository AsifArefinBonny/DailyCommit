#!/usr/bin/env python3
"""
TEST QUESTION ANSWERING FLOW
Simulates the complete flow of answering questions
"""
import requests
import time

# Configuration
CHAT_ID = 6676414504
BOT_TOKEN = "8883911322:AAEtasRH43qNw7ThK29LFa9YXVzlQtQd788"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json"
}

def get_questions():
    """Get available questions from database"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/question",
        params={"limit": "5"},
        headers=headers
    )
    return response.json() if response.status_code == 200 else []

def get_user():
    """Get user from database"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/app_user",
        params={"telegram_user_id": f"eq.{CHAT_ID}"},
        headers=headers
    )
    users = response.json()
    return users[0] if isinstance(users, list) and len(users) > 0 else None

def send_webhook_update(update_data):
    """Send a simulated update to the webhook"""
    webhook_url = f"{SUPABASE_URL}/functions/v1/telegram-webhook"
    response = requests.post(
        webhook_url,
        json=update_data,
        headers=headers
    )
    return response

print("=" * 80)
print("🧪 QUESTION FLOW TEST")
print("=" * 80)
print()

# Get questions
print("📚 Fetching available questions...")
questions = get_questions()
if not questions:
    print("❌ No questions found!")
    exit(1)

print(f"✅ Found {len(questions)} question(s)")
for i, q in enumerate(questions[:3], 1):
    print(f"   {i}. [{q['type']}] {q['prompt'][:50]}...")
    print(f"      Correct Answer: {q['correct_answer']}")
print()

# Get user
print("👤 Fetching user...")
user = get_user()
if not user:
    print("❌ User not found!")
    exit(1)

print(f"✅ User: {user['display_name']} (ID: {user['id']})")
print(f"   Current XP: {user['xp']}")
print()

# Test simulating a callback query (answering a question)
print("=" * 80)
print("TEST: Simulating Answer to Question")
print("=" * 80)

if len(questions) > 0:
    test_question = questions[0]
    question_id = test_question['id']
    correct_answer = test_question['correct_answer']

    print(f"Question: {test_question['prompt'][:60]}...")
    print(f"Correct Answer: {correct_answer}")
    print()

    # For MCQ, get the letter option
    if test_question['type'] == 'mcq':
        options = test_question.get('options', [])
        # Find which option matches the correct answer
        answer_letter = None
        for i, opt in enumerate(options):
            if opt.lower() == correct_answer.lower():
                answer_letter = chr(65 + i)  # A, B, C, D
                break

        if answer_letter:
            callback_data = f"ans_{question_id}_{answer_letter}"
            print(f"📤 Simulating answer: {answer_letter} ({correct_answer})")
            print(f"   Callback data: {callback_data}")
            print()

            # Simulate a callback query
            update = {
                "callback_query": {
                    "id": "test_callback_123",
                    "from": {
                        "id": CHAT_ID,
                        "first_name": "Test",
                        "username": "test"
                    },
                    "message": {
                        "message_id": 999,
                        "chat": {
                            "id": CHAT_ID,
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": "Test question"
                    },
                    "data": callback_data
                }
            }

            print("🔄 Sending callback query to webhook...")
            response = send_webhook_update(update)

            if response.status_code == 200:
                print(f"✅ Webhook responded: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            else:
                print(f"❌ Webhook error: {response.status_code}")
                print(f"   Error: {response.text}")

            print()
            time.sleep(2)

            # Check if XP was updated
            print("📊 Checking if XP was updated...")
            updated_user = get_user()
            if updated_user:
                print(f"   Previous XP: {user['xp']}")
                print(f"   Current XP: {updated_user['xp']}")
                if updated_user['xp'] > user['xp']:
                    print(f"   ✅ XP increased by {updated_user['xp'] - user['xp']}!")
                else:
                    print(f"   ⚠️ XP not updated (may need to check webhook)")
        else:
            print("⚠️ Could not determine answer letter for MCQ")
    else:
        print("⚠️ Non-MCQ question - manual testing required")

print()
print("=" * 80)
print("📋 NEXT STEPS")
print("=" * 80)
print("1. Check your Telegram to see if you received:")
print("   • Questions from /learn")
print("   • Feedback after answering")
print("   • Next question automatically")
print()
print("2. Try answering a question in Telegram and verify:")
print("   • You get immediate feedback (✅ or ❌)")
print("   • Next question appears automatically")
print("   • XP is updated in /stats")
print()
print("3. Test /learn multiple times to ensure:")
print("   • No 'tomorrow' blocking message")
print("   • Questions are always available")
print("   • Practice mode works after completing all questions")
print()
