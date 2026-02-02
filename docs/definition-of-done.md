# Definition of Done - Pigeon

**Referenced from:** [AGENTS.md](../AGENTS.md)

This document defines the "Done" criteria for the Pigeon project. It extends the universal Agent Kernel Definition of Done with project-specific requirements.

## Agent Kernel Definition of Done

This project follows the Agent Kernel Definition of Done. **You MUST review these documents first:**

### Universal Requirements

See **[Universal Definition of Done](system-prompts/principles/definition-of-done.md)** for:
- Plan vs Reality Protocol
- Verification as Data
- Codebase State Integrity
- Agent Handoff
- Status tracking in project plans
- dev_notes/ change documentation requirements

### Python Requirements

See **[Python Definition of Done](system-prompts/languages/python/definition-of-done.md)** for:
- Python environment & dependencies
- Testing requirements (pytest)
- Code quality standards (black, type hints)
- File organization
- Coverage requirements

## Project-Specific Extensions

The following requirements are specific to Pigeon and extend the Agent Kernel DoD:

### 1. Google Drive Integration Requirements

**Mandatory Checks:**
- [ ] Google Drive API calls are properly authenticated
- [ ] OAuth flow handles token refresh correctly
- [ ] Folder path resolution works for nested folders
- [ ] File listing handles pagination (1000+ files)
- [ ] Download handles large files without corruption

**Example verification:**

```bash
# Test OAuth and folder listing
python3 -c "from pigeon.drive_client import DriveClient; from pigeon.config import Config; c = Config.from_env(); d = DriveClient(c); print(d.list_folder_files(c.drive_folder))"
```

### 2. State Management Requirements

**Mandatory Checks:**
- [ ] State file is created in tmp/pigeon-state.json
- [ ] State is loaded correctly on startup
- [ ] State is saved atomically (no corruption on crash)
- [ ] State survives file renames on Google Drive
- [ ] State file is not committed to git (.gitignore included)

**Example verification:**

```bash
# Check state file format
cat tmp/pigeon-state.json | python3 -m json.tool

# Verify it's in gitignore
grep "pigeon-state.json" .gitignore
```

### 3. Polling and File Handling Requirements

**Mandatory Checks:**
- [ ] Polling runs at configured interval
- [ ] New files are detected correctly
- [ ] Filenames are sanitized (no invalid chars)
- [ ] Timestamps are added in ISO format (YYYY-MM-DD_HH-MM-SS)
- [ ] Filename uniqueness is ensured (counter added if collision)
- [ ] Files are not re-downloaded on restart
- [ ] Errors don't stop the polling loop

**Example verification:**

```bash
# Check downloaded file naming
ls -la dev_notes/inbox/ | head -5
# Should show: 2026-02-01_HH-MM-SS_sanitized-name.ext

# Verify polling doesn't re-download
pigeon start &
sleep 5
ps aux | grep pigeon
```

### 4. Signal Handling and Graceful Shutdown

**Mandatory Checks:**
- [ ] SIGINT (Ctrl+C) triggers graceful shutdown
- [ ] SIGTERM (kill from daemon) triggers graceful shutdown
- [ ] State is saved before exit
- [ ] No in-flight downloads are lost
- [ ] Logs are written cleanly on shutdown

**Example verification:**

```bash
# Test graceful shutdown
pigeon start
# Wait for poll
# Ctrl+C
# Check logs:
tail tmp/pigeon-poller.log | grep "shutdown\|Stopping"
```

### 5. Configuration and Environment

**Mandatory Checks:**
- [ ] Configuration loads from .env file
- [ ] Environment variables override .env
- [ ] Defaults are provided for all settings
- [ ] Invalid config raises clear error messages
- [ ] Google profile directory path is validated

**Example verification:**

```bash
# Test configuration
cp .env.example .env
python3 -c "from pigeon.config import Config; c = Config.from_env(); print(f'Poll interval: {c.poll_interval}s')"

# Test invalid config
PIGEON_POLL_INTERVAL=-1 python3 -c "from pigeon.config import Config; Config.from_env()" 2>&1 | grep -i "error\|invalid"
```

### 6. Process Management (Daemon)

**Mandatory Checks:**
- [ ] `pigeon start --daemon` starts background process
- [ ] PID is saved to tmp/pigeon-poller.pid
- [ ] Logs are written to tmp/pigeon-poller.log
- [ ] `pigeon stop` sends SIGTERM and waits for graceful shutdown
- [ ] `pigeon status` correctly reports running/stopped
- [ ] Daemon logs include startup and shutdown messages

**Example verification:**

```bash
# Test daemon mode
pigeon start --daemon
sleep 2
ps aux | grep pigeon  # Should see process
pigeon status         # Should say "running"

# Check PID file
cat tmp/pigeon-poller.pid

# Check logs
tail -20 tmp/pigeon-poller.log

# Test stop
pigeon stop
sleep 1
pigeon status  # Should say "not running"
```

## Pre-Commit Checklist

Before committing, verify:

**Code Quality:**
- [ ] Black formatting applied: `black src/ tests/`
- [ ] Linting passes: `pylint src/pigeon/`
- [ ] Type hints present for all functions
- [ ] Docstrings present for public methods
- [ ] No unused imports or variables

**Testing:**
- [ ] All unit tests pass: `pytest`
- [ ] Integration tests pass or documented why skipped
- [ ] Manual testing done on new features
- [ ] No test failures on CI

**Google Drive Integration:**
- [ ] Tested with actual Google Drive folder if applicable
- [ ] No credentials or tokens committed
- [ ] OAuth flow works with fresh credentials
- [ ] Handles permission errors gracefully

**Documentation:**
- [ ] README updated for new features
- [ ] Architecture docs updated for design changes
- [ ] Implementation reference updated for new patterns
- [ ] Docstrings/comments explain non-obvious logic
- [ ] Examples provided for new features

**Commit:**
- [ ] Commit message follows format: `type: description`
- [ ] Co-Authored-By trailer included (if pair programmed)
- [ ] Changes reviewed
- [ ] Definition of Done checklist completed

## File Structure Integrity

**Mandatory Checks:**
- [ ] No .env file committed (only .env.example)
- [ ] tmp/ directory exists and contains state files
- [ ] docs/system-prompts/ is read-only
- [ ] No large files committed (> 1MB)
- [ ] src/ structure is clean and organized

**Example verification:**

```bash
# Check no secrets in git
git grep -l "API_KEY\|SECRET\|TOKEN" || echo "✓ No secrets found"

# Check file sizes
find . -type f -size +1M ! -path "./venv/*" ! -path "./.git/*"
```

## Verification Scripts

### Quick Validation

```bash
#!/bin/bash
# Run all checks

echo "=== Code Quality ==="
black --check src/ tests/ && echo "✓ Black"
pylint src/pigeon/ && echo "✓ Pylint"

echo "=== Testing ==="
pytest && echo "✓ All tests pass"

echo "=== Configuration ==="
python3 -c "from pigeon.config import Config; Config.from_env()" && echo "✓ Config valid"

echo "=== Integration ==="
# Manual tests would go here
```

### Pre-Commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

echo "Running pre-commit checks..."

# Code formatting
black src/ tests/ || exit 1

# Linting
pylint src/pigeon/ || exit 1

# Tests
pytest || exit 1

echo "✓ All checks passed"
```

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Universal DoD](system-prompts/principles/definition-of-done.md) - Agent Kernel universal requirements
- [Python DoD](system-prompts/languages/python/definition-of-done.md) - Agent Kernel Python requirements
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Code patterns
- [Workflows](workflows.md) - Development workflows

---

Last Updated: 2026-02-01
