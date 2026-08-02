#!/usr/bin/env python3
"""
Test that the infinite loop bug is fixed
User should get DIFFERENT questions now, not the same one
"""
import subprocess
import json
import time

CHAT_ID = 6676414504
WEBHOOK_URL = "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"

def send_learn():
    data = {
        "message": {
            "message_id": int(time.time()),
            "from": {"id": CHAT_ID, "first_name": "Test"},
            "chat": {"id": CHAT_ID, "type": "private"},
            "date": int(time.time()),
            "text": "/learn"
        }
    }
    cmd = ['curl', '-s', '-X', 'POST', WEBHOOK_URL,
           '-H', 'Content-Type: application/json',
           '-d', json.dumps(data)]
    subprocess.run(cmd, capture_output=True)

print("=" * 80)
print("TESTING INFINITE LOOP FIX")
print("=" * 80)
print()
print("Sending /learn 5 times...")
print("If bug is fixed: You should get DIFFERENT random questions")
print("If bug still exists: You'll get the SAME question 5 times")
print()

for i in range(1, 6):
    print(f"{i}. Sending /learn...")
    send_learn()
    time.sleep(2)

print()
print("✅ Commands sent!")
print()
print("📱 CHECK YOUR TELEGRAM NOW:")
print()
print("Did you receive 5 DIFFERENT questions?")
print("  ✅ YES → Bug is FIXED!")
print("  ❌ NO (same question 5 times) → Bug still exists")
print()
