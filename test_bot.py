#!/usr/bin/env python3
"""
Comprehensive Bot Testing Script
Tests deployment, database, and bot functionality
"""
import requests
import time
import json

# Configuration
BOT_TOKEN = "8883911322:AAEtasRH43qNw7ThK29LFa9YXVzlQtQd788"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

print("🧪 DailyCommit Bot Comprehensive Test")
print("=" * 60)
print()

# Test 1: Get Bot Info
print("📡 Test 1: Checking bot API connection...")
try:
    response = requests.get(f"{TELEGRAM_API}/getMe")
    data = response.json()
    if data.get("ok"):
        bot_info = data["result"]
        print(f"✅ Bot connected: @{bot_info['username']}")
        print(f"   Bot ID: {bot_info['id']}")
        print(f"   Name: {bot_info['first_name']}")
    else:
        print(f"❌ Bot API error: {data}")
except Exception as e:
    print(f"❌ Failed to connect to bot: {e}")
print()

# Test 2: Get Webhook Info
print("📡 Test 2: Checking webhook configuration...")
try:
    response = requests.get(f"{TELEGRAM_API}/getWebhookInfo")
    data = response.json()
    if data.get("ok"):
        webhook = data["result"]
        print(f"✅ Webhook URL: {webhook.get('url', 'Not set')}")
        print(f"   Pending updates: {webhook.get('pending_update_count', 0)}")
        if webhook.get('last_error_date'):
            print(f"   ⚠️ Last error: {webhook.get('last_error_message')}")
    else:
        print(f"❌ Webhook check failed: {data}")
except Exception as e:
    print(f"❌ Failed to check webhook: {e}")
print()

# Test 3: Query Database for Users
print("💾 Test 3: Querying database for users...")
try:
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}"
    }
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/app_user",
        params={"select": "telegram_user_id,name,total_xp,current_streak"},
        headers=headers
    )
    users = response.json()
    if isinstance(users, list):
        print(f"✅ Found {len(users)} user(s) in database:")
        for user in users:
            chat_id = user['telegram_user_id']
            print(f"\n   📱 Chat ID: {chat_id}")
            print(f"      Name: {user['name']}")
            print(f"      Total XP: {user['total_xp']}")
            print(f"      Streak: {user['current_streak']} days")

            # Save the first user's chat_id for testing
            if 'CHAT_ID' not in globals():
                globals()['CHAT_ID'] = chat_id
                print(f"      👆 Using this chat_id for testing")
    else:
        print(f"❌ Database error: {users}")
        print(f"   Response status: {response.status_code}")
except Exception as e:
    print(f"❌ Failed to query database: {e}")
print()

# Test 4: Query Recent Attempts
print("💾 Test 4: Checking recent attempts...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/attempt",
        params={
            "select": "created_at,user_answer,correct",
            "order": "created_at.desc",
            "limit": "5"
        },
        headers=headers
    )
    attempts = response.json()
    if isinstance(attempts, list):
        print(f"✅ Found {len(attempts)} recent attempt(s):")
        for att in attempts:
            status = "✅ Correct" if att['correct'] else "❌ Incorrect"
            print(f"   • {att['created_at'][:19]} - Answer: {att['user_answer']} - {status}")
    else:
        print(f"⚠️ Could not parse attempts: {response.status_code}")
except Exception as e:
    print(f"❌ Failed to query attempts: {e}")
print()

# Test 5: Query Questions
print("💾 Test 5: Checking available questions...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/question",
        params={
            "select": "id,type,prompt",
            "limit": "3"
        },
        headers=headers
    )
    questions = response.json()
    print(f"✅ Found {len(questions)} question(s) in database:")
    for q in questions:
        print(f"   • [{q['type']}] {q['prompt'][:60]}...")
except Exception as e:
    print(f"❌ Failed to query questions: {e}")
print()

# Test 6: Send Test Message (if we have chat_id)
if 'CHAT_ID' in globals():
    CHAT_ID = globals()['CHAT_ID']
    print(f"📨 Test 6: Sending test message to chat_id {CHAT_ID}...")
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": "🧪 *Bot Test Message*\n\nThis is an automated test to verify the bot is working correctly.\n\nSend /learn to test the fix!",
                "parse_mode": "Markdown"
            }
        )
        data = response.json()
        if data.get("ok"):
            print(f"✅ Test message sent successfully!")
            print(f"   Message ID: {data['result']['message_id']}")
        else:
            print(f"❌ Failed to send message: {data}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
    print()
else:
    print("⚠️ Test 6: Skipped (no chat_id found)")
    print("   Please send /start to the bot first, then run this script again.")
    print()

# Summary
print("=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)
if 'CHAT_ID' in globals():
    print(f"✅ Your Chat ID: {globals()['CHAT_ID']}")
    print()
    print("🎯 NEXT STEPS:")
    print("1. Check your Telegram - you should have received a test message")
    print("2. Send /learn to test the question flow")
    print("3. Click an answer and check if you progress to next question")
    print("4. Send /stats to verify XP is updating")
else:
    print("⚠️ No users found in database")
    print("   Please send /start to your bot first!")
print()
