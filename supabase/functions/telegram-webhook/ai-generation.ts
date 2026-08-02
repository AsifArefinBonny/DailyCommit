/**
 * AI Lesson Generation using Groq
 */

const GROQ_API_KEY = Deno.env.get("GROQ_API_KEY")!;
const GROQ_BASE_URL = "https://api.groq.com/openai/v1";

const SQA_TOPICS = [
  "Test Automation Frameworks",
  "API Testing with REST Assured",
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
  "Continuous Testing",
];

interface AIQuestion {
  type: string;
  prompt: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  difficulty: number;
  concept_tag: string;
}

interface AILesson {
  title: string;
  topic_category: string;
  questions: AIQuestion[];
}

export async function generateAILesson(
  supabase: any,
  userId: string
): Promise<string | null> {
  try {
    console.log("[AI] Generating new lesson for user", userId);

    // Pick random topic
    const topic = SQA_TOPICS[Math.floor(Math.random() * SQA_TOPICS.length)];
    console.log("[AI] Topic selected:", topic);

    // Call Groq API
    const prompt = `Generate a micro-lesson about "${topic}" for software QA engineers.

The lesson must include exactly 3 questions of varying types.

Return a JSON object with this exact structure:
{
  "title": "Short lesson title (max 100 chars)",
  "topic_category": "${topic}",
  "questions": [
    {
      "type": "mcq",
      "prompt": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "A",
      "explanation": "Why this answer is correct",
      "difficulty": 2,
      "concept_tag": "${topic.toLowerCase().replace(/ /g, "_")}"
    },
    {
      "type": "true_false",
      "prompt": "True/false question",
      "correct_answer": "true",
      "explanation": "Explanation",
      "difficulty": 1,
      "concept_tag": "${topic.toLowerCase().replace(/ /g, "_")}"
    },
    {
      "type": "fill_in",
      "prompt": "Fill in the blank: ___",
      "correct_answer": "answer",
      "explanation": "Explanation",
      "difficulty": 3,
      "concept_tag": "${topic.toLowerCase().replace(/ /g, "_")}"
    }
  ]
}

Requirements:
- Make questions practical and relevant to real QA work
- Vary question types (mcq, true_false, fill_in)
- Set appropriate difficulty (1-5)
- Provide clear, helpful explanations
- Return ONLY valid JSON, no markdown code blocks`;

    const response = await fetch(`${GROQ_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [
          {
            role: "system",
            content:
              "You are an expert QA engineer and educator. Generate high-quality, practical SQA learning content. Return ONLY valid JSON.",
          },
          {
            role: "user",
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
    });

    if (!response.ok) {
      console.error("[AI] Groq API error:", response.status, await response.text());
      return null;
    }

    const data = await response.json();
    let content = data.choices[0].message.content;

    // Clean response (remove markdown code blocks if present)
    content = content.trim();
    if (content.startsWith("```")) {
      content = content.split("```")[1];
      if (content.startsWith("json")) {
        content = content.substring(4);
      }
      content = content.trim();
    }

    // Parse JSON
    const lessonData: AILesson = JSON.parse(content);

    // Validate
    if (!lessonData.title || !lessonData.questions || lessonData.questions.length !== 3) {
      console.error("[AI] Invalid lesson structure");
      return null;
    }

    console.log("[AI] Lesson generated:", lessonData.title);

    // Save to database
    const { data: lesson, error: lessonError } = await supabase
      .from("lesson")
      .insert({
        title: lessonData.title,
        lesson_date: new Date().toISOString().split("T")[0],
        concept_tag: topic.toLowerCase().replace(/ /g, "_"),
        is_ai_generated: true,
        generated_at: new Date().toISOString(),
        topic_category: lessonData.topic_category,
      })
      .select()
      .single();

    if (lessonError) {
      console.error("[AI] Failed to save lesson:", lessonError);
      return null;
    }

    const lessonId = lesson.id;
    console.log("[AI] Lesson saved with ID:", lessonId);

    // Save questions
    for (const q of lessonData.questions) {
      const { error: qError } = await supabase.from("question").insert({
        lesson_id: lessonId,
        type: q.type,
        prompt: q.prompt,
        options: q.options || null,
        correct_answer: q.correct_answer,
        explanation: q.explanation,
        difficulty: q.difficulty,
        concept_tag: q.concept_tag,
      });

      if (qError) {
        console.error("[AI] Failed to save question:", qError);
      }
    }

    // Set as user's current lesson
    await supabase
      .from("app_user")
      .update({ current_lesson_id: lessonId })
      .eq("id", userId);

    console.log("[AI] Lesson generation complete!");
    return lessonId;
  } catch (error) {
    console.error("[AI] Error generating lesson:", error);
    return null;
  }
}
