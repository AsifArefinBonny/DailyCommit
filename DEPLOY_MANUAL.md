# Manual Webhook Deployment (Supabase Dashboard)

Since the Supabase CLI requires interactive login, here's how to deploy via the web interface:

## Step 1: Open Supabase Dashboard

Go to: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/functions

## Step 2: Create New Function

1. Click **"Create a new function"**
2. Name: `telegram-webhook`
3. Click **"Create function"**

## Step 3: Copy the Code

1. Open the file: `supabase/functions/telegram-webhook/index.ts`
2. Copy ALL the code (420 lines)
3. Paste it into the function editor in Supabase dashboard
4. Click **"Deploy"**

## Step 4: Set Environment Variables

In the Supabase dashboard:

1. Go to: **Settings > Edge Functions**
2. Add these secrets:
   - `TELEGRAM_BOT_TOKEN`: (your bot token from GitHub Secrets)
   - `SUPABASE_URL`: https://ybblpzymovvngtllrsbn.supabase.co
   - `SUPABASE_SERVICE_ROLE_KEY`: (your service role key from GitHub Secrets)

## Step 5: Get Function URL

After deployment, the function URL will be:
```
https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook
```

## Step 6: Register Webhook with Telegram

Run this command (replace YOUR_BOT_TOKEN):

```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ybblpzymovvngtllrsbn.supabase.co/functions/v1/telegram-webhook"
  }'
```

You should see:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

## Step 7: Test It!

1. Open Telegram and find your bot
2. Send: `/start`
   - You should get a welcome message
3. Send: `/learn`
   - You should see a question with interactive buttons!
4. Click a button to answer
   - You'll get instant feedback and XP

## Verify It's Working

Check the webhook status:
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

Should show:
- `url`: Your webhook URL
- `pending_update_count`: 0 (if no errors)
- `last_error_date`: Should be empty

## Troubleshooting

**Function not deploying:**
- Make sure you copied ALL 420 lines of code
- Check for syntax errors in the editor
- Try refreshing the page and deploying again

**Webhook not responding:**
- Check function logs in Supabase dashboard
- Verify environment variables are set correctly
- Make sure the webhook URL matches exactly

**Commands not working:**
- Send `/start` first to initialize your user account
- Check Telegram bot token is correct
- View Edge Function logs for errors

## Quick Deployment Script

If you prefer, I can also prepare a script that uses the Supabase API directly to deploy, which doesn't require CLI login.

Would you like me to create that?
