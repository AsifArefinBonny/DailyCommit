# DailyCommit 📚

A Telegram bot that delivers one **read-first** micro-lesson per day, tracks your learning streak, and compounds your knowledge over time using spaced repetition and learning science.

**Focus areas:** Software QA, Test Automation, DevOps, Computer Science, Coding, AI/Agents, Math, and Science.

**Cost:** $0 — runs entirely on free tiers (GitHub Actions, Supabase, OpenRouter).

---

## Features

### Core Learning Loop
- **Read-first lessons** with grounded questions (MCQ, true/false, fill-in, predict-output, spot-the-bug, short-answer)
- **Spaced repetition (SM-2)** — wrong/unsure items resurface sooner
- **Confidence calibration** — tap your certainty level to improve retention
- **AI tutor follow-ups** — toggle "Explain Simply" or "Senior QA / Production Context"

### Gamification & Habit Building
- **Streak tracking** with freezes (missed days consume a freeze instead of resetting)
- **XP, levels, and badges** — 7-day streak, 30-day streak, QA Century, Bug Hunter, etc.
- **Snooze button** — "remind me in 2 hrs" (never affects your streak)
- **On-demand lessons** — `/learn` or `/learn <topic>` (daily cap configurable)

### Career Visibility
- **Public GitHub Pages dashboard** — activity heatmap, accuracy trends, recent lessons
- **Interview/SDET mode** — bias questions toward interview-style problems
- **Concept journal** — capture key takeaways from each lesson
- **Export summary** — last 30 days of learnings → LinkedIn/resume-ready Markdown

### Stats
- **Telegram:** `/stats` — streak, accuracy, weakest topic
- **Web dashboard:** GitHub-style heatmap, topic coverage, badges, concept map

---

## Architecture

| Service | Role | Free Tier |
|---------|------|-----------|
| **GitHub Actions** | Daily lesson generation + send, weekly digest, DB keep-alive | Unlimited (public repo) |
| **Supabase Postgres** | All data (see `supabase/schema.sql`) | Pauses after 7 days inactivity — daily writes keep it alive |
| **Supabase Edge Function** | Telegram webhook: answers, `/stats`, `/learn`, tutor toggles, snooze | 500k invocations/mo |
| **Supabase pg_cron** | Fires due snooze reminders (checks every few minutes) | Free extension |
| **OpenRouter** | Free LLM for lesson generation, short-answer grading, tutor follow-ups | Free models (rate-limited) |
| **Telegram Bot API** | Delivery + all interaction | Free |
| **GitHub Pages** | Public dashboard | Free, static |

**Design rule:** GitHub Actions only *delivers*; the database decides everything time-sensitive (streaks, day boundaries, reminders), because scheduled Actions can drift 15–45 min. All day math uses the user's stored `timezone`, not UTC.

---

## Setup

See **[SPEC.md](SPEC.md)** for the full spec and **[CLAUDE.md](CLAUDE.md)** for the build instructions.

### Quick Start

1. **Create accounts:**
   - Telegram bot via [@BotFather](https://t.me/botfather) → `TELEGRAM_BOT_TOKEN`
   - [OpenRouter](https://openrouter.ai/) → `OPENROUTER_API_KEY`
   - [Supabase](https://supabase.com/) → `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

2. **Set up database:**
   - Run `supabase/schema.sql` in Supabase SQL Editor
   - Enable `pg_cron` and `pg_net` extensions
   - Run `supabase/pg_cron.sql`

3. **Deploy Edge Function:**
   - Deploy `supabase/functions/telegram-webhook/index.ts`
   - Set secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, etc.
   - Register webhook with Telegram: `setWebhook` → `<edge-function-url>`

4. **Add GitHub Secrets:**
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`, `OPENROUTER_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

5. **Enable GitHub Pages:**
   - Settings → Pages → Source: `main` branch, `/dashboard` folder
   - Update `dashboard/app.js` with your Supabase URL and anon key

6. **Insert your user:**
   ```sql
   INSERT INTO app_user (telegram_user_id, timezone, display_name)
   VALUES (YOUR_TELEGRAM_USER_ID, 'Asia/Dhaka', 'Your Name');
   ```

7. **Test:**
   - Send `/start` to your bot
   - Manually trigger the daily workflow: Actions → Daily Lesson → Run workflow
   - Check `/stats`

---

## Development Roadmap

See **[SPEC.md §6](SPEC.md)** for the suggested rollout order.

**v1 (ship first):**
- ✅ Daily read-first lesson + grounded quiz
- ✅ Streak tracking
- ✅ `/stats` command
- ✅ Full error/alerting layer

**v2:**
- ⬜ Spaced repetition
- ⬜ Web dashboard
- ⬜ Snooze reminders

**v3:**
- ⬜ Predict-first mode
- ⬜ Confidence tap
- ⬜ Misconception distractors
- ⬜ Journal resurfacing
- ⬜ Weak-area remediation days
- ⬜ Audio mode
- ⬜ `/export_summary`
- ⬜ Tutor toggles
- ⬜ Spot-the-bug copy/diff

---

## Configuration

Edit `config/topics.yaml` to customize:
- **Topics & weights** (higher weight = shows up more often)
- **Question type distribution** (MCQ, true/false, fill-in, etc.)
- **LLM models** (primary + fallback chain)
- **Lesson settings** (questions per lesson, passage length)
- **On-demand cap** (max `/learn` requests per day)
- **Tutor prompts** (Explain Simply, Senior QA)

---

## Contributing

Contributions welcome! Please open an issue or PR.

---

## License

MIT

---

**Built with ❤️ for continuous learning. One lesson at a time. 🚀**
