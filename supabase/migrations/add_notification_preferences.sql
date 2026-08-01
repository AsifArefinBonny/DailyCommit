-- Migration: Add notification preferences to app_user table
-- Date: 2026-08-02
-- Description: Adds timezone and notification time preferences for personalized reminders

-- Add new columns for notification preferences
ALTER TABLE app_user 
ADD COLUMN IF NOT EXISTS preferred_notification_time TIME DEFAULT '08:00:00',
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT true;

-- Create index for faster notification queries
CREATE INDEX IF NOT EXISTS idx_app_user_notification_time 
ON app_user(preferred_notification_time) 
WHERE notifications_enabled = true;

-- Add column comments for documentation
COMMENT ON COLUMN app_user.preferred_notification_time IS 'User preferred time for daily lesson notifications (in their timezone)';
COMMENT ON COLUMN app_user.timezone IS 'User timezone (e.g., Asia/Dhaka, America/New_York) - IANA timezone database format';
COMMENT ON COLUMN app_user.notifications_enabled IS 'Whether user wants to receive daily push notifications';

-- Verify migration
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Users can now use /settime to set notification preferences.';
END $$;
