"""
Daily lesson generation job (GitHub Actions cron).
Generates a read-first lesson, inserts to DB, sends to Telegram.
"""
import os
import sys

print("🚀 Starting generate_daily.py...", flush=True)

import yaml
from datetime import date

print("✓ Standard libraries imported", flush=True)

try:
    from db import SupabaseDB
    print("✓ db module imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import db: {e}", flush=True)
    raise

try:
    from groq_client import GroqClient
    print("✓ groq_client module imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import groq_client: {e}", flush=True)
    raise

try:
    from models import Lesson, Question
    print("✓ models module imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import models: {e}", flush=True)
    raise

try:
    from telegram_notify import send_message, notify_admin
    print("✓ telegram_notify module imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import telegram_notify: {e}", flush=True)
    raise

import random
print("✓ All imports successful", flush=True)


def load_config():
    """Load topics.yaml configuration."""
    # Get the project root directory (parent of bot/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, "config", "topics.yaml")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def select_topic(db: SupabaseDB, config: dict) -> dict:
    """Select a topic using weighted random selection."""
    topics = config["topics"]
    active_topics = [t for t in topics if t.get("active", True)]

    if not active_topics:
        notify_admin("Daily Lesson", "⚠️ No active topics",
                   "No topics are marked active in config/topics.yaml", {})
        return None

    # Weighted random selection
    weights = [t.get("weight", 1.0) for t in active_topics]
    selected = random.choices(active_topics, weights=weights, k=1)[0]

    # Sync topic to DB if needed
    db.upsert("topic", {
        "slug": selected["slug"],
        "name": selected["name"],
        "category": selected["category"],
        "weight": selected.get("weight", 1.0),
        "active": selected.get("active", True)
    })

    # Get topic ID from DB
    topic_row = db.select("topic", filters={"slug": selected["slug"]})
    if topic_row:
        selected["id"] = topic_row[0]["id"]

    return selected


def generate_lesson_prompt(topic: dict, config: dict) -> str:
    """Build the LLM prompt for lesson generation."""
    lesson_settings = config.get("lesson", {})
    passage_length = lesson_settings.get("passage_length_target", 150)
    num_questions = lesson_settings.get("questions_per_lesson", 3)

    prompt = f"""Generate a daily micro-lesson for software QA learning.

Topic: {topic['name']} ({topic['category']})
Target difficulty: 2/5 (intermediate beginner)

Requirements:
1. **READ-FIRST passage** (~{passage_length} words):
   - A concrete, practical example or concept explanation
   - Real-world context (production scenarios, common mistakes, etc.)
   - Must contain ALL information needed to answer the questions

2. **{num_questions} grounded questions**:
   - Questions MUST be answerable by reading the passage (no external knowledge)
   - Mix question types: MCQ, true/false, fill-in, predict-output, spot-the-bug, short-answer
   - Include a concept_tag for spaced repetition (e.g., "boundary-value-analysis")
   - Each question has a clear explanation that deepens understanding

Output as JSON:
{{
  "title": "...",
  "body": "...(the passage, markdown)...",
  "difficulty": 2,
  "questions": [
    {{
      "type": "mcq",
      "prompt": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "...",
      "concept_tag": "...",
      "difficulty": 2
    }},
    ...
  ]
}}

Make it engaging, practical, and career-relevant for a QA engineer."""

    return prompt


def save_lesson_to_db(db: SupabaseDB, lesson: Lesson, topic_id: str, lesson_date: date) -> str:
    """Save lesson and questions to database. Returns lesson_id."""
    # Insert lesson
    lesson_data = {
        "lesson_date": str(lesson_date),
        "topic_id": topic_id,
        "title": lesson.title,
        "body": lesson.body,
        "difficulty": lesson.difficulty,
        "source": "ai"
    }
    lesson_result = db.insert("lesson", lesson_data)

    if not lesson_result:
        notify_admin("Daily Lesson", "❌ DB insert failed",
                   "Failed to insert lesson into database", {"date": str(lesson_date)})
        return None

    lesson_id = lesson_result[0]["id"]

    # Insert questions
    for q in lesson.questions:
        question_data = {
            "lesson_id": lesson_id,
            "type": q.type,
            "prompt": q.prompt,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "explanation": q.explanation,
            "concept_tag": q.concept_tag,
            "difficulty": q.difficulty,
            "meta": q.meta
        }
        db.insert("question", question_data)

    return lesson_id


