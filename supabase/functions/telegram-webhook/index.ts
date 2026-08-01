/**
 * Telegram Webhook for DailyCommit Bot
 * Handles incoming updates, question delivery, answer validation, XP tracking
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";

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
      name: firstName,
      total_xp: 0,
      current_streak: 0,
      longest_streak: 0,
    })
    .select()
    .single();

  return newUser;
}

async function getPendingQuestion(userId: string) {
  // Get the most recent lesson that has unanswered questions
  const { data: lessons } = await supabase
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

  if (!lessons || lessons.length === 0) return null;

  // Find first question not yet answered correctly by this user
  for (const lesson of lessons) {
    for (const question of (lesson as any).question) {
      const { data: attempt } = await supabase
        .from("attempt")
        .select("*")
        .eq("user_id", userId)
        .eq("question_id", question.id)
        .eq("correct", true)
        .single();

      if (!attempt) {
        return { lesson, question };
      }
    }
  }

  return null;
}

async function updateStreak(userId: string) {
  const { data: user } = await supabase
    .from("app_user")
    .select("*")
    .eq("id", userId)
    .single();

  if (!user) return;

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

  await supabase
    .from("app_user")
    .update({
      current_streak: newStreak,
      longest_streak: longestStreak,
    })
    .eq("id", userId);
}

async function awardXP(userId: string, amount: number, reason: string) {
  const { data: user } = await supabase
    .from("app_user")
    .select("total_xp")
    .eq("id", userId)
    .single();

  if (!user) return;

  await supabase
    .from("app_user")
    .update({ total_xp: user.total_xp + amount })
    .eq("id", userId);

  console.log(`Awarded ${amount} XP to user ${userId}: ${reason}`);
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
  const { data: existing } = await supabase
    .from("review_schedule")
    .select("*")
    .eq("user_id", userId)
    .eq("question_id", questionId)
    .single();

  const quality = correct ? 4 : 2; // Simplified quality rating
  const easiness = existing?.easiness_factor || 2.5;
  const interval = existing?.interval_days || 0;

  const { newEasiness, newInterval, nextReview } = calculateNextReview(
    easiness,
    interval,
    quality
  );

  await supabase.from("review_schedule").upsert({
    user_id: userId,
    question_id: questionId,
    next_review_date: nextReview.toISOString(),
    interval_days: newInterval,
    easiness_factor: newEasiness,
    repetitions: (existing?.repetitions || 0) + 1,
  });
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
  return {
    inline_keyboard: [
      [{ text: "✏️ Type your answer", callback_data: `ans_${question.id}_text` }],
      [{ text: "🔍 Show answer", callback_data: `ans_${question.id}_reveal` }],
    ],
  };
}

async function sendNextQuestion(chatId: number, userId: string) {
  const pending = await getPendingQuestion(userId);

  if (!pending) {
    await sendMessage(
      chatId,
      "🎉 *Amazing work!*\n\nYou've completed all available questions.\n\nNew lessons arrive daily at 8:00 AM UTC. See you tomorrow! 💪"
    );
    return;
  }

  const { lesson, question } = pending;

  const questionText = `📝 *Question ${question.difficulty}/5*\n\n${question.prompt}`;

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
  // Parse callback data: ans_<question_id>_<answer>
  const parts = data.split("_");
  if (parts.length < 3) return;

  const questionId = parts[1];
  const answer = parts.slice(2).join("_");

  // Get question details
  const { data: question } = await supabase
    .from("question")
    .select("*")
    .eq("id", questionId)
    .single();

  if (!question) {
    await answerCallbackQuery(callbackQueryId, "Question not found", true);
    return;
  }

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
      user_answer: "revealed",
      correct: false,
    });

    await scheduleReview(userId, questionId, false);

    setTimeout(() => sendNextQuestion(chatId, userId), 2000);
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

  // Validate answer
  const correct = answer.toLowerCase() === question.correct_answer.toLowerCase();

  // Record attempt
  await supabase.from("attempt").insert({
    user_id: userId,
    question_id: questionId,
    user_answer: answer,
    correct,
  });

  // Update spaced repetition
  await scheduleReview(userId, questionId, correct);

  // Award XP
  if (correct) {
    await awardXP(userId, 10, "Correct answer");
    await updateStreak(userId);
    await answerCallbackQuery(callbackQueryId, "✅ Correct! +10 XP");
  } else {
    await answerCallbackQuery(callbackQueryId, "❌ Incorrect. Try again!");
  }

  // Update message with feedback
  const feedbackEmoji = correct ? "✅" : "❌";
  const feedbackText = correct ? "Correct!" : "Incorrect";

  await editMessage(
    chatId,
    messageId,
    `📝 *Question*\n\n${question.prompt}\n\n${feedbackEmoji} *${feedbackText}*\n\n💡 *Explanation:*\n${question.explanation}`,
    null
  );

  // Send next question after delay
  setTimeout(() => sendNextQuestion(chatId, userId), 3000);
}

// ============================================================================
// Command Handlers
// ============================================================================

async function handleStart(chatId: number, userId: string, firstName: string) {
  await sendMessage(
    chatId,
    `👋 *Welcome to DailyCommit, ${firstName}!*\n\nI'll help you level up your QA skills with daily micro-lessons.\n\n📚 Use /learn to start today's lesson\n📊 Use /stats to see your progress\n\nLet's get started! 💪`
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
  const correctAttempts = attempts?.filter((a) => a.correct).length || 0;
  const accuracy = totalAttempts > 0 ? Math.round((correctAttempts / totalAttempts) * 100) : 0;

  const statsText = `📊 *Your Progress*\n\n` +
    `🎯 Total XP: ${user.total_xp}\n` +
    `🔥 Current Streak: ${user.current_streak} days\n` +
    `🏆 Longest Streak: ${user.longest_streak} days\n\n` +
    `📝 Questions Answered: ${totalAttempts}\n` +
    `✅ Correct: ${correctAttempts}\n` +
    `📈 Accuracy: ${accuracy}%\n\n` +
    `Keep it up! 💪`;

  await sendMessage(chatId, statsText);
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
      }

      return new Response("OK", { status: 200 });
    }

    return new Response("OK", { status: 200 });
  } catch (error) {
    console.error("Webhook error:", error);
    return new Response("Error", { status: 500 });
  }
});
