#!/usr/bin/env python3
"""
AI Lesson Generation using OpenRouter
Generates new lessons with 3 questions each on SQA topics
"""
import os
import json
import random
import requests
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

# SQA Topics for lesson generation
SQA_TOPICS = [
    "Test Automation Frameworks",
    "API Testing with REST Assured/Postman",
    "Selenium WebDriver Best Practices",
    "Test Data Management",
    "CI/CD Integration for QA",
    "Performance Testing Fundamentals",
    "Security Testing Basics",
    "Test Case Design Techniques",
    "Bug Life Cycle and Tracking",
    "Debugging Strategies",
    "Mobile App Testing",
    "Cross-Browser Testing",
    "Database Testing (SQL)",
    "Test Reporting and Metrics",
    "Agile Testing Methodologies",
    "Behavior-Driven Development (BDD)",
    "Test-Driven Development (TDD)",
    "Continuous Testing",
    "Accessibility Testing (WCAG)",
    "Smoke Testing vs Sanity Testing"
]

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Groq models to use (all free and fast!)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",      # Best quality
    "llama-3.1-70b-versatile",      # Good fallback
    "mixtral-8x7b-32768",           # Fast alternative
    "gemma2-9b-it"                  # Lightweight fallback
]

# Pydantic Models for Validation
class QuestionModel(BaseModel):
    """Validated question structure"""
    type: str = Field(..., pattern="^(mcq|true_false|fill_in|short_answer)$")
    prompt: str = Field(..., min_length=10, max_length=500)
    options: Optional[List[str]] = None
    correct_answer: str = Field(..., min_length=1)
    explanation: str = Field(..., min_length=20, max_length=1000)
    difficulty: int = Field(..., ge=1, le=5)
    concept_tag: str

    @validator('options')
    def validate_options(cls, v, values):
        if values.get('type') == 'mcq' and (not v or len(v) != 4):
            raise ValueError("MCQ must have exactly 4 options")
        return v

class LessonModel(BaseModel):
    """Validated lesson structure"""
    title: str = Field(..., min_length=5, max_length=200)
    topic_category: str
    questions: List[QuestionModel] = Field(..., min_length=3, max_length=3)

    @validator('questions')
    def validate_three_questions(cls, v):
        if len(v) != 3:
            raise ValueError("Lesson must have exactly 3 questions")
        return v

