# Project Agents - Pigeon (Google Drive Polling Service)

This file defines the mandatory workflow for AI agents working on the Pigeon project.

**Quick Navigation:**
- [Definition of Done](docs/definition-of-done.md) - Quality standards
- [Architecture](docs/architecture.md) - System design
- [Implementation Reference](docs/implementation-reference.md) - Code patterns
- [Workflows](docs/workflows.md) - Project workflows
- [Templates](docs/templates.md) - Planning document templates


<!-- SECTION: MANDATORY-READING -->
# MANDATORY READING - READ FIRST, EVERY SESSION

**CRITICAL:** Before starting ANY task in this project, you MUST read these files in this exact order.

## Why These Files Are Mandatory

These files define:
- How to approach all tasks (workflow and steps)
- Quality standards (definition of done criteria)
- Project-specific rules and structure
- What actions are prohibited

**Reading these files is NOT optional. Skip them and you WILL make mistakes.**

---

## The Mandatory Reading List

### 1. Core Workflow
**File:** [docs/system-prompts/workflows/logs-first.md](workflows/logs-first.md)

**What it contains:**
- 5-step workflow (Analyze Request → Create Spec → Create Plan → Get Approval → Implement & Document)
- File naming conventions: `YYYY-MM-DD_HH-MM-SS_description.md`
- Status definitions: Draft, Approved, In Progress, Completed, WONT-DO
- The unbreakable rules
- Definition of Done principles
- How to handle uncertainties

**Why mandatory:** Defines the entire workflow for this project. Without this, you won't know how to structure your work.

---

### 2. Definition of Done
**File:** [docs/definition-of-done.md](docs/definition-of-done.md)

**What it contains:**
- Completion criteria for all tasks
- Verification requirements with proof (actual commands and output)
- Configuration integrity rules
- Quality standards
- Dependencies and configuration management

**Why mandatory:** No task is "Done" until it meets these criteria. You must know them before starting work.

---

### 3. Project-Specific Guidelines
**File:** [docs/mandatory.md](docs/mandatory.md)

**What it contains:**
- Second Voice project structure and overview
- Key documentation references
- Development guidelines (language, dependencies, code style)
- Prohibited actions specific to this project
- When to stop and ask for help

**Why mandatory:** Contains rules unique to this project. Generic knowledge isn't enough.

---

## Optional Resources (Read As Needed)

These files provide additional context when working on specific features:

- **Architecture:** [docs/architecture.md](docs/architecture.md) - System design, components, and data flow
- **Implementation Reference:** [docs/implementation-reference.md](docs/implementation-reference.md) - Code patterns, style, and conventions
- **Workflows:** [docs/workflows.md](docs/workflows.md) - Development processes and available workflow options
- **Tool Guides:** [docs/system-prompts/tools/](tools/) - Guides for Aider, Claude Code, and other tools

---

## Self-Check: Did You Really Read Them?

After reading the mandatory files, you should be able to answer:

- ✓ What are the 5 steps of the core workflow? (Hint: A, B, C, D, E)
- ✓ What timestamp format do I use for dev_notes files? (Hint: YYYY-MM-DD_HH-MM-SS)
- ✓ What are the possible status values for a Project Plan? (Hint: 5 values)
- ✓ When is a task considered "Done"? (Hint: See Definition of Done checklist)
- ✓ What directories am I NOT allowed to edit? (Hint: docs/system-prompts/)
- ✓ Where do I create temporary files? (Hint: Current directory, pattern tmp-*)
- ✓ What should I do if I'm uncertain about something? (Hint: STOP and ask)

If you can't answer these, **re-read the mandatory files now**. This isn't punishment - it's debugging.

---

**Remember:** Reading is REQUIRED, not suggested. These files are in your context for a reason.
<!-- END-SECTION -->

<!-- SECTION: PROJECT-SPECIFIC -->
## Project-Specific Rules: Polecat Tactical Execution

### 1. Your Role: Tactical Executor
- **Source of Truth:** The Bead description (provided by Mayor) and `docs/specs/` (in Town Root).
- **Mandate:** Execute the assigned Bead.
- **Workflow:**
    1.  Read the Bead (`bd show <id>`).
    2.  Create a tactical plan in `dev_notes/project_plans/` (following the Logs-First workflow).
    3.  Execute and verify.

