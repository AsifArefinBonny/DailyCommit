# Setup Personalized Notifications - Complete Guide

## ✅ What You Get (All FREE!)

- `/settime` - Users set their own notification time + timezone
- `/notifications on/off` - Toggle daily reminders
- Personalized push notifications at each user's chosen time
- No email setup needed (uses Telegram only!)

## 🚀 Quick Setup (3 Steps)

### Step 1: Update Database Schema

Go to Supabase Dashboard → SQL Editor:
https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/sql/new

Copy and run the SQL from: `supabase/migrations/add_notification_preferences.sql`

Or run this directly:

```sql
ALTER TABLE app_user 
ADD COLUMN IF NOT EXISTS preferred_notification_time TIME DEFAULT '08:00:00',
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_app_user_notification_time 
ON app_user(preferred_notification_time) 
WHERE notifications_enabled = true;
```

### Step 2: Deploy Updated Webhook

Go to Supabase Dashboard → Edge Functions:
https://supabase.com/dashboard/project/ybblpzymovvngtllrsbn/functions

1. Click "telegram-webhook"
2. Click "Edit Function"
3. Copy contents from: `supabase/functions/telegram-webhook/index.ts`
4. Paste and click "Deploy"

### Step 3: Verify GitHub Secrets (Already Set!)

The notification workflow uses these secrets (already configured):
- ✅ `DB_URL`
- ✅ `DB_SERVICE_KEY`
- ✅ `TELEGRAM_BOT_TOKEN`

No action needed!

## 🎯 How It Works

### User Experience:

```
User: /settime 14:00 Asia/Dhaka
Bot: ✅ Notification time set!
     🕐 Time: 14:00
     🌍 Timezone: Asia/Dhaka
     
     You'll receive a daily reminder at this time.
```

Every day at 14:00 Bangladesh time:
```
Bot: 📚 Daily Lesson Time!
     
     Your daily QA lesson is ready.
     
     Send /learn to start practicing! 💪
```

User can:
- ✅ Respond immediately with `/learn`
- ✅ Ignore and practice later (no pressure!)
- ✅ Disable with `/notifications off`

### Behind the Scenes:

1. **Hourly Check** (GitHub Actions runs every hour)
2. **Query Users** (checks who has notifications enabled)
3. **Timezone Math** (converts UTC → user's timezone)
4. **Smart Matching** (if current hour matches user's preference, notify)
5. **Send Telegram** (personalized push notification)

## 📱 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/settime HH:MM TIMEZONE` | Set notification time | `/settime 14:00 Asia/Dhaka` |
| `/notifications on` | Enable daily reminders | `/notifications on` |
| `/notifications off` | Disable reminders | `/notifications off` |
| `/learn` | Practice anytime (always works!) | `/learn` |
| `/stats` | View your progress | `/stats` |

## 🌍 Supported Timezones

Use IANA timezone database format:
- `Asia/Dhaka` - Bangladesh
- `America/New_York` - US Eastern
- `Europe/London` - UK
- `Asia/Tokyo` - Japan
- `Australia/Sydney` - Australia

[Full list of timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## 💰 Cost Breakdown

| Resource | Usage | Free Tier | Cost |
|----------|-------|-----------|------|
| **GitHub Actions** | 5 min/day | 2000 min/month | $0.00 ✅ |
| **Telegram Notifications** | Unlimited | Unlimited | $0.00 ✅ |
| **Database Storage** | 3 columns × users | 500 MB | $0.00 ✅ |
| **Supabase Functions** | Already deployed | 500K calls/month | $0.00 ✅ |

**Total: $0.00 per month** (even with 1000+ users!)

## 🧪 Testing

### Test /settime Command:

```
You: /settime 15:30 Asia/Dhaka
Bot: ✅ Notification time set!
     🕐 Time: 15:30
     🌍 Timezone: Asia/Dhaka
```

### Test Notifications Immediately:

```bash
# Trigger notification workflow manually
gh workflow run notify-users.yml

# Check logs
gh run list --workflow=notify-users.yml
gh run view --log
```

### Verify Database:

```sql
-- Check your notification settings
SELECT telegram_user_id, preferred_notification_time, timezone, notifications_enabled
FROM app_user
WHERE notifications_enabled = true;
```

## 🔍 Troubleshooting

### "Invalid time format" Error

✅ **Use HH:MM format**: `14:00` not `2:00 PM`
✅ **24-hour clock**: `23:00` not `11:00 PM`

### "No notification received"

1. Check: Did you enable notifications?
   ```
   /notifications on
   ```

2. Check: Is it the right time in your timezone?
   - Notifications sent within first 10 minutes of the hour
   - Example: Set 14:00 → notified between 14:00-14:10

3. Check workflow logs:
   ```bash
   gh run list --workflow=notify-users.yml
   ```

### "Database error" when using /settime

Run the migration SQL again - columns might not exist yet.

## 📊 Monitoring

### View Active Users with Notifications:

```sql
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN notifications_enabled THEN 1 END) as notif_enabled
FROM app_user;
```

### See Notification Distribution:

```sql
SELECT 
    timezone,
    preferred_notification_time,
    COUNT(*) as user_count
FROM app_user
WHERE notifications_enabled = true
GROUP BY timezone, preferred_notification_time
ORDER BY user_count DESC;
```

## 🎓 User Guide (Share with Users)

**Want daily reminders?**

1. Set your preferred time:
   ```
   /settime 14:00 Asia/Dhaka
   ```

2. You'll get ONE notification per day at that time

3. Respond anytime you want - no pressure!

4. Disable anytime:
   ```
   /notifications off
   ```

5. Still use `/learn` anytime regardless of notifications!

## 🔮 Future Enhancements

Potential additions (all free!):
- [ ] `/settime` with multiple times per day
- [ ] Streak reminder if user hasn't practiced in 23 hours
- [ ] Weekend mode (skip Sat/Sun notifications)
- [ ] Remind me later (snooze for X hours)
- [ ] Weekly summary notifications

## ❓ FAQ

**Q: Do I HAVE to use /settime?**  
A: No! Notifications are optional. You can always use `/learn` anytime.

**Q: Can I change my time?**  
A: Yes! Just use `/settime` again with new time.

**Q: What if I miss the notification?**  
A: No problem! Questions stay in your queue. Practice whenever you want.

**Q: Does this cost money?**  
A: Nope! Completely free using GitHub Actions (2000 free minutes/month).

**Q: How many users can this support?**  
A: 1000+ users easily within free tiers.

---

**All set! 🎉**

Your users can now:
1. Set personalized notification times
2. Get daily reminders in their timezone
3. Practice on their own schedule
4. All for $0.00/month!
