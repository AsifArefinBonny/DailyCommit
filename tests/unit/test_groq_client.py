"""
Unit tests for Groq API client
Tests retry logic, error handling, and response validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from bot.groq_client import GroqClient, GroqError
from bot.models import Lesson, Question
from pydantic import ValidationError


class TestGroqClient:
    """Test GroqClient functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.client = GroqClient(
            api_key="test_key",
            model_name="llama-3.3-70b-versatile",
            max_retries=3,
            timeout=30
        )

    def test_initialization(self):
        """Test client initialization"""
        assert self.client.api_key == "test_key"
        assert self.client.model_name == "llama-3.3-70b-versatile"
        assert self.client.max_retries == 3
        assert self.client.timeout == 30

    @patch('bot.groq_client.requests.post')
    def test_successful_generation(self, mock_post):
        """Test successful LLM generation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"title": "Test", "body": "Test body", "difficulty": 2, "questions": []}'
                }
            }]
        }
        mock_post.return_value = mock_response

        result = self.client.generate("test prompt", Lesson)

        assert result is not None
        assert isinstance(result, Lesson)
        assert result.title == "Test"

    @patch('bot.groq_client.requests.post')
    def test_rate_limit_retry(self, mock_post):
        """Test retry logic on rate limit (HTTP 429)"""
        # First call: rate limited
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"retry-after": "1"}

        # Second call: success
        success_response = Mock()
        success_response.status_code = 200
        success_response.ok = True
        success_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"title": "Test", "body": "Body", "difficulty": 2, "questions": []}'
                }
            }]
        }

        mock_post.side_effect = [rate_limit_response, success_response]

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.client.generate("test", Lesson)

        assert result is not None
        assert mock_post.call_count == 2

    @patch('bot.groq_client.requests.post')
    def test_invalid_api_key(self, mock_post):
        """Test handling of invalid API key (HTTP 401)"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with pytest.raises(GroqError, match="Invalid API key"):
            self.client.generate("test", Lesson)

    @patch('bot.groq_client.requests.post')
    def test_server_error_retry(self, mock_post):
        """Test retry on server errors (HTTP 5xx)"""
        # All retries fail with 500
        server_error = Mock()
        server_error.status_code = 500
        mock_post.return_value = server_error

        with patch('time.sleep'):
            result = self.client.generate("test", Lesson)

        assert result is None  # Should return None after all retries
        assert mock_post.call_count == 3  # max_retries

    @patch('bot.groq_client.requests.post')
    def test_validation_error_retry(self, mock_post):
        """Test retry on validation errors"""
        # Response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"title": "Test"}'  # Missing required fields
                }
            }]
        }
        mock_post.return_value = mock_response

        with patch('time.sleep'):
            result = self.client.generate("test", Lesson)

        assert result is None
        assert mock_post.call_count == 3

    @patch('bot.groq_client.requests.post')
    def test_json_extraction_from_markdown(self, mock_post):
        """Test extraction of JSON from markdown code blocks"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '```json\n{"title": "Test", "body": "Body", "difficulty": 2, "questions": []}\n```'
                }
            }]
        }
        mock_post.return_value = mock_response

        result = self.client.generate("test", Lesson)

        assert result is not None
        assert result.title == "Test"

    @patch('bot.groq_client.requests.post')
    def test_timeout_handling(self, mock_post):
        """Test timeout handling"""
        import requests
        mock_post.side_effect = requests.Timeout()

        with patch('time.sleep'):
            result = self.client.generate("test", Lesson)

        assert result is None
        assert mock_post.call_count == 3

    @patch('bot.groq_client.requests.post')
    def test_network_error_handling(self, mock_post):
        """Test network error handling"""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")

        with patch('time.sleep'):
            result = self.client.generate("test", Lesson)

        assert result is None
        assert mock_post.call_count == 3
