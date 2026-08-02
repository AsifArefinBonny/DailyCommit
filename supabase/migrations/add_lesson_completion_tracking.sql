-- Migration: Add Lesson Completion Tracking
-- This enables tracking which lessons users have completed
-- and supports the 3-questions-per-lesson progression system

-- 1. Create completed_lesson table
CREATE TABLE IF NOT EXISTS completed_lesson (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  lesson_id UUID NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  questions_correct INT NOT NULL DEFAULT 0,
  total_questions INT NOT NULL DEFAULT 3,
  xp_earned INT NOT NULL DEFAULT 0,
  UNIQUE(user_id, lesson_id)
);

-- 2. Add current_lesson_id to app_user
-- This tracks which lesson the user is currently working on
ALTER TABLE app_user
ADD COLUMN IF NOT EXISTS current_lesson_id UUID REFERENCES lesson(id);

-- 3. Add lesson metadata for tracking
-- These fields help with AI generation and progression
ALTER TABLE lesson
ADD COLUMN IF NOT EXISTS is_ai_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS generated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS topic_category VARCHAR(100);

-- 4. Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_completed_lesson_user ON completed_lesson(user_id);
CREATE INDEX IF NOT EXISTS idx_completed_lesson_completed_at ON completed_lesson(completed_at);
CREATE INDEX IF NOT EXISTS idx_app_user_current_lesson ON app_user(current_lesson_id);

-- 5. Add function to mark lesson as complete
CREATE OR REPLACE FUNCTION complete_lesson(
  p_user_id UUID,
  p_lesson_id UUID,
  p_questions_correct INT
) RETURNS VOID AS $$
DECLARE
  v_xp_earned INT;
BEGIN
  -- Calculate XP: 10 per correct answer
  v_xp_earned := p_questions_correct * 10;

  -- Insert completion record
  INSERT INTO completed_lesson (
    user_id,
    lesson_id,
    questions_correct,
    total_questions,
    xp_earned
  ) VALUES (
    p_user_id,
    p_lesson_id,
    p_questions_correct,
    3, -- Always 3 questions per lesson
    v_xp_earned
  ) ON CONFLICT (user_id, lesson_id) DO UPDATE SET
    questions_correct = p_questions_correct,
    xp_earned = v_xp_earned,
    completed_at = NOW();

  -- Update user's XP
  UPDATE app_user
  SET xp = xp + v_xp_earned
  WHERE id = p_user_id;

  -- Clear current lesson
  UPDATE app_user
  SET current_lesson_id = NULL
  WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- 6. Add view for user progress stats
CREATE OR REPLACE VIEW user_progress_stats AS
SELECT
  u.id AS user_id,
  u.display_name,
  u.xp,
  u.current_streak,
  u.longest_streak,
  COUNT(DISTINCT cl.id) AS lessons_completed,
  SUM(cl.questions_correct) AS total_questions_correct,
  SUM(cl.total_questions) AS total_questions_attempted,
  CASE
    WHEN SUM(cl.total_questions) > 0
    THEN ROUND((SUM(cl.questions_correct)::numeric / SUM(cl.total_questions)) * 100, 1)
    ELSE 0
  END AS accuracy_percentage
FROM app_user u
LEFT JOIN completed_lesson cl ON u.id = cl.user_id
GROUP BY u.id, u.display_name, u.xp, u.current_streak, u.longest_streak;

COMMENT ON TABLE completed_lesson IS 'Tracks completed lessons with performance metrics';
COMMENT ON COLUMN app_user.current_lesson_id IS 'The lesson the user is currently working on (NULL if between lessons)';
COMMENT ON FUNCTION complete_lesson IS 'Marks a lesson as complete and awards XP';
COMMENT ON VIEW user_progress_stats IS 'Aggregated user progress statistics for dashboards';
