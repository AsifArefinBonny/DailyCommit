"""
Unit tests for Pydantic models
Tests validation, serialization, and data integrity
"""
import pytest
from pydantic import ValidationError
from bot.models import Lesson, Question


class TestQuestion:
    """Test Question model"""

    def test_valid_mcq_question(self):
        """Test creating a valid MCQ question"""
        q = Question(
            type="mcq",
            prompt="What is 2+2?",
            options=["A. 3", "B. 4", "C. 5", "D. 6"],
            correct_answer="B",
            explanation="2+2=4",
            concept_tag="arithmetic",
            difficulty=1
        )

        assert q.type == "mcq"
        assert len(q.options) == 4
        assert q.correct_answer == "B"

    def test_valid_true_false_question(self):
        """Test creating a valid True/False question"""
        q = Question(
            type="true_false",
            prompt="Python is a programming language",
            options=None,
            correct_answer="true",
            explanation="Python is indeed a programming language",
            concept_tag="python-basics",
            difficulty=1
        )

        assert q.type == "true_false"
        assert q.options is None
        assert q.correct_answer == "true"

    def test_invalid_question_type(self):
        """Test that invalid question types are rejected"""
        with pytest.raises(ValidationError, match="type"):
            Question(
                type="invalid_type",  # Not in allowed types
                prompt="Test",
                options=None,
                correct_answer="A",
                explanation="Test",
                concept_tag="test",
                difficulty=1
            )

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error"""
        with pytest.raises(ValidationError):
            Question(
                type="mcq",
                # Missing prompt, correct_answer, etc.
            )

    def test_difficulty_range(self):
        """Test that difficulty must be in valid range"""
        # Valid difficulty
        q = Question(
            type="mcq",
            prompt="Test",
            options=["A", "B"],
            correct_answer="A",
            explanation="Test",
            concept_tag="test",
            difficulty=3
        )
        assert q.difficulty == 3

        # Difficulty can be 1-5, test boundaries
        for diff in [1, 2, 3, 4, 5]:
            q = Question(
                type="mcq",
                prompt="Test",
                options=["A", "B"],
                correct_answer="A",
                explanation="Test",
                concept_tag="test",
                difficulty=diff
            )
            assert q.difficulty == diff


class TestLesson:
    """Test Lesson model"""

    def test_valid_lesson(self):
        """Test creating a valid lesson"""
        lesson = Lesson(
            title="Test Lesson",
            body="This is test content",
            difficulty=2,
            questions=[
                Question(
                    type="mcq",
                    prompt="Test?",
                    options=["A. 1", "B. 2"],
                    correct_answer="A",
                    explanation="Test",
                    concept_tag="test",
                    difficulty=2
                )
            ]
        )

        assert lesson.title == "Test Lesson"
        assert len(lesson.questions) == 1
        assert lesson.difficulty == 2

    def test_lesson_with_multiple_questions(self):
        """Test lesson with multiple questions"""
        questions = [
            Question(
                type="mcq",
                prompt=f"Question {i}",
                options=["A", "B"],
                correct_answer="A",
                explanation="Test",
                concept_tag="test",
                difficulty=2
            )
            for i in range(3)
        ]

        lesson = Lesson(
            title="Multi-Question Lesson",
            body="Content",
            difficulty=2,
            questions=questions
        )

        assert len(lesson.questions) == 3

    def test_lesson_missing_required_fields(self):
        """Test that missing fields raise validation error"""
        with pytest.raises(ValidationError):
            Lesson(
                title="Test",
                # Missing body, difficulty, questions
            )

    def test_lesson_with_empty_questions_list(self):
        """Test lesson with no questions"""
        lesson = Lesson(
            title="Empty Lesson",
            body="Content",
            difficulty=2,
            questions=[]
        )

        assert len(lesson.questions) == 0

    def test_lesson_json_serialization(self):
        """Test JSON serialization of lesson"""
        lesson = Lesson(
            title="Test",
            body="Content",
            difficulty=2,
            questions=[]
        )

        json_data = lesson.model_dump()

        assert json_data["title"] == "Test"
        assert json_data["body"] == "Content"
        assert json_data["difficulty"] == 2
        assert json_data["questions"] == []

    def test_lesson_from_json(self):
        """Test creating lesson from JSON"""
        json_data = {
            "title": "From JSON",
            "body": "Content",
            "difficulty": 3,
            "questions": [
                {
                    "type": "true_false",
                    "prompt": "Test?",
                    "options": None,
                    "correct_answer": "true",
                    "explanation": "Because",
                    "concept_tag": "test",
                    "difficulty": 3
                }
            ]
        }

        lesson = Lesson.model_validate(json_data)

        assert lesson.title == "From JSON"
        assert len(lesson.questions) == 1
        assert lesson.questions[0].type == "true_false"