def call_groq(prompt: str, max_retries: int = 3) -> Optional[str]:
    """
    Call Groq API with retry logic and fallback models
    Groq is MUCH faster than OpenRouter and free!
    """
    for attempt in range(max_retries):
        for model in GROQ_MODELS:
            try:
                response = requests.post(
                    f"{GROQ_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert QA engineer and educator. Generate high-quality, practical SQA learning content."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    timeout=15  # Groq is super fast!
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    print(f"✅ Success with model: {model}")
                    return content

                elif response.status_code == 429:
                    print(f"⚠️  Rate limited on {model}, trying next model...")
                    continue

                else:
                    print(f"❌ Error {response.status_code} on {model}: {response.text}")
                    continue

            except Exception as e:
                print(f"❌ Exception with {model}: {e}")
                continue

    print("❌ All models failed or rate-limited")
    return None

def generate_lesson_ai(topic: Optional[str] = None) -> Optional[LessonModel]:
    """
    Generate a complete lesson with 3 questions using AI
    """
    if not topic:
        topic = random.choice(SQA_TOPICS)

    print(f"🎓 Generating lesson on: {topic}")

    prompt = f"""Generate a micro-lesson about "{topic}" for software QA engineers.

The lesson must include exactly 3 questions of varying types.

Return a JSON object with this exact structure:
{{
  "title": "Short lesson title (max 100 chars)",
  "topic_category": "{topic}",
  "questions": [
    {{
      "type": "mcq",
      "prompt": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A",
      "explanation": "Why this answer is correct (practical explanation)",
      "difficulty": 2,
      "concept_tag": "{topic.lower().replace(' ', '_')}"
    }},
    {{
      "type": "true_false",
      "prompt": "True/false question",
      "correct_answer": "true",
      "explanation": "Explanation",
      "difficulty": 1,
      "concept_tag": "{topic.lower().replace(' ', '_')}"
    }},
    {{
      "type": "fill_in",
      "prompt": "Fill in the blank: ___",
      "correct_answer": "answer",
      "explanation": "Explanation",
      "difficulty": 3,
      "concept_tag": "{topic.lower().replace(' ', '_')}"
    }}
  ]
}}

Requirements:
- Make questions practical and relevant to real QA work
- Vary question types (mcq, true_false, fill_in, short_answer)
- Set appropriate difficulty (1-5)
- Provide clear, helpful explanations
- MCQ options should include common misconceptions
- Return ONLY valid JSON, no markdown code blocks
"""

    response_text = call_groq(prompt)
    if not response_text:
        return None

    try:
        # Clean response (remove markdown code blocks if present)
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        # Parse JSON
        lesson_data = json.loads(cleaned)

        # Validate with Pydantic
        lesson = LessonModel(**lesson_data)
        print(f"✅ Lesson generated and validated: {lesson.title}")
        return lesson

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response was: {response_text[:200]}...")
        return None
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return None

def save_lesson_to_supabase(lesson: LessonModel, user_id: str) -> Optional[str]:
    """
    Save generated lesson to Supabase database
    Returns lesson_id if successful
    """
    import subprocess

    SUPABASE_URL = "https://ybblpzymovvngtllrsbn.supabase.co"
    SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliYmxwenltb3Z2bmd0bGxyc2JuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NTYwNTI1OCwiZXhwIjoyMTAxMTgxMjU4fQ.ri0VXmwF1597IQ38BBL_ysYhM8IdDuwAXX8RIw3foSg"

    try:
        # Insert lesson
        lesson_payload = {
            "title": lesson.title,
            "lesson_date": datetime.now().date().isoformat(),
            "concept_tag": lesson.topic_category.lower().replace(' ', '_'),
            "is_ai_generated": True,
            "generated_at": datetime.now().isoformat(),
            "topic_category": lesson.topic_category
        }

        cmd = ['curl', '-s', '-X', 'POST',
               f'{SUPABASE_URL}/rest/v1/lesson',
               '-H', f'apikey: {SERVICE_KEY}',
               '-H', f'Authorization: Bearer {SERVICE_KEY}',
               '-H', 'Content-Type: application/json',
               '-H', 'Prefer: return=representation',
               '-d', json.dumps(lesson_payload)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        lesson_response = json.loads(result.stdout)

        if isinstance(lesson_response, list) and len(lesson_response) > 0:
            lesson_id = lesson_response[0]['id']
            print(f"✅ Lesson saved: {lesson_id}")

            # Insert questions
            for q in lesson.questions:
                question_payload = {
                    "lesson_id": lesson_id,
                    "type": q.type,
                    "prompt": q.prompt,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation,
                    "difficulty": q.difficulty,
                    "concept_tag": q.concept_tag
                }

                cmd_q = ['curl', '-s', '-X', 'POST',
                         f'{SUPABASE_URL}/rest/v1/question',
                         '-H', f'apikey: {SERVICE_KEY}',
                         '-H', f'Authorization: Bearer {SERVICE_KEY}',
                         '-H', 'Content-Type: application/json',
                         '-d', json.dumps(question_payload)]

                subprocess.run(cmd_q, capture_output=True)

            # Update user's current_lesson_id
            cmd_user = ['curl', '-s', '-X', 'PATCH',
                        f'{SUPABASE_URL}/rest/v1/app_user?id=eq.{user_id}',
                        '-H', f'apikey: {SERVICE_KEY}',
                        '-H', f'Authorization: Bearer {SERVICE_KEY}',
                        '-H', 'Content-Type: application/json',
                        '-d', json.dumps({"current_lesson_id": lesson_id})]

            subprocess.run(cmd_user, capture_output=True)

            print(f"✅ All questions saved for lesson {lesson_id}")
            return lesson_id

    except Exception as e:
        print(f"❌ Error saving to Supabase: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("AI LESSON GENERATOR")
    print("=" * 80)
    print()

    # Test generation
    lesson = generate_lesson_ai()
    if lesson:
        print("\n" + "=" * 80)
        print("GENERATED LESSON")
        print("=" * 80)
        print(f"Title: {lesson.title}")
        print(f"Topic: {lesson.topic_category}")
        print(f"Questions: {len(lesson.questions)}")
        print()
        for i, q in enumerate(lesson.questions, 1):
            print(f"{i}. [{q.type}] {q.prompt[:60]}...")
        print()
        print("✅ Lesson generation successful!")
    else:
        print("❌ Failed to generate lesson")
