# Deploy Webhook with Debug Fixes

## Quick Deploy via Dashboard (Recommended)

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/functions
   - Navigate to: Edge Functions → telegram-webhook

2. **Update the Function Code**
   - Click "Edit Function" or create new version
   - Copy contents from: `supabase/functions/telegram-webhook/index.ts`
   - Paste into the editor
   - Click "Deploy"

3. **Verify Environment Variables**
   - Check that these are set:
     - `TELEGRAM_BOT_TOKEN`
     - `DB_URL`  
     - `DB_SERVICE_ROLE_KEY`

4. **Test the Deployment**
   - Open Telegram bot
   - Send `/learn` command
   - Click an answer button
   - Check the logs in Supabase dashboard

## Check Logs for Debug Output

After testing, check logs for these debug messages:
```
[DEBUG] handleAnswer called: data=ans_XXX_A, userId=YYY
[DEBUG] Parsed: questionId=XXX, answer=A
[DEBUG] Question found: type=mcq, correct_answer=A
```

## Alternative: Deploy via CLI

If you have SUPABASE_ACCESS_TOKEN:

```bash
export SUPABASE_ACCESS_TOKEN='your-token-here'
./deploy_webhook.sh
```

## What Was Fixed

1. ✅ Added debug logging to trace answer validation flow
2. ✅ Fixed setTimeout for Edge Functions (now uses await pattern)
3. ✅ Better error handling and logging for debugging

## Expected Behavior After Fix

- Click answer button → See validation feedback ("✅ Correct!" or "❌ Incorrect")
- Message updates with explanation
- Next question appears after 2 second delay
- Debug logs appear in Supabase function logs