### 2. File Organization
- **Architectural Specs:** `docs/specs/` (Mayor managed, authoritative).
- **Execution Plans:** `dev_notes/` (Polecat managed, ephemeral/tactical).

### 3. Documentation Access
- **System Prompts:** `docs/system-prompts/` (Local Copy)
- **Project Specs:** `${GT_TOWN_ROOT}/docs/specs/`
<!-- END-SECTION -->


<!-- SECTION: CORE-WORKFLOW -->
# Agent Kernel: Core Workflow & Unbreakable Rules

## 1. The Core Workflow

**MANDATORY:** For any request that involves creating or modifying code or infrastructure, you MUST follow this workflow.

**Step A: Analyze the Request & Declare Intent**
1.  **Is it a simple question?** → Answer it directly.
2.  **Is it a Trivial Change?** → Make the change directly. No documentation required.
3.  **Is it just to fix tests or to fix broken usage?** → Make the change directly. No documentation required.
4.  **Is it a Research/Documentation Change?** → Make the change directly. No project plan required, but for non-trivial documentation work, create a timestamped change log in `dev_notes/changes/` marked with `Status: ad-hoc`.
5.  **Is it anything else?** → Announce you will create a **Project Plan**.

> **Trivial Change Definition:** Non-functional changes like fixing typos in comments or code formatting.
> **Research/Documentation Change:** Requests which culminate ONLY into writes to markdown documents in the root folder or in docs/ or in `dev_notes`.
> **Non-Trivial Documentation:** Creating new documentation files, substantial rewrites, or establishing new patterns/conventions. These skip project plans but still require change documentation for the audit trail.

**Step B: Process Spec File (If Required)**
- When a prompt involves planning, represent the planning in `dev_notes/specs`
- Create a summary of what the user is asking for in `dev_notes/specs/YYYY-MM-DD_HH-MM-SS_spec-description.md` (using the timestamp-based filename format)
- If the prompt involves processing user intentions from a un-timestamped file already in `dev_notes/specs`, then rename it to match the filename format based on the file's last modified time.
  - Add any additional context as developed over follow-up conversations about the spec.
- Spec files signify user intentions and goals, and are typically used to create or update project plans.

**Step C: Create a Project Plan (If Required)**
- Use the **Project Plan Structure** defined in `docs/system-prompts/templates/structure.md`.
- The plan must be detailed enough for another agent to execute.
- Save the plan to `dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_description.md`.

**Step D: AWAIT DEVELOPER APPROVAL**
- **NEVER EXECUTE A PLAN WITHOUT EXPLICIT APPROVAL.**
- Present the full Project Plan to the developer.
- "Approved", "proceed", "go ahead", "ok", or "yes" mean you can start.
- If the developer asks questions or provides feedback, answer them and then **return to a waiting state** until you receive a new, explicit approval.
- **If approval is ambiguous** (e.g., "maybe", "I think so", "probably"): Ask a follow-up clarifying question such as "I want to confirm: should I proceed with this Project Plan? Please respond with 'yes' or 'no'."

**Step E: Implement & Document Concurrently**
- Execute the approved plan step-by-step.
- After each logical change, create or update a **Change Documentation** entry in `dev_notes/changes/`. Use the structure from your project's templates documentation.

## 2. The Unbreakable Rules

