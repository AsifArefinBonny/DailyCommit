# CLAUDE.md — project instructions

This is **DailyCommit**, a daily learning Telegram bot. **Read `SPEC.md` for the full spec
and feature list, and `supabase/schema.sql` for the data model.** This file tells you how
to build it.

## What we're building
A Telegram bot that sends one read-first micro-lesson per day (a passage to read, then
questions grounded in it), tracks a streak, and compounds learning via spaced repetition.
Everything runs on free tiers. See SPEC.md §3 for the complete feature list.

## Stack
- **GitHub Actions (Python)** — scheduled jobs: daily generate+send, weekly digest.
- **Supabase Postgres** — all data (schema.sql).
- **Supabase Edge Function (Deno/TypeScript)** — the Telegram webhook: handles answer
  taps, `/stats`, `/learn`, tutor toggles, snooze. This is the always-on interactive piece.
- **Supabase pg_cron** — fires due snooze reminders.
- **OpenRouter** — free LLM for generation, grading, tutor follow-ups.
- **GitHub Pages** — static public dashboard.

> Note the language split: Actions jobs are **Python**, the Edge Function is **TypeScript/Deno**.

## Proposed repo structure
```
├── CLAUDE.md  ├── SPEC.md  ├── config/topics.yaml
├── supabase/
│   ├── schema.sql
│   ├── pg_cron.sql                    # reminder scheduler setup
│   └── functions/telegram-webhook/index.ts
├── bot/                               # Python (GitHub Actions)
│   ├── generate_daily.py  ├── weekly_digest.py
│   ├── openrouter.py                  # retries, fallback chain, error classification
│   ├── models.py                      # Pydantic schemas for LLM output
│   ├── srs.py                         # SM-2  ├── db.py  ├── telegram.py  # + notify_admin
│   └── requirements.txt
├── dashboard/                         # static site (GitHub Pages)
│   ├── index.html  ├── app.js  ├── styles.css
└── .github/workflows/daily.yml, weekly.yml
```

## Build order (ship v1 first — see SPEC.md §6)
1. **v1:** daily read-first lesson + grounded quiz + streak + `/stats`, with the full
   error/alert layer from SPEC.md §4. Get this working end-to-end before anything else.
2. **v2:** spaced repetition, web dashboard, snooze reminders.
3. **v3:** predict-first, confidence tap, misconception distractors, journal resurfacing,
   weak-area days, audio mode, `/export_summary`, tutor toggles, spot-the-bug copy/diff.

## Conventions (important)
- **All time/day/streak math happens in the DB using the user's stored `timezone`**, never
  from when an Action happens to run (Actions drift 15–45 min).
- **Wrap every external call** (OpenRouter, Telegram, Supabase) so any failure calls the
  `notify_admin(service, status, reason, context)` helper and pings Telegram with the
  human-readable reason. Never fail silently. See SPEC.md §4 for the taxonomy.
- **Validate all LLM JSON with Pydantic** before writing to Supabase.
- **Free OpenRouter models only** (`:free` suffix); model ids come from `config/topics.yaml`,
  with a fallback chain. Never hardcode a paid model.
- **Never invent URLs** in lesson content. If a "go deeper" link is included, use only
  canonical doc roots (e.g. official docs), never a guessed deep link.
- **Secrets** live in GitHub Actions secrets and Supabase Function secrets. Never commit
  them; never print them in logs or alerts.

## Setup runbook (the human does these once; you can't create accounts)
1. Create the Telegram bot via **@BotFather** → `TELEGRAM_BOT_TOKEN`.
2. Create an **OpenRouter** account → `OPENROUTER_API_KEY`.
3. Create a **Supabase** project → `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
4. Run `supabase/schema.sql` in the Supabase SQL editor.
5. Enable the `pg_cron` and `pg_net` extensions, then run `supabase/pg_cron.sql`.
6. Deploy the Edge Function; set `TELEGRAM_WEBHOOK_SECRET` + the Supabase secrets on it.
7. Register the webhook: `setWebhook` with `url=<edge fn url>&secret_token=<TELEGRAM_WEBHOOK_SECRET>`,
   and verify the `X-Telegram-Bot-Api-Secret-Token` header inside the function.
8. Add all secrets as **GitHub Actions secrets**.
9. Enable **GitHub Pages** serving `/dashboard`.
10. Insert your `app_user` row (`telegram_user_id`, `timezone`, e.g. `Asia/Dhaka`).

## Definition of done for v1
You receive a lesson each morning, can read it and answer inline, your streak and `/stats`
update correctly, and any failure of OpenRouter / Telegram / Supabase produces a clear
Telegram alert stating the service and reason.
