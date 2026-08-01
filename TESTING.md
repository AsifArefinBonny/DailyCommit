# DailyCommit Testing Guide

Complete testing documentation for the DailyCommit project.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Coverage Requirements](#coverage-requirements)
- [Adding New Tests](#adding-new-tests)
- [CI/CD Integration](#cicd-integration)

## 🚀 Quick Start

```bash
# Run all tests
./run_tests.sh

# Run with coverage report
./run_tests.sh coverage

# Run only unit tests (fast)
./run_tests.sh unit

# Run only integration tests
./run_tests.sh integration

# Run only regression tests
./run_tests.sh regression

# Quick smoke test
./run_tests.sh quick
```

## 📁 Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_groq_client.py  # Groq API client tests
│   ├── test_db.py           # Database operations
│   └── test_models.py       # Pydantic model validation
│
├── integration/             # Integration tests (multiple components)
│   └── test_daily_lesson_workflow.py  # End-to-end lesson generation
│
├── regression/              # Tests for previously found bugs
│   └── test_bugs_found.py   # All historical bugs
│
├── fixtures/                # Test data and mocks
│
└── requirements.txt         # Test dependencies
```

## 🧪 Test Categories

### Unit Tests
**Purpose**: Test individual components in isolation
**Speed**: Fast (<1s per test)
**Dependencies**: None (mocked)

**Coverage**:
- ✅ Groq API client (retry logic, error handling, validation)
- ✅ Database operations (CRUD, error handling)
- ✅ Pydantic models (validation, serialization)

**Example**:
```python
def test_groq_client_retry_logic(self):
    """Test that client retries on rate limit"""
    # Mock rate-limited response
    # Verify retry happens
    # Verify eventually succeeds
```

### Integration Tests
**Purpose**: Test complete workflows
**Speed**: Medium (5-10s per test)
**Dependencies**: Multiple components

**Coverage**:
- ✅ Daily lesson generation workflow
- ✅ Topic selection and weighting
- ✅ Database persistence
- ✅ Telegram notification

**Example**:
```python
def test_full_lesson_generation_flow(self):
    """Test from config → LLM → DB → Telegram"""
    # Mock all external services
    # Run complete workflow
    # Verify all steps executed correctly
```

### Regression Tests
**Purpose**: Ensure bugs don't reoccur
**Speed**: Fast to medium
**Coverage**: All historically found bugs

**Bugs Tested**:
1. ✅ Config file path error (relative vs absolute)
2. ✅ httpx version conflict
3. ✅ OpenRouter model availability
4. ✅ Question type validation
5. ✅ Supabase env var naming
6. ✅ Webhook JWT authentication
7. ✅ Git branch defaults
8. ✅ Secrets not committed
9. ✅ Database connection errors

## 📊 Coverage Requirements

| Component | Target Coverage | Current |
|-----------|----------------|---------|
| `groq_client.py` | 80% | - |
| `db.py` | 80% | - |
| `models.py` | 90% | - |
| `generate_daily.py` | 70% | - |
| **Overall** | **70%** | - |

View coverage report:
```bash
./run_tests.sh coverage
open htmlcov/index.html
```

## ➕ Adding New Tests

### When to Add Tests

1. **New Feature**: Write tests FIRST (TDD)
2. **Bug Fixed**: Add regression test IMMEDIATELY
3. **Refactoring**: Ensure existing tests still pass
4. **Code Review**: Check test coverage

### How to Add Tests

#### 1. Unit Test Template

```python
# tests/unit/test_new_module.py
"""
Unit tests for new_module
Description of what this module does
"""
import pytest
from unittest.mock import Mock, patch
from bot.new_module import NewClass


class TestNewClass:
    """Test NewClass functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.instance = NewClass()

    def test_feature_works(self):
        """Test that the main feature works"""
        result = self.instance.do_something()
        assert result == expected_value

    def test_error_handling(self):
        """Test error cases"""
        with pytest.raises(SomeError):
            self.instance.do_invalid_thing()
```

#### 2. Regression Test Template

```python
# tests/regression/test_bugs_found.py

class TestBugXYZ:
    """
    BUG: Short description
    ERROR: Exact error message
    FIX: How it was fixed
    """

    def test_bug_xyz_fixed(self):
        """Test that bug XYZ doesn't reoccur"""
        # Reproduce the bug scenario
        # Verify it's fixed
        assert expected_behavior
```

#### 3. Integration Test Template

```python
# tests/integration/test_new_workflow.py

class TestNewWorkflow:
    """Test new end-to-end workflow"""

    @patch('module.external_dependency')
    def test_complete_flow(self, mock_dep):
        """Test complete workflow from start to finish"""
        # Mock external dependencies
        # Run workflow
        # Verify all steps
        assert workflow_completed
```

## 🔄 CI/CD Integration

Tests run automatically on:
- ✅ Every commit to `main`
- ✅ Every pull request
- ✅ Daily at 9:00 AM UTC

### GitHub Actions Workflow

Located at: `.github/workflows/test.yml`

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r bot/requirements.txt
          pip install -r tests/requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=bot --cov-fail-under=70
```

### Pre-commit Hook (Optional)

Run tests before each commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash
./run_tests.sh quick || exit 1
```

## 🐛 Testing Checklist for Bug Fixes

When fixing a bug:

- [ ] Reproduce the bug with a failing test
- [ ] Fix the bug
- [ ] Verify test now passes
- [ ] Add test to regression suite
- [ ] Document in `test_bugs_found.py`
- [ ] Update this README if needed

## 📝 Test Writing Best Practices

### DO ✅

- **Test one thing** per test function
- **Use descriptive names**: `test_retry_on_rate_limit` not `test_1`
- **Mock external dependencies**: No real API calls, DB connections
- **Test edge cases**: Empty inputs, null values, max limits
- **Test error paths**: Not just happy path
- **Keep tests fast**: Unit tests < 1s each
- **Use fixtures**: Share setup code via `setup_method()`

### DON'T ❌

- **Test implementation details**: Test behavior, not internals
- **Make tests depend on each other**: Each test should be independent
- **Hardcode values**: Use variables and constants
- **Skip flaky tests**: Fix them or remove them
- **Test external services**: Always mock APIs, databases
- **Write mega-tests**: Split into smaller, focused tests

## 🔍 Debugging Failed Tests

```bash
# Run with verbose output
pytest tests/unit/test_module.py -v

# Run specific test
pytest tests/unit/test_module.py::TestClass::test_method -v

# Show print statements
pytest tests/ -v -s

# Drop into debugger on failure
pytest tests/ --pdb

# Show full traceback
pytest tests/ --tb=long
```

## 📈 Coverage Analysis

```bash
# Generate HTML report
pytest --cov=bot --cov-report=html
open htmlcov/index.html

# Show missing lines
pytest --cov=bot --cov-report=term-missing

# Fail if coverage below 70%
pytest --cov=bot --cov-fail-under=70
```

## 🎯 Future Testing Improvements

- [ ] Add load testing for API endpoints
- [ ] Add end-to-end tests with real Telegram
- [ ] Add performance benchmarks
- [ ] Add mutation testing
- [ ] Add contract tests for external APIs
- [ ] Add visual regression tests for dashboard

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Mocking Guide](https://docs.python.org/3/library/unittest.mock.html)

## ❓ FAQ

**Q: How do I run tests locally?**
A: `./run_tests.sh` or `pytest tests/`

**Q: Tests are slow, how to speed up?**
A: Run only unit tests: `./run_tests.sh unit`

**Q: How do I add a new test?**
A: Follow templates above, run `pytest` to verify

**Q: CI is failing but tests pass locally?**
A: Check Python version, dependencies, environment variables

**Q: How do I test new API integrations?**
A: Always mock external APIs, test error cases

---

**Remember**: Good tests are your safety net. They let you refactor with confidence and catch bugs before users do! 🛡️
