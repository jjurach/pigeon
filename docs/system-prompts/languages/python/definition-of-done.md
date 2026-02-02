# Definition of Done: Python Specifics

This document extends the universal Definition of Done (see `docs/system-prompts/principles/definition-of-done.md`) with Python-specific criteria and tools.

## 1. Python Environment & Dependencies

**Mandatory Checks:**
- [ ] All new imports are added to `requirements.txt`
- [ ] All new imports are added to `pyproject.toml` (if project uses it)
- [ ] Dependencies are pinned to specific versions (e.g., `requests==2.31.0`)
- [ ] Virtual environment (`venv`) can be recreated cleanly from updated files
- [ ] No `pip install` commands are hardcoded; all deps are declarative
- [ ] No development-only dependencies in main requirements (use `requirements-dev.txt` if needed)

**Verification Command:**
```bash
python -m venv /tmp/test_venv
source /tmp/test_venv/bin/activate
pip install -r requirements.txt
# All imports should work without additional installations
```

## 2. Testing with pytest

**Mandatory Checks:**
- [ ] All new functions have corresponding test cases
- [ ] Tests are located in `tests/` directory matching source structure
- [ ] Tests use `pytest` framework and fixtures
- [ ] All tests pass without warnings: `pytest -v`
- [ ] Code coverage is measured (use `pytest-cov` if required)
- [ ] Mocking is used for external dependencies (API calls, file I/O, etc.)

**Verification Command:**
```bash
pytest tests/ -v --tb=short
# All tests pass, no failures or errors
```

**Coverage Check:**
```bash
pytest tests/ --cov=src/ --cov-report=term-missing
# Coverage report shows appropriate coverage levels
```

## 3. Code Quality

**Mandatory Checks:**
- [ ] Code follows PEP 8 style guide
- [ ] Type hints are present for function signatures (Python 3.6+)
- [ ] Docstrings follow project conventions (see `docs/`)
- [ ] No hardcoded credentials, API keys, or secrets
- [ ] No `print()` statements in library code (use `logging` instead)
- [ ] Error handling uses appropriate exception types

**Example of Good Style:**
```python
def process_audio(audio_path: str, sample_rate: int = 16000) -> np.ndarray:
    """
    Load and process audio file.

    Args:
        audio_path: Path to audio file
        sample_rate: Target sample rate in Hz

    Returns:
        Processed audio as numpy array

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If sample_rate is invalid
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Implementation...
```

## 4. File Organization

**Expected Structure:**
```
project/
├── src/
│   └── module_name/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── processor.py
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py (shared fixtures)
│   └── test_processor.py
├── requirements.txt
├── pyproject.toml
└── setup.py (if needed)
```

**Mandatory Checks:**
- [ ] All modules have `__init__.py`
- [ ] Test file names start with `test_`
- [ ] Test class names start with `Test`
- [ ] Test method names start with `test_`
- [ ] No circular imports

## 5. Fixtures and Mocking

**Best Practices:**
- Use `pytest` fixtures in `conftest.py` for shared test utilities
- Mock external services (APIs, databases, file systems) using `unittest.mock`
- Use `pytest-mock` for cleaner mocking: `mocker.patch()`
- Avoid real network calls; use request mocking

**Example Fixture:**
```python
# conftest.py
import pytest

@pytest.fixture
def sample_config():
    """Provide a test configuration."""
    return {
        'api_key': 'test-key',
        'timeout': 5,
        'retries': 2
    }

@pytest.fixture
def mock_api(mocker):
    """Mock external API calls."""
    return mocker.patch('module.api.Client')
```

## 6. Temporary Scripts and Cleanup

**If You Create Test Scripts:**
1. Create in a temporary directory: `tmp-verify-*.py`
2. Include the full script content in `dev_notes/changes/` documentation
3. Delete the script after verification:
   ```bash
   rm tmp-verify-*.py
   ```

**Example:**
```python
# tmp-verify-bug-123.py
import sys
sys.path.insert(0, '.')
from src.module import function

# Test code
result = function()
assert result == expected
print("✓ Bug fix verified")
```

## 7. Python Version Compatibility

**Mandatory Checks:**
- [ ] Specify minimum Python version in `pyproject.toml` or `setup.py`
- [ ] Use type hints compatible with declared version
- [ ] Test against minimum declared version
- [ ] Document Python version requirements in `README.md`

**Typical Configuration:**
```toml
[project]
python = ">=3.8"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

## 8. Common Python Tools Integration

**Pre-commit Hooks (Optional but Recommended):**
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking
- `pytest` for running tests

**Verification Command:**
```bash
# Format check
black --check src/ tests/

# Lint check
flake8 src/ tests/

# Type check
mypy src/

# All tests
pytest tests/
```

## Checklist for Python-Specific DoD

- [ ] All dependencies in `requirements.txt` and `pyproject.toml`
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code follows PEP 8 and has type hints
- [ ] No hardcoded secrets or credentials
- [ ] Docstrings present for public APIs
- [ ] `__init__.py` in all modules
- [ ] No circular imports
- [ ] Temporary scripts deleted after verification
- [ ] Python version documented and tested

