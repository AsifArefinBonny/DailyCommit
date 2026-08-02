"""
Test suite for answer validation logic in webhook.
Tests all possible answer formats and edge cases.
"""
import pytest


class TestAnswerValidation:
    """
    Test the answer validation logic that handles multiple formats.
    This simulates the webhook's validation function.
    """

    def validate_answer(self, question_type: str, user_answer: str, correct_answer: str, options: list = None) -> bool:
        """
        Replica of the webhook's answer validation logic for testing.
        """
        correct = False
        user_answer_norm = user_answer.lower().strip()
        correct_answer_norm = correct_answer.lower().strip()

        if question_type == "mcq":
            # Direct match (handles letter format)
            if user_answer_norm == correct_answer_norm:
                correct = True
            # Check if correct_answer is in options array
            elif options and isinstance(options, list):
                # Find the index of the correct answer in options
                correct_index = -1
                for i, opt in enumerate(options):
                    opt_lower = opt.lower().strip()
                    # Match if:
                    # 1. Exact match (e.g., "hash table" == "hash table")
                    # 2. Option starts with letter prefix (e.g., "a. hash table" with correct_answer="a")
                    # 3. Correct answer is full text contained in option (e.g., "hash table" in "a. hash table")
                    if opt_lower == correct_answer_norm:
                        correct_index = i
                        break
                    elif opt_lower.startswith(f"{correct_answer_norm}. "):
                        correct_index = i
                        break
                    elif len(correct_answer_norm) > 1 and correct_answer_norm in opt_lower:
                        # Only match substring if correct_answer is more than 1 char (avoid "b" matching "hash table")
                        correct_index = i
                        break

                # Map user's letter to index
                letter_to_index = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
                user_index = letter_to_index.get(user_answer_norm)

                if correct_index != -1 and user_index is not None and correct_index == user_index:
                    correct = True

        elif question_type == "true_false":
            # Normalize variations
            normalized = user_answer_norm.replace('✓', '').replace('✗', '').replace(' ', '')
            correct_normalized = correct_answer_norm.replace('✓', '').replace('✗', '').replace(' ', '')
            correct = normalized == correct_normalized

        else:
            # Direct comparison for other types
            correct = user_answer_norm == correct_answer_norm

        return correct

    # ========================================================================
    # MCQ Tests - Correct Answer Format: Letter (A, B, C, D)
    # ========================================================================

    def test_mcq_correct_answer_letter_format(self):
        """Test MCQ with correct_answer='A' and options with letter prefixes."""
        question_type = "mcq"
        options = ["A. Hash table", "B. Array", "C. List", "D. Tree"]
        correct_answer = "A"

        # User selects first option
        assert self.validate_answer(question_type, "A", correct_answer, options) == True
        # User selects wrong option
        assert self.validate_answer(question_type, "B", correct_answer, options) == False
        assert self.validate_answer(question_type, "C", correct_answer, options) == False
        assert self.validate_answer(question_type, "D", correct_answer, options) == False

    def test_mcq_correct_answer_letter_format_case_insensitive(self):
        """Test MCQ with lowercase user input."""
        question_type = "mcq"
        options = ["A. Hash table", "B. Array", "C. List", "D. Tree"]
        correct_answer = "A"

        assert self.validate_answer(question_type, "a", correct_answer, options) == True
        assert self.validate_answer(question_type, "A", correct_answer, options) == True

    # ========================================================================
    # MCQ Tests - Correct Answer Format: Full Text
    # ========================================================================

    def test_mcq_correct_answer_full_text_format(self):
        """Test MCQ where correct_answer is full option text."""
        question_type = "mcq"
        options = ["A. Hash table", "B. Array", "C. List", "D. Tree"]
        correct_answer = "Hash table"

        # User selects option A (index 0) which contains "Hash table"
        assert self.validate_answer(question_type, "A", correct_answer, options) == True
        assert self.validate_answer(question_type, "B", correct_answer, options) == False

    def test_mcq_correct_answer_full_text_with_prefix(self):
        """Test MCQ where correct_answer includes the letter prefix."""
        question_type = "mcq"
        options = ["A. Hash table", "B. Array", "C. List", "D. Tree"]
        correct_answer = "A. Hash table"

        # User selects option A
        assert self.validate_answer(question_type, "A", correct_answer, options) == True

    # ========================================================================
    # MCQ Tests - Options Without Letter Prefixes
    # ========================================================================

    def test_mcq_options_without_prefixes(self):
        """Test MCQ where options don't have letter prefixes."""
        question_type = "mcq"
        options = ["Hash table", "Array", "List", "Tree"]
        correct_answer = "Hash table"

        # User selects first option (A)
        assert self.validate_answer(question_type, "A", correct_answer, options) == True
        assert self.validate_answer(question_type, "B", correct_answer, options) == False

    def test_mcq_options_without_prefixes_letter_correct_answer(self):
        """Test MCQ where options have no prefixes but correct_answer is a letter."""
        question_type = "mcq"
        options = ["Hash table", "Array", "List", "Tree"]
        correct_answer = "B"  # Should match second option

        assert self.validate_answer(question_type, "B", correct_answer, options) == True
        assert self.validate_answer(question_type, "A", correct_answer, options) == False

    # ========================================================================
    # True/False Tests
    # ========================================================================

    def test_true_false_basic(self):
        """Test true/false validation."""
        question_type = "true_false"

        assert self.validate_answer(question_type, "true", "true") == True
        assert self.validate_answer(question_type, "false", "false") == True
        assert self.validate_answer(question_type, "true", "false") == False
        assert self.validate_answer(question_type, "false", "true") == False

    def test_true_false_case_insensitive(self):
        """Test true/false with different cases."""
        question_type = "true_false"

        assert self.validate_answer(question_type, "True", "true") == True
        assert self.validate_answer(question_type, "TRUE", "true") == True
        assert self.validate_answer(question_type, "False", "false") == True

    def test_true_false_with_symbols(self):
        """Test true/false with checkmark symbols."""
        question_type = "true_false"

        assert self.validate_answer(question_type, "true ✓", "true") == True
        assert self.validate_answer(question_type, "false ✗", "false") == True

    # ========================================================================
    # Other Question Types
    # ========================================================================

    def test_fill_in_direct_match(self):
        """Test fill-in-the-blank questions."""
        question_type = "fill_in"

        assert self.validate_answer(question_type, "boundary testing", "boundary testing") == True
        assert self.validate_answer(question_type, "Boundary Testing", "boundary testing") == True
        assert self.validate_answer(question_type, "boundary value", "boundary testing") == False

    def test_short_answer_direct_match(self):
        """Test short answer questions."""
        question_type = "short_answer"

        assert self.validate_answer(question_type, "integration test", "integration test") == True
        assert self.validate_answer(question_type, "Integration Test", "integration test") == True

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_options_array(self):
        """Test MCQ with empty options array."""
        question_type = "mcq"
        options = []
        correct_answer = "A"

        # Should fall back to direct string comparison
        assert self.validate_answer(question_type, "A", correct_answer, options) == True
        assert self.validate_answer(question_type, "B", correct_answer, options) == False

    def test_none_options(self):
        """Test MCQ with None options."""
        question_type = "mcq"
        options = None
        correct_answer = "A"

        # Should fall back to direct string comparison
        assert self.validate_answer(question_type, "A", correct_answer, options) == True

    def test_whitespace_handling(self):
        """Test that extra whitespace is handled."""
        question_type = "mcq"
        options = ["A. Hash table ", " B. Array", "C. List  ", "D. Tree"]
        correct_answer = " A "

        assert self.validate_answer(question_type, " a ", correct_answer, options) == True

    def test_special_characters_in_answer(self):
        """Test answers with special characters."""
        question_type = "fill_in"

        assert self.validate_answer(question_type, "test-driven development", "test-driven development") == True
        assert self.validate_answer(question_type, "Test-Driven Development", "test-driven development") == True


