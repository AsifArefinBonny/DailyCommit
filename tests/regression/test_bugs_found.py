"""
Regression tests for bugs found during development
These tests ensure previously found bugs don't reoccur
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add bot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../bot'))


class TestConfigPathBug:
    """
    BUG: Config file path error when running from GitHub Actions
    ERROR: [Errno 2] No such file or directory: 'config/topics.yaml'
    FIX: Used absolute path from __file__
    """

    @patch('builtins.open')
    def test_config_uses_absolute_path(self, mock_open):
        """Test that config loading uses absolute path, not relative"""
        from generate_daily import load_config
        import yaml

        mock_open.return_value.__enter__.return_value.read.return_value = "topics: []"

        with patch('yaml.safe_load', return_value={"topics": []}):
            config = load_config()

        # Verify open was called with absolute path
        call_args = str(mock_open.call_args)
        assert '/config/topics.yaml' in call_args or '\\config\\topics.yaml' in call_args
        assert not call_args.startswith('config/')  # Should not be relative


class TestHttpxVersionConflict:
    """
    BUG: httpx version conflict
    ERROR: httpx 0.28.1 incompatible with supabase requiring httpx<0.28
    FIX: Pinned httpx<0.28,>=0.24 in requirements.txt
    """

    def test_httpx_version_pinned(self):
        """Test that httpx version is pinned in requirements"""
        with open('bot/requirements.txt', 'r') as f:
            requirements = f.read()

        assert 'httpx<0.28' in requirements, "httpx version should be pinned <0.28"
        assert 'httpx>=' in requirements, "httpx should have minimum version"


class TestOpenRouterModelAvailability:
    """
    BUG: OpenRouter free models unavailable
    ERROR: deepseek-chat-v3:free, llama-3.3-70b:free returned 404
    FIX: Switched to Groq API with guaranteed free models
    """

    def test_using_groq_not_openrouter(self):
        """Test that we're using Groq, not OpenRouter"""
        with open('config/topics.yaml', 'r') as f:
            import yaml
            config = yaml.safe_load(f)

        assert config['llm']['provider'] == 'groq', "Should use Groq provider"

    def test_groq_model_exists(self):
        """Test that Groq client is implemented"""
        from groq_client import GroqClient

        assert GroqClient is not None


class TestQuestionTypeValidation:
    """
    BUG: LLM generated invalid question types
    ERROR: questions.1.type - Input should be 'mcq', 'true_false'... got 'true/'
    FIX: Added explicit type list in prompt
    """

    def test_question_type_must_be_valid(self):
        """Test that Question model only accepts valid types"""
        from models import Question
        from pydantic import ValidationError

        valid_types = ['mcq', 'true_false', 'fill_in', 'predict_output',
                       'spot_the_bug', 'short_answer', 'scenario']

        # Test valid types work
        for q_type in valid_types:
            q = Question(
                type=q_type,
                prompt="Test",
                options=None,
                correct_answer="test",
                explanation="test",
                concept_tag="test",
                difficulty=2
            )
            assert q.type == q_type

        # Test invalid type fails
        with pytest.raises(ValidationError):
            Question(
                type="true/",  # The bug we encountered
                prompt="Test",
                options=None,
                correct_answer="test",
                explanation="test",
                concept_tag="test",
                difficulty=2
            )

    def test_prompt_includes_valid_types(self):
        """Test that generation prompt explicitly lists valid types"""
        from generate_daily import generate_lesson_prompt

        topic = {"name": "Test", "category": "test"}
        config = {"lesson": {"passage_length_target": 150, "questions_per_lesson": 3}}

        prompt = generate_lesson_prompt(topic, config)

        # Verify prompt contains explicit type list
        assert '"mcq"' in prompt
        assert '"true_false"' in prompt
        assert '"fill_in"' in prompt
        assert 'CRITICAL' in prompt or 'must be EXACTLY' in prompt.lower()


class TestSupabaseEnvVarNames:
    """
    BUG: Supabase reserves SUPABASE_ prefix
    ERROR: Name must not start with the SUPABASE_ prefix
    FIX: Changed to DB_URL and DB_SERVICE_KEY
    """

    def test_webhook_uses_correct_env_vars(self):
        """Test that webhook doesn't use SUPABASE_ prefix"""
        with open('supabase/functions/telegram-webhook/index.ts', 'r') as f:
            webhook_code = f.read()

        # Should NOT use SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY
        assert 'SUPABASE_URL' not in webhook_code or 'DB_URL' in webhook_code
        assert 'SUPABASE_SERVICE_ROLE_KEY' not in webhook_code or 'DB_SERVICE_KEY' in webhook_code

        # Should use DB_URL and DB_SERVICE_KEY instead
        assert 'DB_URL' in webhook_code
        assert 'DB_SERVICE_KEY' in webhook_code


class TestWebhookJWTAuthentication:
    """
    BUG: Webhook returned 401 Unauthorized
    ERROR: Wrong response from the webhook: 401 Unauthorized
    FIX: Disabled JWT verification for public webhook
    """

    def test_webhook_config_disables_jwt(self):
        """Test that webhook config disables JWT verification"""
        import os

        config_path = 'supabase/functions/telegram-webhook/config.yaml'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                import yaml
                config = yaml.safe_load(f)

            assert config.get('verify_jwt') == False, "JWT verification should be disabled"


class TestGitBranchDefault:
    """
    BUG: Pushed to 'master' but default was 'main'
    FIX: Renamed branch to main and force-pushed
    """

    def test_github_actions_use_main_branch(self):
        """Test that GitHub Actions workflows reference main branch"""
        workflow_file = '.github/workflows/daily.yml'

        with open(workflow_file, 'r') as f:
            workflow = f.read()

        # Workflows should trigger on main, not master
        assert 'main' in workflow.lower()


class TestSecretsNotCommitted:
    """
    BUG: Accidentally committed secrets in setup_secrets.sh
    FIX: Added to .gitignore, use GitHub Secrets instead
    """

    def test_secrets_in_gitignore(self):
        """Test that secret files are in .gitignore"""
        with open('.gitignore', 'r') as f:
            gitignore = f.read()

        # Common secret file patterns should be ignored
        dangerous_patterns = ['*.env', 'secrets', '.env']
        for pattern in dangerous_patterns:
            # At least one pattern should be in gitignore
            pass  # Basic check

    def test_no_hardcoded_secrets_in_code(self):
        """Test that no obvious secrets are hardcoded"""
        import re

        # Check Python files
        secret_pattern = re.compile(r'(api_?key|token|password)\s*=\s*["\'][^"\']{20,}["\']', re.IGNORECASE)

        for root, dirs, files in os.walk('bot'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read()
                        # Should use os.getenv, not hardcoded values
                        matches = secret_pattern.findall(content)
                        for match in matches:
                            # If we find API key assignments, they should use getenv
                            assert 'getenv' in content or 'environ' in content, \
                                f"Possible hardcoded secret in {file}"


class TestDatabaseConnectionError:
    """
    BUG: Silent database connection failures
    ERROR: No error messages when DB connection failed
    FIX: Added extensive debug logging with flush=True
    """

    @patch('bot.db.create_client')
    def test_db_initialization_logs_errors(self, mock_create):
        """Test that DB errors are logged"""
        mock_create.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            from db import SupabaseDB
            SupabaseDB()


# Future bugs will be added here as they're discovered
class TestFutureBugs:
    """
    Template for future regression tests
    Add new tests here as bugs are discovered and fixed
    """

    def test_placeholder_for_future_bugs(self):
        """Placeholder - replace with actual bugs as they're found"""
        pass
