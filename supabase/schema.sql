-- =============================================================================
-- DailyCommit — Supabase schema
-- Run this once in Supabase > SQL Editor (paste + Run).
-- Safe to re-run: uses IF NOT EXISTS / CREATE OR REPLACE where possible.
-- =============================================================================

create extension if not exists "pgcrypto";  -- for gen_random_uuid()

-- -----------------------------------------------------------------------------
-- app_user : you (single user for now, but modeled to generalize)
-- -----------------------------------------------------------------------------
create table if not exists app_user (
  id                uuid primary key default gen_random_uuid(),
  telegram_user_id  bigint unique not null,
  display_name      text,
  timezone          text not null default 'UTC',   -- e.g. 'Asia/Dhaka' — day boundary is measured here
  current_streak    int  not null default 0,
  longest_streak    int  not null default 0,
  last_active_date  date,
  streak_freezes    int  not null default 2,       -- a missed day consumes a freeze instead of resetting
  xp                int  not null default 0,
  level             int  not null default 1,
  interview_mode    boolean not null default false, -- bias questions toward SDET/interview style
  audio_mode        boolean not null default false, -- opt-in: also send a spoken version of the passage
  created_at        timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- topic : mirror of config/topics.yaml, synced on each run.
-- Config file is the source of truth; this table exists so the dashboard and
-- weighting/stats can join against it.
-- -----------------------------------------------------------------------------
create table if not exists topic (
  id           uuid primary key default gen_random_uuid(),
  slug         text unique not null,          -- e.g. 'test-design'
  name         text not null,                 -- e.g. 'Test Design Techniques'
  category     text not null,                 -- 'qa' | 'cs' | 'coding' | 'ai' | 'devops' | 'math' | 'science'
  weight       numeric not null default 1.0,  -- higher = shows up more often
  active       boolean not null default true
);

-- -----------------------------------------------------------------------------
-- lesson : the READ-FIRST passage for a given day + topic
-- -----------------------------------------------------------------------------
create table if not exists lesson (
  id           uuid primary key default gen_random_uuid(),
  lesson_date  date not null,
  topic_id     uuid references topic(id),
  title        text not null,
  body         text not null,                 -- the passage you read first (markdown)
  difficulty   int  not null default 2,       -- 1..5, nudged by adaptive difficulty
  source       text not null default 'ai',    -- 'ai' | 'bank'
  created_at   timestamptz not null default now()
);
create index if not exists idx_lesson_date on lesson(lesson_date);

-- -----------------------------------------------------------------------------
-- question : grounded in a specific lesson (answer is in the passage)
-- -----------------------------------------------------------------------------
create table if not exists question (
  id            uuid primary key default gen_random_uuid(),
  lesson_id     uuid not null references lesson(id) on delete cascade,
  type          text not null,                -- 'mcq'|'true_false'|'fill_in'|'predict_output'|'spot_the_bug'|'short_answer'
  prompt        text not null,
  options       jsonb,                        -- for mcq: ["A ...","B ..."]
  correct_answer text not null,
  explanation   text not null,                -- shown after answering (this is where compounding happens)
  concept_tag   text,                         -- groups items for spaced repetition, e.g. 'boundary-value-analysis'
  difficulty    int not null default 2,
  meta          jsonb                         -- extras per type, e.g. spot_the_bug: {"buggy_code":"...","fixed_code":"..."}
);
create index if not exists idx_question_lesson on question(lesson_id);

-- -----------------------------------------------------------------------------
-- attempt : every answer you give
-- -----------------------------------------------------------------------------
create table if not exists attempt (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references app_user(id),
  question_id   uuid not null references question(id) on delete cascade,
  lesson_id     uuid not null references lesson(id) on delete cascade,
  user_answer   text,
  is_correct    boolean not null,
  confidence    text,                          -- 'guess' | 'unsure' | 'certain' — feeds SRS ease weighting
  time_taken_seconds int,
  answered_at   timestamptz not null default now()
);
create index if not exists idx_attempt_user_time on attempt(user_id, answered_at);

-- -----------------------------------------------------------------------------
-- daily_activity : one row per day — powers streak + the heatmap dashboard
-- -----------------------------------------------------------------------------
create table if not exists daily_activity (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references app_user(id),
  activity_date  date not null,
  completed      boolean not null default false,
  correct_count  int not null default 0,
  total_count    int not null default 0,
  xp_earned      int not null default 0,
  unique (user_id, activity_date)
);

-- -----------------------------------------------------------------------------
-- review_item : spaced repetition (SM-2). One row per concept you've seen.
-- -----------------------------------------------------------------------------
create table if not exists review_item (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references app_user(id),
  concept_tag   text not null,
  ease          numeric not null default 2.5,
  interval_days int not null default 1,
  repetitions   int not null default 0,
  due_date      date not null default current_date,
  last_reviewed date,
  last_result   text,
  unique (user_id, concept_tag)
);
create index if not exists idx_review_due on review_item(user_id, due_date);

-- -----------------------------------------------------------------------------
-- journal_entry : your saved notes/insights (compiled into the weekly digest)
-- -----------------------------------------------------------------------------
create table if not exists journal_entry (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references app_user(id),
  lesson_id  uuid references lesson(id) on delete set null,
  note       text not null,
  created_at timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- badge + user_badge : light gamification
-- -----------------------------------------------------------------------------
create table if not exists badge (
  id          uuid primary key default gen_random_uuid(),
  code        text unique not null,
  name        text not null,
  description text not null,
  icon        text
);
create table if not exists user_badge (
  user_id   uuid not null references app_user(id),
  badge_id  uuid not null references badge(id),
  earned_at timestamptz not null default now(),
  primary key (user_id, badge_id)
);

insert into badge (code, name, description, icon) values
  ('streak_7',   '7-Day Streak',  'Learned 7 days in a row',          '🔥'),
  ('streak_30',  '30-Day Streak', 'Learned 30 days in a row',         '🏆'),
  ('qa_100',     'QA Century',    'Answered 100 QA questions',        '🧪'),
  ('bug_hunter', 'Bug Hunter',    'Nailed 25 spot-the-bug questions', '🐞'),
  ('level_5',    'Level 5',       'Reached level 5',                  '⭐')
on conflict (code) do nothing;

-- -----------------------------------------------------------------------------
-- callback_action : maps a tiny token -> full action state, so Telegram button
-- callback_data stays well under its 64-byte limit. When we send buttons we
-- insert a row and put just 'a:<token>' (or 'a:<token>:<optIdx>') in the button.
-- On tap, the Edge Function looks the token up to recover question/lesson/etc.
-- -----------------------------------------------------------------------------
create table if not exists callback_action (
  token       text primary key,             -- short random id, e.g. 8 chars
  action_type text not null,                -- 'answer' | 'tutor' | 'journal' | 'more'
  user_id     uuid references app_user(id),
  question_id uuid references question(id) on delete cascade,
  lesson_id   uuid references lesson(id) on delete cascade,
  payload     jsonb,                         -- e.g. {"option_index": 2}
  created_at  timestamptz not null default now(),
  expires_at  timestamptz not null default now() + interval '2 days'
);
create index if not exists idx_callback_expiry on callback_action(expires_at);
alter table callback_action enable row level security;  -- private; no anon policy

-- -----------------------------------------------------------------------------
-- scheduled_reminders : powers the "remind me in 2 hrs" snooze button.
-- A scheduler (Supabase pg_cron, recommended) checks this every few minutes
-- and re-sends the nudge when remind_at passes. Snoozing never affects the
-- streak, since the streak is credited on completion, not on delivery time.
-- -----------------------------------------------------------------------------
create table if not exists scheduled_reminders (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references app_user(id),
  lesson_id  uuid references lesson(id) on delete cascade,
  remind_at  timestamptz not null,
  kind       text not null default 'lesson_nudge',
  sent       boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists idx_reminders_due on scheduled_reminders(remind_at) where sent = false;
alter table scheduled_reminders enable row level security;  -- private; no anon policy

-- =============================================================================
-- Dashboard-facing views (safe columns only) — read by the public GitHub Pages
-- dashboard via the anon key. security_invoker=true so RLS applies.
-- =============================================================================
create or replace view v_recent_lessons
  with (security_invoker = true) as
  select l.lesson_date, l.title, l.difficulty, t.name as topic, t.category
  from lesson l left join topic t on t.id = l.topic_id
  order by l.lesson_date desc;

create or replace view v_public_stats
  with (security_invoker = true) as
  select current_streak, longest_streak, xp, level
  from app_user
  limit 1;

-- =============================================================================
-- Row Level Security
--   * anon (dashboard) may READ only public-safe data
--   * the bot/Actions use the service_role key, which bypasses RLS for writes
-- =============================================================================
alter table app_user      enable row level security;
alter table topic         enable row level security;
alter table lesson        enable row level security;
alter table question      enable row level security;
alter table attempt       enable row level security;
alter table daily_activity enable row level security;
alter table review_item   enable row level security;
alter table journal_entry enable row level security;
alter table badge         enable row level security;
alter table user_badge    enable row level security;

-- Public (dashboard) reads — kept to non-sensitive tables/columns:
create policy anon_read_topic          on topic          for select to anon using (true);
create policy anon_read_lesson         on lesson         for select to anon using (true);
create policy anon_read_daily_activity on daily_activity for select to anon using (true);
create policy anon_read_badge          on badge          for select to anon using (true);
create policy anon_read_user_badge     on user_badge     for select to anon using (true);
create policy anon_read_public_stats   on app_user       for select to anon using (true);

-- Note: question (contains answers), attempt, review_item, journal_entry have NO
-- anon policy, so they stay private. Tighten app_user later if you want to hide
-- fields beyond the v_public_stats view.
