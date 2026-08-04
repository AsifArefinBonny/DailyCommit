"""
Weekly digest job (GitHub Actions cron).
Sends a summary of the week's learning: topics covered, accuracy, journal notes.
"""

import os
from datetime import date, timedelta
from db import SupabaseDB
from telegram_notify import send_message, notify_admin


def main():
    """Generate and send weekly digest."""
    try:
        db = SupabaseDB()

        # Get user
        users = db.select("app_user")
        if not users:
            return

        user = users[0]
        chat_id = user["telegram_user_id"]

        # Get this week's lessons
        week_ago = date.today() - timedelta(days=7)
        lessons = db.execute_query(
            lambda: db.client.table("lesson")
            .select("*, topic(name)")
            .gte("lesson_date", str(week_ago))
            .order("lesson_date")
            .execute()
        )

        if not lessons:
            await send_message(
                chat_id, "📊 No lessons this week. Let's get back on track! 💪"
            )
            return

        # Get this week's attempts
        attempts = db.execute_query(
            lambda: db.client.table("attempt")
            .select("*")
            .eq("user_id", user["id"])
            .gte("answered_at", str(week_ago))
            .execute()
        )

        total = len(attempts) if attempts else 0
        correct = sum(1 for a in attempts if a["is_correct"]) if attempts else 0
        accuracy = round((correct / total) * 100) if total > 0 else 0

        # Build digest message
        message = f"📊 **Weekly Digest**\n\n"
        message += f"Lessons completed: {len(lessons)}\n"
        message += f"Questions answered: {total} ({accuracy}% accuracy)\n"
        message += f"XP earned: {user['xp']} total\n\n"

        message += "**Topics covered:**\n"
        for lesson in lessons:
            topic_name = lesson.get("topic", {}).get("name", "Unknown")
            message += f"• {lesson['title']} ({topic_name})\n"

        message += "\n🔥 Keep up the momentum! See you tomorrow."

        send_message(chat_id, message)
        print("✅ Weekly digest sent")

    except Exception as e:
        notify_admin("Weekly Digest", "❌ Failed", str(e), {"traceback": str(e)[:500]})


if __name__ == "__main__":
    main()
