#!/usr/bin/env python3
"""
Secure test runner - Uses environment variables for secrets
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get secrets from environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Validate secrets are loaded
if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, TELEGRAM_BOT_TOKEN]):
    print("❌ ERROR: Missing environment variables!")
    print("Please create a .env file with:")
    print("  SUPABASE_URL=...")
    print("  SUPABASE_SERVICE_KEY=...")
    print("  TELEGRAM_BOT_TOKEN=...")
    print("\nSee .env.example for template")
    exit(1)

print("✅ Environment variables loaded successfully")
print(f"Supabase URL: {SUPABASE_URL}")
print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...") # Only show first 20 chars
