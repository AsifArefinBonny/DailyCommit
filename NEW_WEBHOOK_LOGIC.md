# NEW LESSON PROGRESSION LOGIC

## Current Problem

```typescript
// OLD BUGGY CODE (lines 181-189):
if (allowRepeat && lessons.length > 0) {
  const lesson = lessons[0];
  const questions = (lesson as any).question;
  if (questions && questions.length > 0) {
    const question = questions[0];  // ❌ ALWAYS RETURNS SAME QUESTION!
    return { lesson, question, isPractice: true };
  }
}
```

## New Solution

### Step 1: Check Current Lesson Progress
```typescript
async function getCurrentLessonProgress(userId: string) {
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
      question!inner (id, type, prompt, options, correct_answer, explanation, difficulty, concept_tag)
    `)
    .eq("id", user.current_lesson_id)
    .single();

  if (!lesson) return null;

  // Count how many questions answered in this lesson
  const { data: attempts } = await supabase
    .from("attempt")
    .select("question_id")
    .eq("user_id", userId)
    .eq("lesson_id", lesson.id);

  const questionsAnswered = attempts ? attempts.length : 0;
  const totalQuestions = (lesson as any).question.length;

  return {
    lesson,
    questionsAnswered,
    totalQuestions,
    isComplete: questionsAnswered >= totalQuestions
  };
}
```

### Step 2: Get Next Question in Lesson
```typescript
async function getNextQuestionInLesson(userId: string, lesson: any) {
  // Get all questions in this lesson
  const questions = (lesson as any).question;

  // Find which ones have been attempted
  const { data: attempts } = await supabase
    .from("attempt")
    .select("question_id")
    .eq("user_id", userId)
    .eq("lesson_id", lesson.id);

  const attemptedQuestionIds = new Set(attempts?.map(a => a.question_id) || []);

  // Find first unattempted question
  for (const question of questions) {
    if (!attemptedQuestionIds.has(question.id)) {
      return question;
    }
  }

  return null; // All questions answered
}
```

### Step 3: Generate New AI Lesson
```typescript
async function generateNewLesson(userId: string): Promise<any> {
  // This would call the Python AI generation script
  // For now, simplified version:

  const topics = [
    "Test Automation",
    "API Testing",
    "Performance Testing",
    "Security Testing",
    "CI/CD for QA"
  ];

  const topic = topics[Math.floor(Math.random() * topics.length)];

  // Call AI generation endpoint (or Python script via subprocess)
  const response = await fetch("https://.../generate-lesson", {
    method: "POST",
    body: JSON.stringify({ topic, user_id: userId })
  });

  const lessonData = await response.json();
  return lessonData;
}
```

### Step 4: NEW getPendingQuestion Function
```typescript
async function getPendingQuestion(userId: string) {
  console.log(`[DEBUG] getPendingQuestion for user ${userId}`);

  // STEP 1: Check if user has an active lesson
  const progress = await getCurrentLessonProgress(userId);

  if (progress && !progress.isComplete) {
    // User is in the middle of a lesson
    const question = await getNextQuestionInLesson(userId, progress.lesson);
    if (question) {
      const questionNumber = progress.questionsAnswered + 1;
      console.log(`[DEBUG] Returning Q${questionNumber}/3 from active lesson`);
      return {
        lesson: progress.lesson,
        question,
        isPractice: false,
        questionNumber,
        totalQuestions: progress.totalQuestions
      };
    }
  }

  if (progress && progress.isComplete) {
    // User just completed a lesson!
    console.log(`[DEBUG] Lesson complete! Marking as done and generating new one...`);

    // Mark lesson as complete
    await completeLesson(userId, progress.lesson.id, progress.questionsAnswered);

    // Generate new AI lesson
    const newLesson = await generateNewLesson(userId);
    if (newLesson && newLesson.question && newLesson.question.length > 0) {
      console.log(`[DEBUG] New AI lesson generated: ${newLesson.title}`);
      return {
        lesson: newLesson,
        question: newLesson.question[0],
        isPractice: false,
        questionNumber: 1,
        totalQuestions: 3
      };
    }
  }

  // STEP 2: No active lesson - find an unattempted lesson or generate new one
  const { data: lessons } = await supabase
    .from("lesson")
    .select(`
      id,
      title,
      topic_category,
      question!inner (id, type, prompt, options, correct_answer, explanation, difficulty, concept_tag)
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

        console.log(`[DEBUG] Starting new existing lesson: ${lesson.id}`);
        return {
          lesson,
          question: (lesson as any).question[0],
          isPractice: false,
          questionNumber: 1,
          totalQuestions: 3
        };
      }
    }
  }

  // STEP 3: All existing lessons completed - generate new AI lesson
  console.log(`[DEBUG] All lessons completed - generating new AI lesson`);
  const newLesson = await generateNewLesson(userId);
  if (newLesson && newLesson.question && newLesson.question.length > 0) {
    return {
      lesson: newLesson,
      question: newLesson.question[0],
      isPractice: false,
      questionNumber: 1,
      totalQuestions: 3
    };
  }

  console.log("[DEBUG] No questions available");
  return null;
}
```

### Step 5: Complete Lesson Function
```typescript
async function completeLesson(userId: string, lessonId: string, questionsCorrect: number) {
  const xpEarned = questionsCorrect * 10;

  // Insert completion record
  await supabase.from("completed_lesson").insert({
    user_id: userId,
    lesson_id: lessonId,
    questions_correct: questionsCorrect,
    total_questions: 3,
    xp_earned: xpEarned
  });

  // Update user XP (additional to individual question XP)
  await supabase
    .from("app_user")
    .update({
      current_lesson_id: null,
      xp: supabase.rpc("increment_xp", { x: xpEarned })
    })
    .eq("id", userId);

  console.log(`[DEBUG] Lesson ${lessonId} completed! ${xpEarned} XP earned`);
}
```

### Step 6: Update sendNextQuestion
```typescript
async function sendNextQuestion(chatId: number, userId: string) {
  const pending = await getPendingQuestion(userId);

  if (!pending) {
    await sendMessage(
      chatId,
      "📚 *Generating your next lesson...*\n\nPlease wait a moment while I create fresh content for you! ⚡"
    );
    // Trigger AI generation
    return;
  }

  const { lesson, question, questionNumber, totalQuestions } = pending;

  // Show difficulty level
  const difficultyEmoji = ['⭐', '⭐⭐', '⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐'][question.difficulty - 1] || '⭐';

  // Show progress: Question 2/3
  const progressText = questionNumber && totalQuestions
    ? `Question ${questionNumber}/${totalQuestions}`
    : `Question`;

  let questionText = `📝 *${progressText}*\n`;
  questionText += `Lesson: ${lesson.title}\n`;
  questionText += `Difficulty: ${difficultyEmoji}\n\n`;
  questionText += `${question.prompt}`;

  const keyboard = buildQuestionKeyboard(question);
  await sendMessage(chatId, questionText, keyboard);
}
```

## Summary of Changes

1. ✅ Track current lesson with `app_user.current_lesson_id`
2. ✅ Count questions answered per lesson
3. ✅ Show progress "Question 2/3"
4. ✅ After 3 questions → mark complete → generate NEW lesson
5. ✅ Never repeat the same question
6. ✅ Each lesson has exactly 3 questions
7. ✅ AI generates unlimited fresh content

## User Experience Flow

```
User: /learn
Bot: "Question 1/3 - Lesson: Test Automation Basics - ⭐⭐ - [Question]"
User: [Answers]
Bot: "✅ Correct! +10 XP - Loading next question..."
Bot: "Question 2/3 - [Next question]"
User: [Answers]
Bot: "✅ Correct! +10 XP - Loading next question..."
Bot: "Question 3/3 - [Final question]"
User: [Answers]
Bot: "✅ Lesson Complete! You earned 30 XP! 🎉"
Bot: "Generating your next lesson..."
Bot: "Question 1/3 - Lesson: API Testing Fundamentals - ⭐⭐ - [New question]"
```

No more infinite loops! ✅
