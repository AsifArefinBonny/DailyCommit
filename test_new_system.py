#!/usr/bin/env python3
"""Test the new lesson progression system"""
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
print("TESTING NEW LESSON PROGRESSION SYSTEM")
print("=" * 80)
print()
print("Sending /learn...")
send_learn()
time.sleep(3)

print()
print("=" * 80)
print("CHECK YOUR TELEGRAM NOW!")
print("=" * 80)
print()
print("You should see:")
print("  - Question 1/3 (or 2/3, or 3/3)")
print("  - Lesson title shown")
print("  - Difficulty stars")
print()
print("After answering 3 questions:")
print("  - 'Lesson Complete!' message")
print("  - XP earned")
print("  - NEW AI-generated lesson starts automatically")
print()
