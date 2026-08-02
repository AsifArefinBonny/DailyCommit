# DailyCommit Dashboard

A beautiful, real-time progress dashboard for DailyCommit users.

## Features

- **Activity Heatmap**: GitHub-style contribution graph showing daily learning activity
- **Progress Stats**: Lessons completed, XP earned, streak tracking, and accuracy
- **XP Progress Chart**: Cumulative XP growth over time
- **Accuracy Trend**: Daily performance tracking
- **Topic Mastery**: See which SQA topics you've mastered
- **Recent Activity**: Latest completed lessons

## How to Access Your Dashboard

### Option 1: URL Parameter
Visit: `https://YOUR_USERNAME.github.io/DailyCommit/?user=YOUR_TELEGRAM_CHAT_ID`

### Option 2: Get Your Chat ID from the Bot
1. Send `/stats` to the DailyCommit bot
2. Your chat ID will be shown
3. Visit the dashboard URL with your ID

### Example
If your Telegram chat ID is `123456789`, visit:
```
https://asifarefinbonny.github.io/DailyCommit/?user=123456789
```

The dashboard will remember your ID in your browser for future visits.

## Technologies Used

- Vanilla JavaScript (no framework)
- Chart.js for data visualization
- Supabase for real-time data
- Pure CSS with CSS Grid and Flexbox
- Responsive design for mobile and desktop

## Local Development

1. Serve the dashboard directory:
   ```bash
   cd dashboard
   python3 -m http.server 8000
   ```

2. Open `http://localhost:8000` in your browser

## Deployment

This dashboard is automatically deployed to GitHub Pages from the `dashboard/` directory.
