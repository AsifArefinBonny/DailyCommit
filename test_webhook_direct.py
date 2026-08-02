#!/usr/bin/env python3
"""
Test webhook directly to see the error
"""
import requests
import json
import time

WEBHOOK_URL = "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

# Simulate a /start message
update = {
    "update_id": 999999,
    "message": {
        "message_id": 123,
        "from": {
            "id": 6676414504,
            "is_bot": False,
            "first_name": "Test",
            "username": "test"
        },
        "chat": {
            "id": 6676414504,
            "first_name": "Test",
            "type": "private"
        },
        "date": int(time.time()),
        "text": "/start"
    }
}

print("Sending /start update to webhook...")
print(f"URL: {WEBHOOK_URL}")
print()

response = requests.post(
    WEBHOOK_URL,
    json=update,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SERVICE_KEY}"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print()
print("Response Body:")
print(response.text)
print()

if response.status_code != 200:
    print("❌ ERROR DETECTED!")
    try:
        error_data = response.json()
        print(f"Error Details: {json.dumps(error_data, indent=2)}")
    except:
        print(f"Raw Error: {response.text}")
else:
    print("✅ Webhook responded successfully")
