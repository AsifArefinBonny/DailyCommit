#!/usr/bin/env python3
import requests

BOT_TOKEN = "8883911322:AAEtasRH43qNw7ThK29LFa9YXVzlQtQd788"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

print("Getting user info from database...")

# Try querying without specifying columns
SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}"
}

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/app_user",
    params={"limit": "1"},
    headers=headers
)

print(f"Status: {response.status_code}")
data = response.json()
if isinstance(data, list) and len(data) > 0:
    print(f"\n✅ Found user!")
    user = data[0]
    print(f"Available columns: {list(user.keys())}")
    print(f"\nFull user data:")
    for key, value in user.items():
        print(f"  {key}: {value}")

    chat_id = user.get('telegram_user_id')
    print(f"\n🎯 YOUR CHAT_ID: {chat_id}")
else:
    print(f"Error or no data: {data}")
