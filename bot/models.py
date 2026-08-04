"""
Pydantic models for validating LLM-generated content.
All OpenRouter responses must pass through these schemas before hitting the DB.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal


class Question(BaseModel):
    """A single question grounded in the lesson passage."""

    type: Literal[
        "mcq",
        "true_false",
        "fill_in",
        "predict_output",
        "spot_the_bug",
        "short_answer",
        "scenario",
    ]
    prompt: str = Field(min_length=10)
    options: Optional[List[str]] = None  # required for MCQ, null otherwise
    correct_answer: str = Field(min_length=1)
    explanation: str = Field(min_length=20)
    concept_tag: Optional[str] = None
    difficulty: int = Field(ge=1, le=5, default=2)
    meta: Optional[dict] = None  # e.g., {"buggy_code": "...", "fixed_code": "..."}

    @field_validator("options")
    @classmethod
    def validate_mcq_options(cls, v, info):
        """MCQ questions must have 2-5 options."""
        if info.data.get("type") == "mcq":
            if not v or len(v) < 2 or len(v) > 5:
                raise ValueError("MCQ must have 2-5 options")
        return v


class Lesson(BaseModel):
    """A complete daily lesson: passage + grounded questions."""

    title: str = Field(min_length=10, max_length=200)
    body: str = Field(min_length=50)  # the read-first passage
    difficulty: int = Field(ge=1, le=5, default=2)
    questions: List[Question] = Field(min_length=1, max_length=5)

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v):
        """Ensure all questions are grounded (no generic trivia)."""
        if not v:
            raise ValueError("Lesson must have at least one question")
        return v


class TutorResponse(BaseModel):
    """AI tutor follow-up response (for Explain Simply / Senior QA buttons)."""

    response: str = Field(min_length=20)


class GradeShortAnswer(BaseModel):
    """Grading result for a short-answer question."""

    is_correct: bool
    feedback: str = Field(min_length=10)
