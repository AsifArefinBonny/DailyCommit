#!/usr/bin/env python3
"""
Check what error is occurring
"""
import requests
import time

CHAT_ID = 6676414504
BOT_TOKEN = "8883911322:AAEtasRH43qNw7ThK29LFa9YXVzlQtQd788"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Get recent messages/updates
print("Fetching recent bot updates...")
response = requests.get(f"{TELEGRAM_API}/getUpdates?limit=10")
data = response.json()

if data.get("ok"):
    updates = data.get("result", [])
    print(f"Found {len(updates)} recent updates\n")

    for update in updates[-5:]:  # Last 5 updates
        if "message" in update:
            msg = update["message"]
            print(f"Message from user: {msg.get('text')}")
            print(f"  Date: {msg.get('date')}")
            print()
        elif "callback_query" in update:
            cb = update["callback_query"]
            print(f"Callback: {cb.get('data')}")
            print(f"  From: {cb['from'].get('first_name')}")
            print()

# Send a simple /start to trigger
print("\nSending /start to see current behavior...")
response = requests.post(
    f"{TELEGRAM_API}/sendMessage",
    json={
        "chat_id": CHAT_ID,
        "text": "/start"
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print("\nWaiting 3 seconds for webhook...")
time.sleep(3)

# Check updates again
response = requests.get(f"{TELEGRAM_API}/getUpdates?limit=5&offset=-5")
data = response.json()
if data.get("ok"):
    print("\nMost recent bot responses:")
    for update in data.get("result", []):
        if "message" in update and update["message"].get("from", {}).get("is_bot"):
            print(f"Bot said: {update['message'].get('text', 'N/A')[:100]}")