def send_lesson_to_telegram(db: SupabaseDB, lesson_id: str):
    """Send the lesson to the user via Telegram."""
    # Get user
    users = db.select("app_user")
    if not users:
        notify_admin("Daily Lesson", "⚠️ No users",
                   "No users in app_user table", {})
        return

    user = users[0]  # Single user for now
    chat_id = user["telegram_user_id"]

    # Get lesson and questions
    lesson_rows = db.select("lesson", filters={"id": lesson_id})
    if not lesson_rows:
        return

    lesson = lesson_rows[0]
    questions = db.select("question", filters={"lesson_id": lesson_id})

    # Format message
    message = f"📚 **{lesson['title']}**\n\n{lesson['body']}\n\n"
    message += f"_{len(questions)} questions to follow..._"

    # Send lesson
    success = send_message(chat_id, message)

    if not success:
        notify_admin("Daily Lesson", "❌ Send failed",
                   "Failed to send lesson to Telegram",
                   {"lesson_id": lesson_id, "chat_id": chat_id})
        return

    # TODO: Send first question with inline keyboard
    # This will be handled by the Telegram webhook in v2


def main():
    """Main entry point for daily lesson generation."""
    try:
        print("📝 Starting main()...", flush=True)
        # Load config
        print("📂 Loading config...", flush=True)
        config = load_config()
        print(f"✓ Config loaded: {len(config.get('topics', []))} topics found", flush=True)

        # Initialize services
        print("🔌 Initializing Supabase DB...", flush=True)
        db = SupabaseDB()
        print("✓ DB connected", flush=True)

        print("🤖 Initializing Groq client...", flush=True)
        llm = GroqClient(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=config["llm"]["model_name"],
            max_retries=config["llm"]["max_retries"],
            timeout=config["llm"]["timeout_seconds"]
        )
        print("✓ Groq client initialized", flush=True)

        # Select topic
        print("🎲 Selecting topic...", flush=True)
        topic = select_topic(db, config)
        print(f"✓ Topic selected: {topic.get('name') if topic else 'None'}", flush=True)
        if not topic:
            sys.exit(1)

        # Generate lesson
        print("📝 Generating lesson prompt...", flush=True)
        prompt = generate_lesson_prompt(topic, config)
        print(f"✓ Prompt generated ({len(prompt)} chars)", flush=True)

        print("🤖 Calling OpenRouter API...", flush=True)
        lesson = llm.generate(prompt, Lesson)
        print(f"✓ Lesson generated: {lesson.title if lesson else 'None'}", flush=True)

        if not lesson:
            notify_admin("Daily Lesson", "❌ Generation failed",
                       "LLM failed to generate valid lesson after all retries",
                       {"topic": topic["name"]})
            sys.exit(1)

        # Save to DB
        lesson_id = save_lesson_to_db(db, lesson, topic.get("id"), date.today())
        if not lesson_id:
            sys.exit(1)

        # Send to Telegram
        send_lesson_to_telegram(db, lesson_id)

        print(f"✅ Daily lesson generated and sent: {lesson.title}")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ ERROR: {str(e)}", file=sys.stderr)
        print(f"Traceback:\n{error_details}", file=sys.stderr)

        notify_admin("Daily Lesson", "❌ Unexpected error",
                   str(e),
                   {"traceback": error_details[:500]},
                   run_url=os.getenv("GITHUB_RUN_URL"))
        sys.exit(1)


if __name__ == "__main__":
    main()