class TestQuestionFlow:
    """
    Integration tests for the complete question flow.
    """

    def test_user_gets_same_question_until_correct(self):
        """
        Verify that getPendingQuestion returns the same question
        until the user answers correctly.
        """
        # This would require database mocking
        # Placeholder for integration test
        pass

    def test_user_progresses_after_correct_answer(self):
        """
        Verify that after a correct answer, the next question is different.
        """
        # This would require database mocking
        # Placeholder for integration test
        pass


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_mcq_question_letter_format():
    """Sample MCQ question with letter format correct_answer."""
    return {
        "id": "test-q-1",
        "type": "mcq",
        "prompt": "What data structure uses key-value pairs?",
        "options": ["A. Hash table", "B. Array", "C. Linked list", "D. Stack"],
        "correct_answer": "A",
        "explanation": "Hash tables use key-value pairs for O(1) lookup."
    }


@pytest.fixture
def sample_mcq_question_text_format():
    """Sample MCQ question with text format correct_answer."""
    return {
        "id": "test-q-2",
        "type": "mcq",
        "prompt": "What data structure uses key-value pairs?",
        "options": ["A. Hash table", "B. Array", "C. Linked list", "D. Stack"],
        "correct_answer": "Hash table",
        "explanation": "Hash tables use key-value pairs for O(1) lookup."
    }


@pytest.fixture
def sample_true_false_question():
    """Sample true/false question."""
    return {
        "id": "test-q-3",
        "type": "true_false",
        "prompt": "Unit tests should test implementation details.",
        "options": None,
        "correct_answer": "false",
        "explanation": "Unit tests should test behavior, not implementation."
    }


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
