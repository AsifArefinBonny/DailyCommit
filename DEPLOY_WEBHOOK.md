# Deploy Telegram Webhook to Supabase

This guide will help you deploy the interactive Telegram webhook to Supabase Edge Functions.

## Prerequisites

- Supabase CLI installed
- Supabase project created
- Telegram bot token

## Step 1: Install Supabase CLI

```bash
# macOS/Linux
brew install supabase/tap/supabase

# Or via npm
npm install -g supabase
```

## Step 2: Login to Supabase

```bash
supabase login
```

## Step 3: Link to Your Project

```bash
supabase link --project-ref YOUR_PROJECT_REF
```

**Find your project ref:**
- Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/general
- Copy the "Reference ID"

## Step 4: Set Environment Secrets

```bash
supabase secrets set TELEGRAM_BOT_TOKEN=your_bot_token_here
supabase secrets set SUPABASE_URL=your_supabase_url
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Step 5: Deploy the Function

```bash
supabase functions deploy telegram-webhook
```

This will output a URL like:
```
https://YOUR_PROJECT_REF.supabase.co/functions/v1/telegram-webhook
```

## Step 6: Register Webhook with Telegram

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://YOUR_PROJECT_REF.supabase.co/functions/v1/telegram-webhook"
  }'
```

**Replace:**
- `YOUR_BOT_TOKEN` with your actual Telegram bot token
- `YOUR_PROJECT_REF` with your Supabase project reference ID

## Step 7: Test the Webhook

Send `/start` to your Telegram bot. You should receive:

```
👋 Welcome to DailyCommit, [Your Name]!

I'll help you level up your QA skills with daily micro-lessons.

📚 Use /learn to start today's lesson
📊 Use /stats to see your progress

Let's get started! 💪
```

Then send `/learn` to start answering questions with interactive buttons!

## Verify Deployment

```bash
# Check function logs
supabase functions logs telegram-webhook

# Check if webhook is registered
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

## Troubleshooting

**Function not deploying:**
```bash
# Check your Supabase CLI version
supabase --version

# Update if needed
brew upgrade supabase
```

**Webhook not responding:**
```bash
# Check the function logs
supabase functions logs telegram-webhook --follow

# Test the endpoint directly
curl https://YOUR_PROJECT_REF.supabase.co/functions/v1/telegram-webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```

**Environment variables not set:**
```bash
# List all secrets
supabase secrets list

# Set missing secrets
supabase secrets set VARIABLE_NAME=value
```

## Commands Available

Once deployed, users can use:
- `/start` - Welcome message
- `/learn` - Start answering questions
- `/stats` - View progress and XP

## Features Enabled

✅ Interactive question delivery with inline buttons
✅ Answer validation with immediate feedback
✅ XP tracking (+10 XP per correct answer)
✅ Streak tracking (consecutive days)
✅ Spaced repetition (SM-2 algorithm)
✅ Progress statistics

## Free Tier Usage

The webhook uses Supabase Edge Functions free tier:
- 500,000 invocations/month
- With ~100 invocations/day = 3,000/month
- **99.4% free tier remaining**

No additional costs! 🎉
