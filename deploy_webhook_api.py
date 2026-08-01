#!/usr/bin/env python3
"""
Deploy Telegram webhook to Supabase using Management API
No CLI login required!
"""
import os
import requests
import json

print("🚀 DailyCommit Webhook Deployment")
print("=" * 50)
print()

# Get credentials
print("📋 Enter your credentials:")
print()

SUPABASE_PROJECT_REF = input("Supabase Project Ref (ybblpzymovvngtllrsbn): ").strip() or "ybblpzymovvngtllrsbn"
SUPABASE_ACCESS_TOKEN = input("Supabase Access Token: ").strip()
TELEGRAM_BOT_TOKEN = input("Telegram Bot Token: ").strip()
SUPABASE_URL = input(f"Supabase URL (https://{SUPABASE_PROJECT_REF}.supabase.co): ").strip() or f"https://{SUPABASE_PROJECT_REF}.supabase.co"
SUPABASE_SERVICE_KEY = input("Supabase Service Role Key: ").strip()

print()
print("📖 Reading webhook code...")

# Read the webhook code
webhook_path = "supabase/functions/telegram-webhook/index.ts"
with open(webhook_path, "r") as f:
    webhook_code = f.read()

print(f"✓ Loaded {len(webhook_code)} characters of code")
print()

# Deploy function using Supabase Management API
print("📦 Deploying function to Supabase...")

# Management API endpoint
api_base = f"https://api.supabase.com/v1/projects/{SUPABASE_PROJECT_REF}"

headers = {
    "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# Create/update the Edge Function
function_payload = {
    "slug": "telegram-webhook",
    "name": "telegram-webhook",
    "verify_jwt": False,
    "import_map": False,
    "entrypoint_path": "./index.ts"
}

# First, create or get the function
print("  → Creating function...")
response = requests.post(
    f"{api_base}/functions",
    headers=headers,
    json=function_payload
)

if response.status_code in [200, 201, 409]:  # 409 means already exists
    print("  ✓ Function created/exists")
else:
    print(f"  ⚠️ Status: {response.status_code}")
    print(f"  Response: {response.text}")

# Deploy the function code
print("  → Deploying code...")

deploy_payload = {
    "slug": "telegram-webhook",
    "body": webhook_code,
    "verify_jwt": False
}

response = requests.post(
    f"{api_base}/functions/telegram-webhook/deploys",
    headers=headers,
    json=deploy_payload
)

if response.status_code in [200, 201]:
    print("  ✓ Code deployed successfully!")
else:
    print(f"  ❌ Deployment failed: {response.status_code}")
    print(f"  Response: {response.text}")
    print()
    print("📌 Try manual deployment instead:")
    print(f"   https://supabase.com/dashboard/project/{SUPABASE_PROJECT_REF}/functions")
    exit(1)

# Set environment secrets
print()
print("🔐 Setting environment secrets...")

secrets = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SERVICE_ROLE_KEY": SUPABASE_SERVICE_KEY
}

for key, value in secrets.items():
    print(f"  → Setting {key}...")
    response = requests.post(
        f"{api_base}/secrets",
        headers=headers,
        json={"name": key, "value": value}
    )
    if response.status_code in [200, 201]:
        print(f"  ✓ {key} set")
    else:
        print(f"  ⚠️ {key} status: {response.status_code}")

# Register webhook with Telegram
print()
print("📡 Registering webhook with Telegram...")

webhook_url = f"https://{SUPABASE_PROJECT_REF}.supabase.co/functions/v1/telegram-webhook"

telegram_response = requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
    json={"url": webhook_url}
)

telegram_data = telegram_response.json()

if telegram_data.get("ok"):
    print(f"  ✓ Webhook registered!")
    print(f"  URL: {webhook_url}")
else:
    print(f"  ❌ Failed: {telegram_data.get('description')}")
    exit(1)

# Verify
print()
print("🔍 Verifying webhook...")

verify_response = requests.get(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
)

info = verify_response.json().get("result", {})
print(f"  URL: {info.get('url')}")
print(f"  Pending updates: {info.get('pending_update_count', 0)}")

if info.get('last_error_message'):
    print(f"  ⚠️ Last error: {info.get('last_error_message')}")
else:
    print("  ✓ No errors!")

print()
print("=" * 50)
print("🎉 Deployment Complete!")
print()
print("Try it out:")
print("  1. Open Telegram and find your bot")
print("  2. Send: /start")
print("  3. Send: /learn")
print()
print("You should see interactive question buttons! 🚀")
