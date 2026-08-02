/**
 * Telegram Webhook for DailyCommit Bot
 * Handles incoming updates, question delivery, answer validation, XP tracking
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";
import { getPendingQuestion } from "./lesson-progression.ts";

const TELEGRAM_BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const TELEGRAM_API = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}`;

const supabase = createClient(
  Deno.env.get("DB_URL")!,
  Deno.env.get("DB_SERVICE_KEY")!
);

interface TelegramUpdate {
  update_id: number;
  message?: {
    message_id: number;
    from: { id: number; first_name: string; username?: string };
    chat: { id: number };
    text?: string;
  };
  callback_query?: {
    id: string;
    from: { id: number; first_name: string };
    message: { message_id: number; chat: { id: number } };
    data: string;
  };
}

// ============================================================================
// Telegram API Helpers
// ============================================================================

async function sendMessage(
  chatId: number,
  text: string,
  replyMarkup?: any
): Promise<any> {
  const response = await fetch(`${TELEGRAM_API}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "Markdown",
      reply_markup: replyMarkup,
    }),
  });
  return response.json();
}

async function editMessage(
  chatId: number,
  messageId: number,
  text: string,
  replyMarkup?: any
): Promise<any> {
  const response = await fetch(`${TELEGRAM_API}/editMessageText`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      message_id: messageId,
      text,
      parse_mode: "Markdown",
      reply_markup: replyMarkup,
    }),
  });
  return response.json();
}

async function answerCallbackQuery(
  callbackQueryId: string,
  text: string,
  showAlert = false
): Promise<void> {
  await fetch(`${TELEGRAM_API}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      callback_query_id: callbackQueryId,
      text,
      show_alert: showAlert,
    }),
  });
}

// ============================================================================
// Database Helpers
// ============================================================================

async function getOrCreateUser(telegramUserId: number, firstName: string) {
  const { data: existing } = await supabase
    .from("app_user")
    .select("*")
    .eq("telegram_user_id", telegramUserId)
    .single();

  if (existing) return existing;

  const { data: newUser } = await supabase
    .from("app_user")
    .insert({
      telegram_user_id: telegramUserId,
      display_name: firstName,
      xp: 0,
      current_streak: 0,
      longest_streak: 0,
    })
    .select()
    .single();

  return newUser;
}

// OLD FUNCTION - REPLACED BY lesson-progression.ts
async function getPendingQuestionOLD(userId: string, allowRepeat = false) {
  // Get the most recent lesson that has unanswered questions
  const { data: lessons, error: lessonsError } = await supabase
    .from("lesson")
    .select(`
      id,
      title,
      lesson_date,
      question!inner (
        id,
        type,
        prompt,
        options,
        correct_answer,
        explanation,
        concept_tag,
        difficulty
      )
    `)
    .order("lesson_date", { ascending: false })
    .limit(10);

  if (lessonsError) {
    console.error("[ERROR] Failed to fetch lessons:", lessonsError);
    return null;
  }

  if (!lessons || lessons.length === 0) {
    console.log("[DEBUG] No lessons found in database");
    return null;
  }

  console.log(`[DEBUG] Found ${lessons.length} lessons, checking for unanswered questions (allowRepeat=${allowRepeat})`);

  // First, try to find questions not yet attempted
  for (const lesson of lessons) {
    for (const question of (lesson as any).question) {
      // Check if user has already attempted this question
      const { data: attempts, error: attemptError } = await supabase
        .from("attempt")
        .select("*")
        .eq("user_id", userId)
        .eq("question_id", question.id);

      if (attemptError) {
        console.error(`[ERROR] Failed to check attempts for question ${question.id}:`, attemptError);
        continue; // Skip this question on error
      }

      const hasAttempted = attempts && attempts.length > 0;
      const hasCorrectAttempt = attempts && attempts.some(a => a.is_correct);

      console.log(`[DEBUG] Question ${question.id}: ${hasAttempted ? (hasCorrectAttempt ? 'CORRECT' : 'ATTEMPTED') : 'NEW'} (${attempts?.length || 0} total attempts)`);

      // Return first question that hasn't been attempted yet
      if (!hasAttempted) {
        console.log(`[DEBUG] Returning new question: ${question.id}`);
        return { lesson, question, isPractice: false };
      }
    }
  }

  // If allowRepeat is true and no pending questions, return RANDOM question for practice
  if (allowRepeat && lessons.length > 0) {
    // Collect ALL questions from ALL lessons
    const allQuestions: any[] = [];
    for (const lesson of lessons) {
      const questions = (lesson as any).question || [];
      for (const question of questions) {
        allQuestions.push({ lesson, question });
      }
    }

    if (allQuestions.length > 0) {
      // Pick a RANDOM question instead of always the first one
      const randomIndex = Math.floor(Math.random() * allQuestions.length);
      const { lesson, question } = allQuestions[randomIndex];
      console.log(`[DEBUG] All questions answered! Returning RANDOM question for practice: ${question.id} (${randomIndex + 1}/${allQuestions.length})`);
      return { lesson, question, isPractice: true };
    }
  }

  console.log("[DEBUG] No pending questions found - all answered!");
  return null;
}

async function updateStreak(userId: string) {
  const { data: user, error: userError } = await supabase
    .from("app_user")
    .select("*")
    .eq("id", userId)
    .single();

  if (userError || !user) {
    console.error(`[ERROR] Failed to get user for streak update:`, userError);
    return;
  }

  const today = new Date().toISOString().split("T")[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];

  const { data: todayAttempts } = await supabase
    .from("attempt")
    .select("*")
    .eq("user_id", userId)
    .gte("created_at", `${today}T00:00:00`)
    .limit(1);

  if (todayAttempts && todayAttempts.length > 0) {
    // Already counted today
    console.log(`[DEBUG] Streak already counted for today for user ${userId}`);
    return;
  }

  const { data: yesterdayAttempts } = await supabase
    .from("attempt")
    .select("*")
    .eq("user_id", userId)
    .gte("created_at", `${yesterday}T00:00:00`)
    .lt("created_at", `${today}T00:00:00`)
    .limit(1);

  let newStreak = 1;
  if (yesterdayAttempts && yesterdayAttempts.length > 0) {
    newStreak = user.current_streak + 1;
  }

  const longestStreak = Math.max(user.longest_streak, newStreak);

  const { error: updateError } = await supabase
    .from("app_user")
    .update({
      current_streak: newStreak,
      longest_streak: longestStreak,
    })
    .eq("id", userId);

  if (updateError) {
    console.error(`[ERROR] Failed to update streak:`, updateError);
    return;
  }

  console.log(`[DEBUG] Streak updated for user ${userId}: ${newStreak} days (longest: ${longestStreak})`);
}

async function awardXP(userId: string, amount: number, reason: string) {
  const { data: user, error: selectError } = await supabase
    .from("app_user")
    .select("xp")
    .eq("id", userId)
    .single();

  if (selectError || !user) {
    console.error(`[ERROR] Failed to get user for XP award:`, selectError);
    return;
  }

  const newXP = user.xp + amount;

  const { error: updateError } = await supabase
    .from("app_user")
    .update({ xp: newXP })
    .eq("id", userId);

  if (updateError) {
    console.error(`[ERROR] Failed to update XP:`, updateError);
    return;
  }

  console.log(`[DEBUG] Awarded ${amount} XP to user ${userId}: ${reason} (new total: ${newXP})`);
}

// ============================================================================
// Spaced Repetition (SM-2 Algorithm)
// ============================================================================

function calculateNextReview(
  easiness: number,
  interval: number,
  quality: number
): { newEasiness: number; newInterval: number; nextReview: Date } {
  // SM-2 algorithm
  let newEasiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  if (newEasiness < 1.3) newEasiness = 1.3;

  let newInterval: number;
  if (quality < 3) {
    newInterval = 1; // Reset interval if answer was poor
  } else {
    if (interval === 0) {
      newInterval = 1;
    } else if (interval === 1) {
      newInterval = 6;
    } else {
      newInterval = Math.round(interval * newEasiness);
    }
  }

  const nextReview = new Date();
  nextReview.setDate(nextReview.getDate() + newInterval);

  return { newEasiness, newInterval, nextReview };
}

async function scheduleReview(
  userId: string,
  questionId: string,
  correct: boolean
) {
  // Get question to find concept_tag
  const { data: question, error: questionError } = await supabase
    .from("question")
    .select("concept_tag")
    .eq("id", questionId)
    .single();

  if (questionError || !question?.concept_tag) {
    console.error(`[ERROR] Failed to get question for review schedule:`, questionError);
    return;
  }

  const conceptTag = question.concept_tag;

  const { data: existing, error: selectError } = await supabase
    .from("review_item")
    .select("*")
    .eq("user_id", userId)
    .eq("concept_tag", conceptTag)
    .maybeSingle();

  if (selectError) {
    console.error(`[ERROR] Failed to get review item:`, selectError);
    return;
  }

  const quality = correct ? 4 : 2; // Simplified quality rating
  const easiness = existing?.ease || 2.5;
  const interval = existing?.interval_days || 0;

  const { newEasiness, newInterval, nextReview } = calculateNextReview(
    easiness,
    interval,
    quality
  );

  const today = new Date().toISOString().split('T')[0];

  const { error: upsertError } = await supabase.from("review_item").upsert({
    user_id: userId,
    concept_tag: conceptTag,
    due_date: nextReview.toISOString().split('T')[0],
    interval_days: newInterval,
    ease: newEasiness,
    repetitions: (existing?.repetitions || 0) + 1,
    last_reviewed: today,
    last_result: correct ? 'correct' : 'incorrect',
  });

  if (upsertError) {
    console.error(`[ERROR] Failed to upsert review item:`, upsertError);
    return;
  }

  console.log(`[DEBUG] Review scheduled for concept ${conceptTag}: next in ${newInterval} days`);
}

// ============================================================================
// Question Delivery
// ============================================================================

function buildQuestionKeyboard(question: any): any {
  const { type, options } = question;

  if (type === "mcq" && options && options.length === 4) {
    return {
      inline_keyboard: [
        [{ text: options[0], callback_data: `ans_${question.id}_A` }],
        [{ text: options[1], callback_data: `ans_${question.id}_B` }],
        [{ text: options[2], callback_data: `ans_${question.id}_C` }],
        [{ text: options[3], callback_data: `ans_${question.id}_D` }],
      ],
    };
  }

  if (type === "true_false") {
    return {
      inline_keyboard: [
        [
          { text: "True ✓", callback_data: `ans_${question.id}_true` },
          { text: "False ✗", callback_data: `ans_${question.id}_false` },
        ],
      ],
    };
  }

  // For fill_in, predict_output, spot_the_bug, short_answer, scenario
  // Simplified: Just show answer (text input not implemented yet)
  return {
    inline_keyboard: [
      [{ text: "🔍 Show answer", callback_data: `ans_${question.id}_reveal` }],
    ],
  };
}

async function sendNextQuestion(chatId: number, userId: string) {
  const pending = await getPendingQuestion(supabase, userId);

  if (!pending) {
    await sendMessage(
      chatId,
      "📚 *Generating your lesson...*\n\nPlease wait a moment while I create fresh content for you! ⚡"
    );
    return;
  }

  const { lesson, question, questionNumber, totalQuestions, lessonJustCompleted, xpEarned } = pending;

  // If lesson was just completed, show celebration message first
  if (lessonJustCompleted) {
    await sendMessage(
      chatId,
      `🎉 *Lesson Complete!*\n\nYou earned *${xpEarned} XP*!\n\nGreat job! Let's continue with your next lesson...`
    );
    await new Promise(resolve => setTimeout(resolve, 2000)); // Pause 2 seconds
  }

  // Show difficulty level
  const difficultyEmoji = ['⭐', '⭐⭐', '⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐'][question.difficulty - 1] || '⭐';

  // Build question text with progress indicator
  const progressText = questionNumber && totalQuestions
    ? `*Question ${questionNumber}/${totalQuestions}*`
    : `*Question*`;

  let questionText = `📝 ${progressText}\n`;
  questionText += `📚 Lesson: ${lesson.title}\n`;
  questionText += `${difficultyEmoji} Difficulty\n\n`;
  questionText += `${question.prompt}`;

  const keyboard = buildQuestionKeyboard(question);
  await sendMessage(chatId, questionText, keyboard);
}

// ============================================================================
// Answer Validation
// ============================================================================

async function handleAnswer(
  callbackQueryId: string,
  chatId: number,
  messageId: number,
  userId: string,
  data: string
) {
  console.log(`[DEBUG] handleAnswer called: data=${data}, userId=${userId}`);

  // Parse callback data: ans_<question_id>_<answer>
  const parts = data.split("_");
  if (parts.length < 3) {
    console.log(`[ERROR] Invalid callback data format: ${data}`);
    return;
  }

  const questionId = parts[1];
  const answer = parts.slice(2).join("_");
  console.log(`[DEBUG] Parsed: questionId=${questionId}, answer=${answer}`);

  // Get question details
  const { data: question, error } = await supabase
    .from("question")
    .select("*")
    .eq("id", questionId)
    .single();

  if (error || !question) {
    console.log(`[ERROR] Question not found: ${questionId}`, error);
    await answerCallbackQuery(callbackQueryId, "Question not found", true);
    return;
  }

  console.log(`[DEBUG] Question found: type=${question.type}, correct_answer=${question.correct_answer}`);

  // Special handling for reveal
  if (answer === "reveal") {
    await answerCallbackQuery(callbackQueryId, "Answer revealed!");
    await editMessage(
      chatId,
      messageId,
      `📝 *Question*\n\n${question.prompt}\n\n✅ *Answer:* ${question.correct_answer}\n\n💡 *Explanation:*\n${question.explanation}`,
      null
    );

    // Record as incorrect attempt
    await supabase.from("attempt").insert({
      user_id: userId,
      question_id: questionId,
      lesson_id: question.lesson_id,
      user_answer: "revealed",
      is_correct: false,
    });

    await scheduleReview(userId, questionId, false);

    await new Promise(resolve => setTimeout(resolve, 2000));
    await sendNextQuestion(chatId, userId);
    return;
  }

  // Special handling for text input
  if (answer === "text") {
    await answerCallbackQuery(
      callbackQueryId,
      "Type your answer as a message",
      false
    );
    // Store state to expect text answer next
    // TODO: Implement state management for text answers
    return;
  }

  // Validate answer (handle multiple formats)
  let correct = false;
  const userAnswer = answer.toLowerCase().trim();
  const correctAnswer = question.correct_answer.toLowerCase().trim();

  console.log(`[DEBUG] Validating: userAnswer='${userAnswer}' vs correctAnswer='${correctAnswer}'`);

  if (question.type === "mcq") {
    // For MCQ, answer could be:
    // 1. Just a letter: "A", "B", "C", "D"
    // 2. Full option text: "Hash table"
    // 3. Option with letter prefix: "A. Hash table"

    // Direct match (handles case 1)
    if (userAnswer === correctAnswer) {
      correct = true;
    }
    // Check if correct_answer is in options array and user selected that option
    else if (question.options && Array.isArray(question.options)) {
      // Find the index of the correct answer in options
      const correctIndex = question.options.findIndex((opt: string) => {
        const optLower = opt.toLowerCase().trim();
        // Match if:
        // 1. Exact match (e.g., "hash table" == "hash table")
        // 2. Option starts with letter prefix (e.g., "a. hash table" with correct_answer="a")
        // 3. Correct answer is full text contained in option (e.g., "hash table" in "a. hash table")
        //    but only if correct_answer is more than 1 char (avoid "b" matching "hash table")
        return optLower === correctAnswer ||
               optLower.startsWith(`${correctAnswer}. `) ||
               (correctAnswer.length > 1 && optLower.includes(correctAnswer));
      });

      // Map user's letter (A/B/C/D) to index (0/1/2/3)
      const letterToIndex: {[key: string]: number} = { 'a': 0, 'b': 1, 'c': 2, 'd': 3 };
      const userIndex = letterToIndex[userAnswer];

      console.log(`[DEBUG] MCQ check: correctIndex=${correctIndex}, userIndex=${userIndex}`);

      if (correctIndex !== -1 && userIndex !== undefined && correctIndex === userIndex) {
        correct = true;
      }
    }
  } else if (question.type === "true_false") {
    // For true/false, normalize variations
    const normalized = userAnswer.replace(/[✓✗\s]/g, '');
    const correctNormalized = correctAnswer.replace(/[✓✗\s]/g, '');
    correct = normalized === correctNormalized;
  } else {
    // For other types, direct comparison
    correct = userAnswer === correctAnswer;
  }

  console.log(`[DEBUG] Validation result: ${correct}`);

  // Record attempt in database
  const { error: insertError } = await supabase.from("attempt").insert({
    user_id: userId,
    question_id: questionId,
    lesson_id: question.lesson_id,
    user_answer: answer,
    is_correct: correct,
  });

  if (insertError) {
    console.error(`[ERROR] Failed to insert attempt:`, insertError);
    await answerCallbackQuery(callbackQueryId, "⚠️ Database error. Please try again.", true);
    return;
  }

  console.log(`[DEBUG] Attempt recorded: questionId=${questionId}, correct=${correct}`);

  // Update spaced repetition
  await scheduleReview(userId, questionId, correct);

  // Award XP and update streak if correct
  if (correct) {
    await awardXP(userId, 10, "Correct answer");
    await updateStreak(userId);
  }

  // Send callback query response (quick popup)
  const callbackMessage = correct
    ? "✅ Correct! +10 XP"
    : "❌ Incorrect. Try again!";
  await answerCallbackQuery(callbackQueryId, callbackMessage);

  // Update message with detailed feedback
  const feedbackEmoji = correct ? "✅" : "❌";
  const feedbackText = correct ? "**Correct!**" : "**Incorrect**";
  const xpText = correct ? "\n\n🎯 *+10 XP earned!*" : "";

  await editMessage(
    chatId,
    messageId,
    `📝 *Question*\n\n${question.prompt}\n\n${feedbackEmoji} ${feedbackText}${xpText}\n\n💡 *Explanation:*\n${question.explanation}\n\n⏳ _Loading next question..._`,
    null
  );

  // Send next question after 3 seconds (giving user time to read explanation)
  await new Promise(resolve => setTimeout(resolve, 3000));

  console.log(`[DEBUG] About to fetch next question for user ${userId}`);
  await sendNextQuestion(chatId, userId);
}

// ============================================================================
// Command Handlers
// ============================================================================

async function handleStart(chatId: number, userId: string, firstName: string) {
  await sendMessage(
    chatId,
    `👋 *Welcome to DailyCommit, ${firstName}!*\n\n` +
    `I'll help you level up your QA skills with daily micro-lessons.\n\n` +
    `*Available Commands:*\n` +
    `📚 /learn - Practice with questions\n` +
    `📊 /stats - View your progress\n` +
    `⏰ /settime - Set notification time (e.g., /settime 14:00 Asia/Dhaka)\n` +
    `🔔 /notifications - Toggle daily reminders (on/off)\n\n` +
    `Let's get started! 💪`
  );
}

async function handleLearn(chatId: number, userId: string) {
  await sendNextQuestion(chatId, userId);
}

async function handleStats(chatId: number, userId: string) {
  const { data: user } = await supabase
    .from("app_user")
    .select("*")
    .eq("id", userId)
    .single();

  if (!user) return;

  const { data: attempts } = await supabase
    .from("attempt")
    .select("*")
    .eq("user_id", userId);

  const totalAttempts = attempts?.length || 0;
  const correctAttempts = attempts?.filter((a) => a.is_correct).length || 0;
  const accuracy = totalAttempts > 0 ? Math.round((correctAttempts / totalAttempts) * 100) : 0;

  const statsText = `📊 *Your Progress*\n\n` +
    `🎯 Total XP: ${user.xp}\n` +
    `🔥 Current Streak: ${user.current_streak} days\n` +
    `🏆 Longest Streak: ${user.longest_streak} days\n\n` +
    `📝 Questions Answered: ${totalAttempts}\n` +
    `✅ Correct: ${correctAttempts}\n` +
    `📈 Accuracy: ${accuracy}%\n\n` +
    `Keep it up! 💪`;

  await sendMessage(chatId, statsText);
}

async function handleSetTime(chatId: number, userId: string, text: string) {
  // Parse: /settime 14:00 Asia/Dhaka
  const parts = text.split(" ").filter(p => p.length > 0);

  if (parts.length < 3) {
    await sendMessage(
      chatId,
      `⏰ *Set Your Daily Notification Time*\n\n` +
      `Usage: \`/settime HH:MM TIMEZONE\`\n\n` +
      `Examples:\n` +
      `• \`/settime 14:00 Asia/Dhaka\`\n` +
      `• \`/settime 09:00 America/New_York\`\n` +
      `• \`/settime 18:30 Europe/London\`\n\n` +
      `[View all timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)`
    );
    return;
  }

  const time = parts[1]; // e.g., "14:00"
  const timezone = parts[2]; // e.g., "Asia/Dhaka"

  // Validate time format (HH:MM)
  if (!/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(time)) {
    await sendMessage(chatId, `❌ Invalid time format. Use HH:MM (e.g., 14:00)`);
    return;
  }

  // Update user preferences
  const { error } = await supabase
    .from("app_user")
    .update({
      preferred_notification_time: time,
      timezone: timezone,
      notifications_enabled: true,
    })
    .eq("id", userId);

  if (error) {
    console.error("Error updating notification settings:", error);
    await sendMessage(chatId, `❌ Failed to save settings. Please try again.`);
    return;
  }

  await sendMessage(
    chatId,
    `✅ *Notification time set!*\n\n` +
    `🕐 Time: ${time}\n` +
    `🌍 Timezone: ${timezone}\n\n` +
    `You'll receive a daily reminder at this time.\n\n` +
    `Use \`/notifications off\` to disable.`
  );
}

async function handleNotifications(chatId: number, userId: string, text: string) {
  const parts = text.toLowerCase().split(" ");
  const command = parts[1]; // "on" or "off"

  if (command !== "on" && command !== "off") {
    await sendMessage(
      chatId,
      `🔔 *Notification Settings*\n\n` +
      `Usage:\n` +
      `• \`/notifications on\` - Enable daily reminders\n` +
      `• \`/notifications off\` - Disable daily reminders\n\n` +
      `Set your preferred time with \`/settime\``
    );
    return;
  }

  const enabled = command === "on";

  const { error } = await supabase
    .from("app_user")
    .update({ notifications_enabled: enabled })
    .eq("id", userId);

  if (error) {
    await sendMessage(chatId, `❌ Failed to update settings. Please try again.`);
    return;
  }

  if (enabled) {
    const { data: user } = await supabase
      .from("app_user")
      .select("preferred_notification_time, timezone")
      .eq("id", userId)
      .single();

    await sendMessage(
      chatId,
      `✅ Notifications enabled!\n\n` +
      `You'll receive daily reminders at ${user?.preferred_notification_time || '08:00'} ${user?.timezone || 'UTC'}\n\n` +
      `Change time with \`/settime\``
    );
  } else {
    await sendMessage(chatId, `🔕 Notifications disabled. You can still use /learn anytime!`);
  }
}

// ============================================================================
// Main Handler
// ============================================================================

serve(async (req) => {
  try {
    const update: TelegramUpdate = await req.json();

    // Handle callback queries (button presses)
    if (update.callback_query) {
      const { id, from, message, data } = update.callback_query;
      const user = await getOrCreateUser(from.id, from.first_name);

      if (data.startsWith("ans_")) {
        await handleAnswer(id, message.chat.id, message.message_id, user.id, data);
      }

      return new Response("OK", { status: 200 });
    }

    // Handle text messages
    if (update.message?.text) {
      const { from, chat, text } = update.message;
      const user = await getOrCreateUser(from.id, from.first_name);

      if (text === "/start") {
        await handleStart(chat.id, user.id, from.first_name);
      } else if (text === "/learn") {
        await handleLearn(chat.id, user.id);
      } else if (text === "/stats") {
        await handleStats(chat.id, user.id);
      } else if (text.startsWith("/settime")) {
        await handleSetTime(chat.id, user.id, text);
      } else if (text.startsWith("/notifications")) {
        await handleNotifications(chat.id, user.id, text);
      }

      return new Response("OK", { status: 200 });
    }

    return new Response("OK", { status: 200 });
  } catch (error) {
    console.error("Webhook error:", error);
    return new Response("Error", { status: 500 });
  }
});
