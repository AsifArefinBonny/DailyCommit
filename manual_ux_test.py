#!/usr/bin/env python3
"""Manual UX Testing - Simulating Real User Journey"""
import subprocess
import json
import time

CHAT_ID = 6676414504
WEBHOOK_URL = "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"

def send_command(text):
    """Send command via webhook"""
    data = {
        "message": {
            "message_id": int(time.time()),
            "from": {"id": CHAT_ID, "first_name": "Test"},
            "chat": {"id": CHAT_ID, "type": "private"},
            "date": int(time.time()),
            "text": text
        }
    }
    cmd = ['curl', '-s', '-X', 'POST', WEBHOOK_URL,
           '-H', 'Content-Type: application/json',
           '-d', json.dumps(data)]
    subprocess.run(cmd)

print("=" * 80)
print("🎨 MANUAL UX TEST - Real User Journey Simulation")
print("=" * 80)
print()

print("USER JOURNEY: Completing lessons and trying to progress")
print()

print("Step 1: User sends /learn")
send_command("/learn")
time.sleep(2)
print("✅ Sent")
print()

print("Step 2: User answers the question (we'll click via webhook)")
print("   (In real usage, you'd click a button in Telegram)")
time.sleep(1)
print()

print("Step 3: User sends /learn again to get next question")
send_command("/learn")
time.sleep(2)
print("✅ Sent")
print()

print("Step 4: User sends /learn again")
send_command("/learn")
time.sleep(2)
print("✅ Sent")
print()

print("Step 5: User sends /learn again (4th time)")
send_command("/learn")
time.sleep(2)
print("✅ Sent")
print()

print("=" * 80)
print("🔍 NOW CHECK YOUR TELEGRAM")
print("=" * 80)
print()
print("Please answer these UX questions:")
print()
print("1. Did you get the SAME question multiple times?")
print("   □ YES - This is the bug! (Practice mode infinite loop)")
print("   □ NO - Different questions each time")
print()
print("2. After answering all 3 questions in a lesson, what happens?")
print("   □ Bot says 'You've completed all new questions!' then repeats")
print("   □ Bot starts a NEW lesson with new questions")
print()
print("3. Can you tell which lesson you're on?")
print("   □ YES - Clearly shows lesson number/name")
print("   □ NO - No indication")
print()
print("4. Can you tell your progress (e.g., Question 2/3 in this lesson)?")
print("   □ YES - Shows progress")
print("   □ NO - No progress indicator")
print()
print("=" * 80)
