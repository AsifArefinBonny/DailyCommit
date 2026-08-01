"""
Integration tests for daily lesson generation workflow
Tests the full end-to-end flow of generating and sending lessons
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../bot'))


class TestDailyLessonWorkflow:
    """Test complete daily lesson generation workflow"""

    @patch('generate_daily.SupabaseDB')
    @patch('generate_daily.GroqClient')
    @patch('generate_daily.send_message')
    @patch('generate_daily.load_config')
    def test_full_lesson_generation_flow(self, mock_config, mock_send, mock_groq, mock_db):
        """Test complete flow from config to Telegram"""
        from generate_daily import main
        from models import Lesson, Question

        # Mock config
        mock_config.return_value = {
            'topics': [
                {'slug': 'test', 'name': 'Test Topic', 'category': 'test',
                 'weight': 1.0, 'active': True}
            ],
            'llm': {
                'model_name': 'test-model',
                'max_retries': 3,
                'timeout_seconds': 30
            },
            'lesson': {
                'passage_length_target': 150,
                'questions_per_lesson': 3
            }
        }

        # Mock DB
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        # Mock topic exists in DB
        mock_db_instance.select.return_value = [
            {'id': 'topic-1', 'slug': 'test', 'name': 'Test Topic'}
        ]

        # Mock successful DB insert
        mock_db_instance.insert.return_value = [{'id': 'lesson-1'}]

        # Mock Groq client
        mock_groq_instance = Mock()
        mock_groq.return_value = mock_groq_instance

        # Mock successful lesson generation
        mock_lesson = Lesson(
            title="Test Lesson",
            body="Test content",
            difficulty=2,
            questions=[
                Question(
                    type="mcq",
                    prompt="Test?",
                    options=["A", "B"],
                    correct_answer="A",
                    explanation="Test",
                    concept_tag="test",
                    difficulty=2
                )
            ]
        )
        mock_groq_instance.generate.return_value = mock_lesson

        # Mock successful Telegram send
        mock_send.return_value = True

        # Mock user exists
        mock_db_instance.select.return_value = [
            {'telegram_user_id': 123456}
        ]

        # Run main workflow
        with patch('generate_daily.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = '2026-08-01'

            try:
                main()
            except SystemExit:
                pass  # main() calls sys.exit(0) on success

        # Verify workflow steps
        assert mock_groq_instance.generate.called
        assert mock_db_instance.insert.called
        assert mock_send.called

    @patch('generate_daily.SupabaseDB')
    @patch('generate_daily.GroqClient')
    @patch('generate_daily.notify_admin')
    @patch('generate_daily.load_config')
    def test_workflow_handles_llm_failure(self, mock_config, mock_notify, mock_groq, mock_db):
        """Test workflow handles LLM generation failure gracefully"""
        from generate_daily import main

        mock_config.return_value = {
            'topics': [{'slug': 'test', 'name': 'Test', 'category': 'test', 'weight': 1.0, 'active': True}],
            'llm': {'model_name': 'test', 'max_retries': 3, 'timeout_seconds': 30},
            'lesson': {'passage_length_target': 150, 'questions_per_lesson': 3}
        }

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.select.return_value = [{'id': 'topic-1', 'slug': 'test'}]

        # Mock LLM failure
        mock_groq_instance = Mock()
        mock_groq.return_value = mock_groq_instance
        mock_groq_instance.generate.return_value = None  # Generation failed

        # Should call notify_admin and exit
        with pytest.raises(SystemExit):
            main()

        assert mock_notify.called

    @patch('generate_daily.SupabaseDB')
    @patch('generate_daily.load_config')
    def test_workflow_handles_no_active_topics(self, mock_config, mock_db):
        """Test workflow handles case when no topics are active"""
        from generate_daily import main

        mock_config.return_value = {
            'topics': [
                {'slug': 'test', 'name': 'Test', 'category': 'test', 'weight': 1.0, 'active': False}
            ],
            'llm': {'model_name': 'test', 'max_retries': 3, 'timeout_seconds': 30},
            'lesson': {'passage_length_target': 150, 'questions_per_lesson': 3}
        }

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        with pytest.raises(SystemExit):
            main()


class TestTopicSelection:
    """Test topic selection with weighted random"""

    @patch('generate_daily.random.choices')
    @patch('generate_daily.SupabaseDB')
    def test_weighted_topic_selection(self, mock_db, mock_choices):
        """Test that topics are selected based on weights"""
        from generate_daily import select_topic

        config = {
            'topics': [
                {'slug': 'topic1', 'name': 'Topic 1', 'category': 'test', 'weight': 2.0, 'active': True},
                {'slug': 'topic2', 'name': 'Topic 2', 'category': 'test', 'weight': 1.0, 'active': True}
            ]
        }

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.select.return_value = [{'id': 'topic-1'}]

        # Mock random.choices to return first topic
        mock_choices.return_value = [config['topics'][0]]

        topic = select_topic(mock_db_instance, config)

        # Verify weights were used
        call_args = mock_choices.call_args
        weights = call_args[1]['weights']
        assert weights == [2.0, 1.0]

    @patch('generate_daily.SupabaseDB')
    def test_topic_synced_to_database(self, mock_db):
        """Test that selected topic is upserted to database"""
        from generate_daily import select_topic

        config = {
            'topics': [
                {'slug': 'test', 'name': 'Test', 'category': 'test', 'weight': 1.0, 'active': True}
            ]
        }

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.select.return_value = [{'id': 'topic-1', 'slug': 'test'}]

        select_topic(mock_db_instance, config)

        # Verify upsert was called
        assert mock_db_instance.upsert.called
        call_args = mock_db_instance.upsert.call_args[0]
        assert call_args[0] == 'topic'


class TestLessonSaving:
    """Test lesson and questions are saved correctly"""

    @patch('generate_daily.SupabaseDB')
    def test_lesson_saved_with_questions(self, mock_db):
        """Test that lesson and all questions are saved"""
        from generate_daily import save_lesson_to_db
        from models import Lesson, Question
        from datetime import date

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        # Mock successful lesson insert
        mock_db_instance.insert.return_value = [{'id': 'lesson-1'}]

        lesson = Lesson(
            title="Test",
            body="Content",
            difficulty=2,
            questions=[
                Question(
                    type="mcq",
                    prompt="Q1",
                    options=["A", "B"],
                    correct_answer="A",
                    explanation="E1",
                    concept_tag="tag1",
                    difficulty=2
                ),
                Question(
                    type="true_false",
                    prompt="Q2",
                    options=None,
                    correct_answer="true",
                    explanation="E2",
                    concept_tag="tag2",
                    difficulty=2
                )
            ]
        )

        lesson_id = save_lesson_to_db(mock_db_instance, lesson, "topic-1", date.today())

        # Verify lesson was inserted
        assert mock_db_instance.insert.call_count == 3  # 1 lesson + 2 questions

        # Verify lesson data
        lesson_call = mock_db_instance.insert.call_args_list[0]
        assert lesson_call[0][0] == 'lesson'
        assert lesson_call[0][1]['title'] == 'Test'

        # Verify questions were inserted
        question_calls = mock_db_instance.insert.call_args_list[1:]
        assert all(call[0][0] == 'question' for call in question_calls)
