# DailyCommit — Build Spec & Roadmap

A Telegram bot that delivers one **read-first** micro-lesson per day (a short passage you
read, then questions grounded in it so googling won't shortcut them), tracks a streak,
and compounds your learning over time. Focused on software QA, automation, DevOps, CS,
coding, AI/agents, math, and science. Runs entirely on free tiers.

---

## 1. Architecture ($0 stack)

| Service | Role | Free-tier note |
|---|---|---|
| **GitHub Actions** (cron) | Daily lesson generate + send, weekly digest, DB keep-alive | Unlimited minutes on a public repo |
| **Supabase Postgres** | All data (see schema.sql) | Pauses after 7 days of no DB activity — daily writes keep it alive |
| **Supabase Edge Function** | Telegram webhook: answers, `/stats`, `/learn`, tutor toggles, snooze | 500k invocations/mo free |
| **Supabase pg_cron** | Fires due snooze reminders (checks every few min in-DB) | Extension, free |
| **OpenRouter** | Free LLM for lesson generation, short-answer grading, tutor follow-ups | Free models are rate-limited (see §4) |
| **Telegram Bot API** | Delivery + all interaction | Free |
| **GitHub Pages** | Public "my recent learnings" dashboard | Free, static |

Key design rule: **GitHub Actions only *delivers*; the database decides everything
time-sensitive** (streaks, day boundaries, reminders), because scheduled Actions can
drift 15–45 min. All day math uses the user's stored `timezone`, not UTC.

---

## 2. Core loop

read-first passage → *(sometimes)* predict-first guess → confidence tap
(guess / unsure / certain) → answer → reveal + explanation → spaced-repetition scheduling
→ streak / XP / badge updates.

---

## 3. Feature list (the development list)

**Core**
- Read-first lessons with grounded questions
- Question types: MCQ, true/false, fill-in, predict-output, spot-the-bug, short-answer
  (AI-graded), scenario/"what would you do" judgment drills, explain-it-back (Feynman)

**Retention & learning science**
- Spaced repetition (SM-2), wrong/unsure items resurface sooner
- Predict-first mode (pretesting effect)
- Confidence calibration tap → weights SRS ease
- Misconception-targeted MCQ distractors with tailored corrections
- Journal-note resurfacing (re-surface *your own* past insights, not just facts)
- Weekly synthesis challenge (combine the week's concepts)
- Weak-area remediation days (target lowest-accuracy topics)

**Gamification & habit**
- Streaks with freezes; streak credited on first completion of the day
- XP / levels / badges
- Snooze "remind me in 2 hrs" button (never affects streak)
- On-demand extra lessons: `/learn` and `/learn <topic>` (daily cap in config)
- Opt-in audio mode for commutes (edge-tts → Telegram voice message)

**Explanations & UX**
- AI tutor follow-up with two toggles: 💡 Explain Simply / 🛠️ Senior QA / Production Context
- Spot-the-bug: Copy Code / Show Diff (fixed version stored in `question.meta`)

**Career visibility**
- Interview / SDET mode toggle
- `/export_summary`: last 30 days of journal + concepts → LinkedIn/resume-ready Markdown
- Concept journal + one-tap "takeaway" capture per lesson
- Public GitHub Pages dashboard (Layer 2) linked from portfolio

**Stats**
- Layer 1: `/stats` in Telegram (streak, longest, totals, accuracy, weakest topic)
- Layer 2: web dashboard — GitHub-style activity heatmap, accuracy trend, topic
  coverage, badges, optional concept map

---

## 4. Reliability & observability

**Principle: never fail silently. Every failure produces a human-readable reason sent to
your Telegram**, so you know *why* instead of guessing. A single `notify_admin(service,
status, reason, context)` helper formats every alert consistently.

Alert shape:
> ⚠️ **Daily lesson failed** · service: OpenRouter · HTTP 429
> reason: rate-limited on `deepseek-...:free` (retry_after 30s)
> action: tried fallback `llama-...:free` → also 429. No lesson today; will retry tomorrow.
> run: <github actions run url>

**OpenRouter** — the most likely thing to trip:
- Exponential backoff + retries; then a fallback model chain (free models only).
- Parse the response `error.code` / `error.message` and classify into a clear reason:
  `rate_limited` (429, honor `retry_after`), `quota_exhausted` (free daily cap hit),
  `model_unavailable` (5xx / model offline → switch model), `invalid_output`
  (JSON failed Pydantic validation → one stricter retry, then fallback),
  `auth` (401 → bad/rotated key), `network` (timeout).
- Strict Pydantic schema validation before anything is written to Supabase, so a
  malformed generation can never corrupt data.

**Telegram Bot API**
- 429 → respect `parameters.retry_after`; 401 → bad token; 403 → bot blocked;
  400 → message/entity formatting error (log the offending payload).

**Supabase**
- Paused project returns HTTP **540** / connection refused → alert "Supabase paused,
  restore it in the dashboard." Daily lesson write doubles as keep-alive so this
  shouldn't happen unless something else broke.
- Surface auth (401) and RLS-violation errors verbatim.

**GitHub Actions**
- A final `if: failure()` step sends the Telegram alert with the run URL. GitHub also
  emails on workflow failure by default — leave that on.

**Health**
- Optional weekly "systems OK ✅" ping so silence always means something, not nothing.

---

## 5. Configuration

- `config/topics.yaml` (source of truth, editable): subjects + weights, question-pattern
  frequencies, lesson settings, model + fallback ids, prompt templates, on-demand cap.
- Per-user preferences in the DB (`app_user`): timezone, `audio_mode`, `interview_mode`,
  toggled via a `/settings` command.

---

## 6. Suggested rollout order

1. **v1 (ship first):** daily read-first lesson + grounded quiz + streak + `/stats`,
   with the full error/alerting layer from §4. Live with it for a week.
2. **v2:** spaced repetition, web dashboard, snooze reminders.
3. **v3:** predict-first, confidence tap, misconception distractors, journal resurfacing,
   weak-area days, audio mode, `/export_summary`, tutor toggles, copy/diff.

Rationale: an app you use beats a perfect app you're still building — and a 10-minute
session can't hold every feature at once anyway.

---

## 7. Secrets (you hold these — never share them in chat)

Stored as GitHub Actions secrets and Supabase Function secrets:
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `OPENROUTER_API_KEY`,
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
The dashboard uses only the public `SUPABASE_ANON_KEY` against read-only views.
