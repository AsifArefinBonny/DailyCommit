/**
 * Lesson Progression Logic
 * Handles 3-question-per-lesson progression system
 */

import { generateAILesson } from "./ai-generation.ts";

export async function getCurrentLessonProgress(supabase: any, userId: string) {
  // Check if user has a current lesson they're working on
  const { data: user } = await supabase
    .from("app_user")
    .select("current_lesson_id")
    .eq("id", userId)
    .single();

  if (!user || !user.current_lesson_id) {
    return null; // No active lesson
  }

  // Get the current lesson with all its questions
  const { data: lesson } = await supabase
    .from("lesson")
    .select(`
      id,
      title,
      topic_category,
      question!inner (
        id,
        type,
        prompt,
        options,
        correct_answer,
        explanation,
        difficulty,
        concept_tag
      )
    `)
    .eq("id", user.current_lesson_id)
    .single();

  if (!lesson) return null;

  // Count how many questions answered in this lesson
  const { data: attempts } = await supabase
    .from("attempt")
    .select("question_id, is_correct")
    .eq("user_id", userId)
    .eq("lesson_id", lesson.id);

  const questionsAnswered = attempts ? attempts.length : 0;
  const totalQuestions = (lesson as any).question.length;
  const correctAnswers = attempts ? attempts.filter((a) => a.is_correct).length : 0;

  return {
    lesson,
    questionsAnswered,
    totalQuestions,
    correctAnswers,
    isComplete: questionsAnswered >= totalQuestions,
  };
}

export async function getNextQuestionInLesson(
  supabase: any,
  userId: string,
  lesson: any
) {
  const questions = (lesson as any).question;

  // Get all questions in this lesson that have been attempted
  const { data: attempts } = await supabase
    .from("attempt")
    .select("question_id")
    .eq("user_id", userId)
    .eq("lesson_id", lesson.id);

  const attemptedQuestionIds = new Set(
    attempts?.map((a) => a.question_id) || []
  );

  // Find first unattempted question
  for (const question of questions) {
    if (!attemptedQuestionIds.has(question.id)) {
      return question;
    }
  }

  return null; // All questions answered
}

export async function completeLesson(
  supabase: any,
  userId: string,
  lessonId: string
) {
  console.log(`[LESSON] Completing lesson ${lessonId} for user ${userId}`);

  // Get completion stats
  const { data: attempts } = await supabase
    .from("attempt")
    .select("is_correct")
    .eq("user_id", userId)
    .eq("lesson_id", lessonId);

  const questionsCorrect = attempts
    ? attempts.filter((a) => a.is_correct).length
    : 0;
  const xpEarned = questionsCorrect * 10;

  // Insert completion record
  await supabase.from("completed_lesson").insert({
    user_id: userId,
    lesson_id: lessonId,
    questions_correct: questionsCorrect,
    total_questions: 3,
    xp_earned: xpEarned,
  });

  // Clear current lesson
  await supabase
    .from("app_user")
    .update({ current_lesson_id: null })
    .eq("id", userId);

  console.log(`[LESSON] Lesson complete! ${xpEarned} XP earned`);
  return xpEarned;
}

export async function getPendingQuestion(supabase: any, userId: string) {
  console.log(`[PROGRESSION] Getting question for user ${userId}`);

  // STEP 1: Check if user has an active lesson
  const progress = await getCurrentLessonProgress(supabase, userId);

  if (progress && !progress.isComplete) {
    // User is in the middle of a lesson
    const question = await getNextQuestionInLesson(
      supabase,
      userId,
      progress.lesson
    );
    if (question) {
      const questionNumber = progress.questionsAnswered + 1;
      console.log(
        `[PROGRESSION] Returning Q${questionNumber}/3 from active lesson`
      );
      return {
        lesson: progress.lesson,
        question,
        isPractice: false,
        questionNumber,
        totalQuestions: progress.totalQuestions,
      };
    }
  }

  if (progress && progress.isComplete) {
    // User just completed a lesson!
    console.log(`[PROGRESSION] Lesson complete! Generating new one...`);

    const xpEarned = await completeLesson(
      supabase,
      userId,
      progress.lesson.id
    );

    // Generate new AI lesson
    const newLessonId = await generateAILesson(supabase, userId);

    if (newLessonId) {
      // Get the new lesson
      const { data: newLesson } = await supabase
        .from("lesson")
        .select(`
          id,
          title,
          topic_category,
          question!inner (
            id,
            type,
            prompt,
            options,
            correct_answer,
            explanation,
            difficulty,
            concept_tag
          )
        `)
        .eq("id", newLessonId)
        .single();

      if (newLesson && (newLesson as any).question.length > 0) {
        console.log(`[PROGRESSION] New AI lesson generated: ${newLesson.title}`);
        return {
          lesson: newLesson,
          question: (newLesson as any).question[0],
          isPractice: false,
          questionNumber: 1,
          totalQuestions: 3,
          lessonJustCompleted: true,
          xpEarned,
        };
      }
    }
  }

  // STEP 2: No active lesson - find an unattempted lesson or generate new one
  const { data: lessons } = await supabase
    .from("lesson")
    .select(`
      id,
      title,
      topic_category,
      question!inner (
        id,
        type,
        prompt,
        options,
        correct_answer,
        explanation,
        difficulty,
        concept_tag
      )
    `)
    .order("created_at", { ascending: false })
    .limit(10);

  if (lessons) {
    // Find a lesson user hasn't started
    for (const lesson of lessons) {
      const { data: completedCheck } = await supabase
        .from("completed_lesson")
        .select("id")
        .eq("user_id", userId)
        .eq("lesson_id", lesson.id)
        .maybeSingle();

      if (!completedCheck) {
        // This lesson hasn't been completed - start it
        await supabase
          .from("app_user")
          .update({ current_lesson_id: lesson.id })
          .eq("id", userId);

        console.log(`[PROGRESSION] Starting existing lesson: ${lesson.id}`);
        return {
          lesson,
          question: (lesson as any).question[0],
          isPractice: false,
          questionNumber: 1,
          totalQuestions: 3,
        };
      }
    }
  }

  // STEP 3: All existing lessons completed - generate new AI lesson
  console.log(`[PROGRESSION] All lessons completed - generating new AI lesson`);
  const newLessonId = await generateAILesson(supabase, userId);

  if (newLessonId) {
    const { data: newLesson } = await supabase
      .from("lesson")
      .select(`
        id,
        title,
        topic_category,
        question!inner (
          id,
          type,
          prompt,
          options,
          correct_answer,
          explanation,
          difficulty,
          concept_tag
        )
      `)
      .eq("id", newLessonId)
      .single();

    if (newLesson && (newLesson as any).question.length > 0) {
      return {
        lesson: newLesson,
        question: (newLesson as any).question[0],
        isPractice: false,
        questionNumber: 1,
        totalQuestions: 3,
      };
    }
  }

  console.log("[PROGRESSION] No questions available");
  return null;
}
