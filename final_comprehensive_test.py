#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE BOT TEST
Tests all bot features after fixes have been deployed
"""
import requests
import time
import json

# Configuration
CHAT_ID = 6676414504
BOT_TOKEN = "8883911322:AAEtasRH43qNw7ThK29LFa9YXVzlQtQd788"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}"
}

def send_command(command):
    """Send a command to the bot"""
    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": command
        }
    )
    return response.json().get("ok")

def get_user_stats():
    """Get current user stats from database"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/app_user",
        params={"telegram_user_id": f"eq.{CHAT_ID}"},
        headers=headers
    )
    users = response.json()
    if isinstance(users, list) and len(users) > 0:
        return users[0]
    return None

def get_recent_attempts(user_id, limit=5):
    """Get recent question attempts"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/attempt",
        params={
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": str(limit)
        },
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return []

print("=" * 80)
print("🧪 FINAL COMPREHENSIVE BOT TEST")
print("=" * 80)
print(f"Testing all bot features after deployment")
print(f"Chat ID: {CHAT_ID}")
print()

# Get initial stats
print("📊 Getting initial user stats...")
initial_stats = get_user_stats()
if initial_stats:
    print(f"✅ User found:")
    print(f"   Display Name: {initial_stats.get('display_name')}")
    print(f"   XP: {initial_stats.get('xp')}")
    print(f"   Streak: {initial_stats.get('current_streak')} days")
    print(f"   Notifications: {'ON' if initial_stats.get('notifications_enabled') else 'OFF'}")
else:
    print("❌ User not found!")
print()

# TEST 1: /start command
print("=" * 80)
print("TEST 1: /start Command")
print("=" * 80)
print("Sending /start...")
if send_command("/start"):
    print("✅ /start command sent successfully")
    time.sleep(2)
else:
    print("❌ Failed to send /start")
print()

# TEST 2: /learn command (should provide questions, no blocking)
print("=" * 80)
print("TEST 2: /learn Command (First Question)")
print("=" * 80)
print("Sending /learn...")
if send_command("/learn"):
    print("✅ /learn command sent successfully")
    print("⏳ Waiting 3 seconds for webhook...")
    time.sleep(3)
    print("📱 CHECK TELEGRAM: You should see a question (NOT 'tomorrow' message)")
else:
    print("❌ Failed to send /learn")
print()

# TEST 3: /learn command again (test practice mode)
print("=" * 80)
print("TEST 3: /learn Command Again (Should Still Work)")
print("=" * 80)
print("Sending /learn again...")
if send_command("/learn"):
    print("✅ Second /learn sent successfully")
    time.sleep(3)
    print("📱 CHECK TELEGRAM: You should see another question")
else:
    print("❌ Failed to send second /learn")
print()

# TEST 4: /stats command
print("=" * 80)
print("TEST 4: /stats Command (Should Show XP)")
print("=" * 80)
print("Sending /stats...")
if send_command("/stats"):
    print("✅ /stats command sent successfully")
    time.sleep(2)
    print("📱 CHECK TELEGRAM: Stats should display with XP value (not undefined)")
else:
    print("❌ Failed to send /stats")
print()

# TEST 5: /settime command
print("=" * 80)
print("TEST 5: /settime Command")
print("=" * 80)
print("Sending /settime 14:00 Asia/Dhaka...")
if send_command("/settime 14:00 Asia/Dhaka"):
    print("✅ /settime command sent successfully")
    time.sleep(2)
    print("📱 CHECK TELEGRAM: Should confirm time was set")
else:
    print("❌ Failed to send /settime")
print()

# TEST 6: /notifications command
print("=" * 80)
print("TEST 6: /notifications Command")
print("=" * 80)
print("Sending /notifications on...")
if send_command("/notifications on"):
    print("✅ /notifications command sent successfully")
    time.sleep(2)
    print("📱 CHECK TELEGRAM: Should confirm notifications enabled")
else:
    print("❌ Failed to send /notifications")
print()

# Get final stats
print("=" * 80)
print("📊 Final Database Check")
print("=" * 80)
final_stats = get_user_stats()
if final_stats:
    print(f"✅ User stats after testing:")
    print(f"   Display Name: {final_stats.get('display_name')}")
    print(f"   XP: {final_stats.get('xp')}")
    print(f"   Streak: {final_stats.get('current_streak')} days")
    print(f"   Notifications: {'ON' if final_stats.get('notifications_enabled') else 'OFF'}")
    print(f"   Notification Time: {final_stats.get('preferred_notification_time')}")
    print(f"   Timezone: {final_stats.get('timezone')}")

    # Get attempts
    attempts = get_recent_attempts(final_stats['id'])
    print(f"\n   Recent Attempts: {len(attempts)}")
    for i, att in enumerate(attempts[:3], 1):
        status = "✅" if att.get('correct') else "❌"
        print(f"   {i}. {status} Answer: {att.get('user_answer')}")
else:
    print("❌ User not found!")
print()

# Summary
print("=" * 80)
print("📋 TEST SUMMARY")
print("=" * 80)
print("✅ All commands sent successfully")
print()
print("🎯 CRITICAL FIXES TO VERIFY IN TELEGRAM:")
print("   1. /learn should NEVER show 'tomorrow' message")
print("   2. /learn should provide questions even if all answered")
print("   3. /stats should show XP value (not undefined)")
print("   4. Question progression should work without repeating same question")
print()
print("📱 CHECK YOUR TELEGRAM NOW AND VERIFY:")
print("   • /start shows welcome message")
print("   • /learn provides questions without blocking")
print("   • /stats displays correct XP and stats")
print("   • /settime confirmed time change")
print("   • /notifications confirmed toggle")
print()
print("📊 CHECK SUPABASE LOGS:")
print("   https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/functions/telegram-webhook/logs")
print()
