-- =============================================================================
-- DailyCommit — pg_cron setup for snooze reminders
-- Run this after enabling pg_cron and pg_net extensions in Supabase.
-- =============================================================================

-- Enable required extensions (if not already enabled)
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- Schedule snooze reminder checker (runs every 5 minutes)
-- This queries scheduled_reminders for due reminders and sends them via Telegram
select cron.schedule(
  'process-snooze-reminders',
  '*/5 * * * *',  -- Every 5 minutes
  $$
  select net.http_post(
    url := current_setting('app.settings.edge_function_url') || '/process-reminders',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    ),
    body := '{}'::jsonb
  );
  $$
);

-- Set configuration (replace with your actual values during setup)
-- These should be set via Supabase dashboard > Project Settings > Custom Postgres Config
-- Example:
-- ALTER DATABASE postgres SET app.settings.edge_function_url = 'https://your-project.supabase.co/functions/v1/telegram-webhook';
-- ALTER DATABASE postgres SET app.settings.service_role_key = 'your-service-role-key';
