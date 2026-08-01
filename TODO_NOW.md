# ✅ TODO NOW - Get Everything Working

## Step 1: Run Database Migration (2 minutes)

1. Go to: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/sql/new

2. Copy and paste this SQL:

```sql
-- Add notification preferences
ALTER TABLE app_user 
ADD COLUMN IF NOT EXISTS preferred_notification_time TIME DEFAULT '08:00:00',
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT true;

-- Create index
CREATE INDEX IF NOT EXISTS idx_app_user_notification_time 
ON app_user(preferred_notification_time) 
WHERE notifications_enabled = true;
```

3. Click "Run" button

4. You should see: "Success. No rows returned"

## Step 2: Redeploy Webhook (2 minutes)

You said you already did this, but let's double-check:

1. Go to: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/functions/telegram-webhook

2. Click **"Edit Function"** button (not just view)

3. **DELETE ALL existing code** in the editor

4. Open this file on your computer: `supabase/functions/telegram-webhook/index.ts`

5. **Copy THE ENTIRE FILE** (all 650+ lines)

6. **Paste** into Supabase editor

7. Click **"Deploy"** button

8. Wait for "Deployed successfully" message

## Step 3: Test in Telegram (1 minute)

Open your Telegram bot and test:

```
You: /start
Bot: Should show welcome message with all commands

You: /settime 14:00 Asia/Dhaka
Bot: ✅ Notification time set! ...

You: /notifications on
Bot: ✅ Notifications enabled! ...

You: /learn
Bot: Should show a question with answer buttons

Click an answer button
Bot: Should show ✅ Correct or ❌ Incorrect, then next question
```

## What to Check If Things Don't Work

### If /settime gives error:
- ❌ Database migration wasn't run → Go back to Step 1

### If /learn questions don't work:
- Check Supabase logs: https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/functions/telegram-webhook/logs
- Look for `[DEBUG]` messages
- If NO debug messages → Webhook wasn't deployed correctly → Go back to Step 2

### If no notifications arrive:
- Wait 1 hour (notifications check every hour on the hour)
- OR manually trigger: `gh workflow run notify-users.yml`
- Check logs: `gh run list --workflow=notify-users.yml`

## What You'll Have After This

✅ `/settime 14:00 Asia/Dhaka` - Set your notification time
✅ `/notifications on/off` - Toggle reminders
✅ `/learn` - Practice anytime, answer validation works
✅ `/stats` - View your progress
✅ Daily push notifications at your chosen time

All for **$0.00/month**!

## Summary of What We Built Today

1. ✅ Weekly test reports via Telegram (no email setup needed)
2. ✅ `/settime` command for personalized notifications
3. ✅ `/notifications` command to toggle reminders
4. ✅ Hourly workflow that sends timezone-aware notifications
5. ✅ Debug logging for webhook troubleshooting
6. ✅ Complete documentation (MCP_SETUP.md, SCHEDULING.md, SETUP_NOTIFICATIONS.md)

## Questions Answered

**Q: How will I know about new lessons?**
A: After you use `/settime`, you'll get a daily push notification at your chosen time!

**Q: Does /learn give new lesson each time?**
A: No, it continues from where you left off. You work through a queue of all available questions.

**Q: Can I snooze?**  
A: Yes! Ignore the notification and use `/learn` whenever you want. No pressure!

**Q: Does this cost money?**
A: Nope! $0.00 forever (GitHub Actions free tier = 2000 min/month, we use ~5 min/day)

---

**Start with Step 1 above!** 👆

## Can I Change My /settime?

**YES! Call `/settime` again anytime you want to change it.**

Example:
```
Monday:
You: /settime 14:00 Asia/Dhaka
Bot: ✅ Notification time set! Time: 14:00

Wednesday (you want to change it):
You: /settime 18:00 Asia/Dhaka
Bot: ✅ Notification time set! Time: 18:00

Now you get notifications at 18:00 instead!
```

It's just an UPDATE in the database - no limits on how many times you can change it!

## /settime vs Daily Lesson Schedule

**Important clarification:**

There are TWO different "schedules" in the system:

### 1. Daily Lesson GENERATION Schedule (GitHub Actions)
- **What**: Creates NEW lessons with 5 questions
- **When**: 8:00 AM UTC daily (currently)
- **Who**: Same time for EVERYONE
- **How to change**: Edit `.github/workflows/daily.yml` (affects all users)
- **Location**: File `.github/workflows/daily.yml` line 12

### 2. Your Personal NOTIFICATION Schedule (/settime)
- **What**: Sends YOU a reminder "Daily Lesson Time!"
- **When**: YOUR chosen time in YOUR timezone
- **Who**: Individual per user
- **How to change**: Just send `/settime` again!
- **Updatable**: YES, unlimited times

### How They Work Together:

```
8:00 AM UTC - GitHub Actions generates 5 new questions → Database
                (This happens automatically, same time for all users)

14:00 Bangladesh Time - Your notification goes out: "📚 Daily Lesson Time!"
18:00 New York Time - Another user's notification goes out
21:00 Tokyo Time - Another user's notification goes out
                (Each user gets reminded at THEIR chosen time)

Any time - You can send /learn to practice (regardless of schedule)
```

So:
- **Lesson creation** = Fixed global schedule (8 AM UTC)
- **Your reminders** = Personal, updatable anytime with `/settime`

Make sense?
