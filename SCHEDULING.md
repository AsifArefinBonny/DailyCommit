# DailyCommit Scheduling System

## How Lessons Work

### 1. On-Demand Learning (`/learn`)
- **Trigger**: User sends `/learn` command anytime
- **Behavior**: Delivers the next pending question immediately
- **Database**: Fetches unanswered questions from recent lessons
- **Frequency**: Unlimited - users can practice anytime

### 2. Scheduled Daily Lessons
- **Trigger**: GitHub Actions workflow runs automatically
- **Schedule**: Currently set to **8:00 AM UTC daily**
- **Process**:
  1. `generate_daily.py` creates new lesson with 5 questions
  2. Questions saved to database
  3. Available to all users via `/learn`
- **Notification**: Currently NO automatic push notifications

## Current Schedule Configuration

**File**: `.github/workflows/daily.yml`

```yaml
schedule:
  - cron: '0 8 * * *'  # 8:00 AM UTC every day
```

### What Time Is 8:00 AM UTC For You?

| Your Location | Local Time |
|---------------|------------|
| **Bangladesh (UTC+6)** | 2:00 PM (14:00) |
| New York (UTC-5) | 3:00 AM |
| London (UTC+0) | 8:00 AM |
| Tokyo (UTC+9) | 5:00 PM |

## Changing the Schedule

### Option 1: Change Global Schedule (All Users)

Edit `.github/workflows/daily.yml`:

```yaml
schedule:
  # Change to 6:00 AM UTC (12:00 PM Bangladesh Time)
  - cron: '0 6 * * *'
```

Cron format: `minute hour day month weekday`
- `0 6 * * *` = 6:00 AM UTC daily
- `0 12 * * *` = 12:00 PM UTC daily
- `0 0 * * *` = Midnight UTC daily

**Commit and push** - GitHub Actions will use new schedule.

### Option 2: Per-User Scheduled Notifications (Future Feature)

Currently **NOT IMPLEMENTED**, but here's how it would work:

1. **Add to Database Schema**:
```sql
ALTER TABLE app_user ADD COLUMN preferred_time TIME;
ALTER TABLE app_user ADD COLUMN timezone VARCHAR(50);
```

2. **User Command**: `/settime 14:00 Asia/Dhaka`
   - Stores user's preferred time and timezone
   
3. **New Workflow**: Create `notify-users.yml`
   - Runs every hour
   - Checks which users want notification at current time
   - Sends personalized Telegram message

4. **Implementation Needed**:
```typescript
// In webhook handler
async function handleSetTime(chatId, userId, time, timezone) {
  await supabase
    .from("app_user")
    .update({ 
      preferred_time: time, 
      timezone: timezone 
    })
    .eq("id", userId);
    
  await sendMessage(chatId, 
    `⏰ Daily lessons will be sent at ${time} ${timezone}`);
}
```

## Current Behavior

### What Happens Now:

1. **8:00 AM UTC Daily**:
   - GitHub Actions runs `generate_daily.py`
   - New lesson created with 5 questions
   - Questions stored in database
   - **NO notification sent to users**

2. **When User Opens Bot**:
   - User manually sends `/learn`
   - Bot delivers next unanswered question
   - User can practice anytime, not just at 8 AM

### What Users See:

- ✅ **New content daily** (questions added to pool)
- ❌ **NO push notifications** (users must initiate with `/learn`)
- ✅ **Can practice anytime** (on-demand learning)
- ✅ **Same lesson for everyone** (no personalization yet)

## Implementing Push Notifications (Feature Request)

To notify users when new lessons are available:

### Option A: Broadcast to All Users (Simple)

Add to `generate_daily.py`:

```python
def notify_all_users(lesson_title):
    """Send notification to all users after lesson generation"""
    users = supabase.table("app_user").select("telegram_user_id").execute()
    
    message = f"📚 New lesson available: {lesson_title}\n\nSend /learn to start!"
    
    for user in users.data:
        try:
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": user["telegram_user_id"],
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
        except Exception as e:
            print(f"Failed to notify user {user['telegram_user_id']}: {e}")
```

### Option B: Per-User Scheduled (Complex)

1. **Add timezone field** to user table
2. **Create hourly cron job**
3. **Query users** whose preferred time matches current hour
4. **Send notifications** only to those users
5. **Handle timezone conversions**

## Testing Schedule Changes

```bash
# Manually trigger daily lesson workflow
gh workflow run daily.yml

# Check workflow status
gh run list --workflow=daily.yml

# View workflow logs
gh run view --log
```

## Recommendations

### For Now (MVP):
1. ✅ Keep 8:00 AM UTC schedule
2. ✅ Users manually use `/learn` when convenient
3. ✅ Add broadcast notification to `generate_daily.py` (optional)

### For Future (v3):
1. Add `preferred_time` and `timezone` fields to users
2. Implement `/settime` command
3. Create hourly notification scheduler
4. Add "Remind me daily" option

## Summary

| Feature | Current Status | User Action |
|---------|---------------|-------------|
| **Daily Lesson Generation** | ✅ Automated (8 AM UTC) | None (automatic) |
| **Push Notifications** | ❌ Not implemented | Must send `/learn` |
| **On-Demand Learning** | ✅ Working | Send `/learn` anytime |
| **Personalized Schedule** | ❌ Not implemented | Same time for everyone |
| **Change Global Time** | ✅ Configurable | Edit `.github/workflows/daily.yml` |

## Quick Actions

**Change lesson generation time to 6:00 AM UTC (12 PM Bangladesh)**:
```bash
# Edit .github/workflows/daily.yml
sed -i 's/0 8 \* \* \*/0 6 * * */' .github/workflows/daily.yml
git add .github/workflows/daily.yml
git commit -m "Change lesson time to 6 AM UTC (12 PM Bangladesh)"
git push
```

**Add broadcast notification**:
Add the `notify_all_users()` function to `bot/generate_daily.py` and call it after lesson creation.
