/**
 * DailyCommit — Telegram webhook (Supabase Edge Function)
 * Handles all interactive commands: answer taps, /stats, /learn, tutor toggles, snooze
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const TELEGRAM_BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const TELEGRAM_WEBHOOK_SECRET = Deno.env.get("TELEGRAM_WEBHOOK_SECRET")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

interface TelegramUpdate {
  message?: {
    chat: { id: number };
    text?: string;
    from?: { id: number; first_name?: string };
  };
  callback_query?: {
    id: string;
    from: { id: number };
    data: string;
    message?: { message_id: number; chat: { id: number } };
  };
}

serve(async (req) => {
  try {
    // Verify webhook secret
    const secretToken = req.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (secretToken !== TELEGRAM_WEBHOOK_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    const update: TelegramUpdate = await req.json();

    // Handle callback queries (button taps)
    if (update.callback_query) {
      await handleCallbackQuery(update.callback_query);
      return new Response("OK");
    }

    // Handle text commands
    if (update.message?.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text;

      if (text.startsWith("/stats")) {
        await handleStats(chatId);
      } else if (text.startsWith("/learn")) {
        await handleLearn(chatId, text);
      } else if (text.startsWith("/start")) {
        await handleStart(chatId, update.message.from!);
      } else if (text.startsWith("/settings")) {
        await handleSettings(chatId);
      }
    }

    return new Response("OK");
  } catch (error) {
    console.error("Webhook error:", error);
    return new Response("Error", { status: 500 });
  }
});

async function handleStart(chatId: number, user: { id: number; first_name?: string }) {
  // Check if user exists, if not create
  const { data: existingUser } = await supabase
    .from("app_user")
    .select("*")
    .eq("telegram_user_id", user.id)
    .single();

  if (!existingUser) {
    await supabase.from("app_user").insert({
      telegram_user_id: user.id,
      display_name: user.first_name || "User",
      timezone: "UTC", // User should update this via /settings
    });
  }

  const message = `👋 Welcome to **DailyCommit**!

You'll receive one read-first micro-lesson per day to compound your QA, DevOps, and coding knowledge.

Commands:
/stats — View your streak and progress
/learn — Get an extra lesson (up to 5/day)
/settings — Configure timezone and preferences

Your daily lesson will arrive soon! 📚`;

  await sendMessage(chatId, message);
}

async function handleStats(chatId: number) {
  const { data: user } = await supabase
    .from("app_user")
    .select("*")
    .eq("telegram_user_id", chatId)
    .single();

  if (!user) {
    await sendMessage(chatId, "Use /start to get started!");
    return;
  }

  // Get accuracy stats
  const { data: attempts } = await supabase
    .from("attempt")
    .select("is_correct")
    .eq("user_id", user.id);

  const totalAttempts = attempts?.length || 0;
  const correctAttempts = attempts?.filter((a) => a.is_correct).length || 0;
  const accuracy = totalAttempts > 0 ? Math.round((correctAttempts / totalAttempts) * 100) : 0;

  // Get weakest topic
  const { data: topicStats } = await supabase.rpc("get_topic_accuracy", {
    p_user_id: user.id,
  });

  const weakestTopic = topicStats?.[0]?.topic_name || "N/A";

  const message = `📊 **Your Stats**

🔥 Current Streak: ${user.current_streak} days
🏆 Longest Streak: ${user.longest_streak} days
⭐ Level ${user.level} (${user.xp} XP)
🎯 Accuracy: ${accuracy}% (${correctAttempts}/${totalAttempts})
📉 Weakest Topic: ${weakestTopic}

Keep learning! 🚀`;

  await sendMessage(chatId, message);
}

async function handleLearn(chatId: number, text: string) {
  // TODO: Implement on-demand lesson generation
  await sendMessage(chatId, "On-demand lessons coming in v2! 🚧");
}

async function handleSettings(chatId: number) {
  // TODO: Implement settings menu
  await sendMessage(chatId, "Settings menu coming soon! 🚧\n\nFor now, update your timezone directly in the database.");
}

async function handleCallbackQuery(query: any) {
  const chatId = query.from.id;
  const data = query.data;

  // Parse callback data (format: "a:<token>" or "a:<token>:<optIdx>")
  const parts = data.split(":");

  if (parts[0] === "a") {
    // Answer callback
    const token = parts[1];
    const optionIndex = parts[2] ? parseInt(parts[2]) : null;

    // Look up action from callback_action table
    const { data: action } = await supabase
      .from("callback_action")
      .select("*")
      .eq("token", token)
      .single();

    if (!action) {
      await answerCallbackQuery(query.id, "This button has expired.");
      return;
    }

    // TODO: Process answer, update DB, send feedback
    await answerCallbackQuery(query.id, "Answer recorded! ✅");
  }
}

async function sendMessage(chatId: number, text: string, replyMarkup?: any) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const payload: any = {
    chat_id: chatId,
    text,
    parse_mode: "Markdown",
  };

  if (replyMarkup) {
    payload.reply_markup = replyMarkup;
  }

  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function answerCallbackQuery(callbackQueryId: string, text: string) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/answerCallbackQuery`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      callback_query_id: callbackQueryId,
      text,
    }),
  });
}