1.  **Approval is Mandatory:** This is the most important rule. Never act on a Project Plan without explicit developer approval.
2.  **Quality is Mandatory:** You MUST follow the existing code patterns, conventions, style, and typing of the files you are editing. New code should look like the old code.
3.  **Uncertainty Requires a Full Stop:** If you encounter any error, are confused by a requirement, or are unsure how to proceed, you MUST **STOP** immediately. Document the issue and ask the developer for guidance. Do not try to solve novel problems alone.
4.  **File Naming is Mandatory:**
    - All Project Plans and Change Documentation MUST use the `YYYY-MM-DD_HH-MM-SS_description.md` filename format. (See your project's documentation for the directory location.)
    - All new documentation files in `docs/` MUST use `lowercase-kebab.md` naming convention.
5.  **Temporary Files:** NEVER use `/tmp` or system temporary directories for temporary files. Always create temporary files in the current working directory using the naming patterns `tmp-*` or `*.tmp` or `tmp/*`. These files should be cleaned up when no longer needed.
6.  **Slack Notification (If Supported):** Notify using the slack-notifications MCP service each time you commit to the local git repo. **Note:** This rule applies only to agents with MCP support.
<!-- END-SECTION -->

<!-- SECTION: PRINCIPLES -->
This section is maintained by the Agent Kernel. For the complete, authoritative version, see:
- [Universal DoD](docs/system-prompts/principles/definition-of-done.md) - Agent Kernel universal requirements
- [Python DoD](docs/system-prompts/languages/python/definition-of-done.md) - Agent Kernel language requirements

**Project-specific extensions:** See [docs/definition-of-done.md](docs/definition-of-done.md)

---

# Definition of Done: Universal Principles

**MANDATORY:** No task is considered "Done" until all applicable criteria in this document are met. This document serves as the **State Transition Logic** for the project's development workflow.

## 1. The "Plan vs. Reality" Protocol

*   **Plan Consistency:**
    *   **Insignificant Deviation:** If the implementation differs slightly from the plan (e.g., helper function name change, minor logic simplification) but the *outcome* is identical, note this in the `dev_notes/changes/` entry.
    *   **Significant Deviation:** If you discover a significantly better architectural approach or a blocker that requires changing other components: **STOP**. Abort the current execution path and ask the human developer for intervention. Do not unilaterally rewrite the architecture.
*   **Plan Status:**
    *   All Project Plans in `dev_notes/project_plans/` must have a `Status` header.
    *   **Draft:** Initial state when creating the plan.
    *   **Approved:** State after human developer gives explicit approval.
    *   **Completed:** You MUST update the header to `Status: Completed` before declaring the task finished.

## 2. Verification as Data

*   **Proof of Work:**
    *   In the `dev_notes/changes/` entry, the "Verification Results" section is **mandatory**.
    *   You MUST include the **exact command** used to verify the change.
    *   You MUST include a **snippet of the terminal output** (stdout/stderr) showing success.
    *   "It works" is not acceptable. Proof is required.
*   **Temporary Tests:**
    *   If you created a temporary test script (e.g., `scripts/verify_bug_123.py`):
        1.  Run it and capture the output.
        2.  Include the **full content of the script** in the `dev_notes/changes/` entry (inside a code block).
        3.  **Delete** the temporary script from the repository.

## 3. Codebase State Integrity

*   **Dependencies:**
    *   If any new library is imported, follow your language-specific Definition of Done for dependency management (see language-specific guidance below).
*   **Configuration Drift:**
    *   If you add or modify a configuration key (e.g., `api_timeout`, `max_retries`):
        1.  Update your project's implementation documentation (e.g., `docs/implementation-reference.md`, `docs/config.md`).
        2.  Update your project's configuration example/template file (e.g., `config.example.json`, `.env.example`, `config.sample.yaml`) to include the new key with a safe default or placeholder.
    *   **Secrets:** Never hardcode secrets. Ensure they are read from env vars or config, and documented in your configuration example/template file.

## 4. The Agent Handoff

*   **Known Issues:**
    *   If the implementation is functional but has caveats (e.g., "slow on first run," "edge case X not handled"), you MUST add a **"Known Issues"** section to the `dev_notes/changes/` entry.
*   **Context Forwarding:**
    *   When starting a new task, agents are instructed to read the previous 2 change summaries to check for "Known Issues" that might impact their work.

## Checklist for "Done"

- [ ] `Status: Completed` set in Project Plan.
- [ ] `dev_notes/changes/` entry created.
- [ ] Verification command and output included in change log.
- [ ] Temporary test scripts content saved to log and file deleted.
- [ ] Dependencies updated (language-specific; see language sections below).
- [ ] Configuration example file updated (if applicable).
- [ ] `docs/` updated for new config/features.
- [ ] "Known Issues" documented.

---

## Language-Specific Requirements

### Python Projects

See `docs/system-prompts/languages/python/definition-of-done.md` for Python-specific requirements including:
- pytest test framework setup
- `requirements.txt` and `pyproject.toml` management
- Type hints and docstrings
- Test coverage requirements
<!-- END-SECTION -->

<!-- SECTION: PYTHON-DOD -->
This section is maintained by the Agent Kernel. For the complete, authoritative version, see:
- [Python DoD](docs/system-prompts/languages/python/definition-of-done.md) - Agent Kernel Python requirements

**Project-specific extensions:** See [docs/definition-of-done.md](docs/definition-of-done.md)

---

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
<!-- END-SECTION -->

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
