# 🚨 URGENT SECURITY FIX REQUIRED

## Issue: Telegram Bot Token Exposed on GitHub

Your Telegram bot token was accidentally committed to the public repository in `.claude/settings.local.json`.

**Current exposed token:** `8883911322:AAHcdyWpsWHvdosW9BtP0Km4Jft8crphcEM`

## ⚠️ IMMEDIATE ACTIONS REQUIRED (Do This NOW!)

### Step 1: Revoke Old Bot Token (2 minutes)

1. Open Telegram and find **@BotFather**
2. Send: `/mybots`
3. Select your bot: **DailyCommit**
4. Click: **API Token**
5. Click: **Revoke current token**
6. Click: **Yes, I'm sure**
7. BotFather will show: `Done! The token has been revoked`

**WARNING:** Your bot will STOP working until you complete Step 2!

### Step 2: Generate New Bot Token (1 minute)

1. Still in **@BotFather**
2. Click: **API Token** again
3. BotFather shows new token like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
4. **COPY THIS TOKEN** immediately

### Step 3: Update GitHub Secret (30 seconds)

```bash
# Replace with your NEW token
gh secret set TELEGRAM_BOT_TOKEN --body "YOUR-NEW-TOKEN-HERE"
```

### Step 4: Update Supabase Env Vars (1 minute)

1. Go to: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/settings/functions
2. Find: `TELEGRAM_BOT_TOKEN`
3. Click Edit
4. Paste your NEW token
5. Save

### Step 5: Re-register Webhook (30 seconds)

```bash
# Replace with your NEW token
curl -X POST "https://api.telegram.org/botYOUR-NEW-TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"}'
```

You should see: `{"ok":true,"result":true,...}`

### Step 6: Verify Bot Works

Open Telegram and send to your bot:
```
/start
```

Bot should respond with welcome message.

## ✅ Git Cleanup (Already Done)

I've already:
- ✅ Removed `.claude/settings.local.json` from git tracking
- ✅ Added it to `.gitignore`
- ✅ Staged these changes for commit

## 🔒 Why This Happened

The `.claude/settings.local.json` file contains approved Bash commands with the bot token embedded. This file should NEVER be committed to git.

## 🛡️ Prevention

**Never commit these files:**
- `.claude/settings.local.json` (now in .gitignore)
- `.env` files
- Any file containing secrets

**Always use:**
- GitHub Secrets for workflows
- Supabase Environment Variables for functions
- Environment variables locally

## ⏱️ Time Sensitive

**Do Steps 1-5 NOW!** The old token is public and anyone can:
- ❌ Send messages as your bot
- ❌ Read incoming messages
- ❌ Impersonate your bot

After you complete Steps 1-5, your bot will be secure again! 🔒
