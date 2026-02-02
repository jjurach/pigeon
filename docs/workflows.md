# Project Workflows

This document describes development workflows specific to the Pigeon project.

## Core Agent Workflow

All AI agents working on this project must follow the **A-E workflow** defined in [AGENTS.md](../AGENTS.md):

- **A: Analyze** - Understand the request and declare intent
- **B: Build** - Create project plan
- **C: Code** - Implement the plan
- **D: Document** - Update documentation
- **E: Evaluate** - Verify against Definition of Done

For complete workflow documentation, see the [Agent Kernel Workflows](system-prompts/workflows/).

## Project-Specific Workflows

### Development Workflow

**When:** Starting a new feature or bug fix

**Steps:**

1. **Environment Setup**
   ```bash
   cd modules/pigeon
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Create Feature Branch** (optional, if using git branches)
   ```bash
   git checkout -b feature/description
   ```

3. **Make Changes**
   - Write code following patterns in [implementation-reference.md](implementation-reference.md)
   - Add tests for new functionality
   - Update documentation

4. **Verify Quality**
   ```bash
   # Format code
   black src/ tests/

   # Lint
   pylint src/pigeon/

   # Run tests
   pytest

   # Manual testing
   pigeon start  # Test foreground
   pigeon start --daemon  # Test daemon mode
   pigeon stop   # Test stop
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description

   - Detail 1
   - Detail 2

   Co-Authored-By: Agent Name <noreply@anthropic.com>"
   ```

### Testing Workflow

**When:** Running tests locally

**Steps:**

```bash
# Activate venv
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_config.py::test_load_from_env -v

# Run with coverage
pytest --cov=src/pigeon

# Run in watch mode (requires pytest-watch)
ptw
```

### Integration Testing Workflow

**When:** Testing with actual Google Drive folder

**Prerequisites:**
- Google Drive folder with test audio files
- google-personal-mcp credentials set up
- Pigeon configured to use test folder

**Steps:**

```bash
# 1. Configure for test folder
cp .env.example .env
# Edit .env to point to test Google Drive folder
export PIGEON_DRIVE_FOLDER="/Test Recordings"

# 2. Start polling
pigeon start --verbose

# 3. In another terminal, add files to Google Drive folder

# 4. Watch logs for downloaded files
tail -f tmp/pigeon-poller.log

# 5. Verify files downloaded
ls -la dev_notes/inbox/

# 6. Verify state file
cat tmp/pigeon-state.json | python3 -m json.tool

# 7. Stop polling
pigeon stop
```

### Daemon Management Workflow

**When:** Running Pigeon as background service

**Starting the daemon:**

```bash
# Start in background
pigeon start --daemon

# Verify it's running
pigeon status

# Check logs
tail -f tmp/pigeon-poller.log

# Monitor downloaded files
watch 'ls -la dev_notes/inbox/ | tail -10'
```

**Monitoring:**

```bash
# Check if still running
pigeon status

# View recent logs
tail -n 50 tmp/pigeon-poller.log

# Check downloaded files
cat tmp/pigeon-state.json | jq '.| length'  # Count tracked files
```

**Stopping the daemon:**

```bash
# Graceful stop (sends SIGTERM)
pigeon stop

# Verify it stopped
pigeon status

# Check final logs
tail -n 10 tmp/pigeon-poller.log
```

### Debugging Workflow

**When:** Troubleshooting issues

**Steps:**

1. **Enable Debug Logging**
   ```bash
   pigeon start --verbose
   ```

2. **Check Configuration**
   ```bash
   python3 -c "from pigeon.config import Config; c = Config.from_env(); print(f'Config: {c.__dict__}')"
   ```

3. **Check Google Drive Access**
   ```bash
   python3 -c "
   from pigeon.drive_client import DriveClient
   from pigeon.config import Config
   config = Config.from_env()
   client = DriveClient(config)
   files = client.list_folder_files(config.drive_folder)
   print(f'Found {len(files)} files')
   for f in files[:5]:
       print(f'  - {f[\"name\"]} ({f[\"id\"]})')
   "
   ```

4. **Check State File**
   ```bash
   cat tmp/pigeon-state.json | python3 -m json.tool
   ```

5. **Check Logs**
   ```bash
   tail -100 tmp/pigeon-poller.log | grep -i error
   ```

6. **Check Daemon PID**
   ```bash
   cat tmp/pigeon-poller.pid
   ps aux | grep $(cat tmp/pigeon-poller.pid)
   ```

### Releasing / Versioning Workflow

**When:** Preparing a release

**Steps:**

1. **Update Version**
   ```bash
   # Edit pyproject.toml
   # Change version = "0.x.y" to "0.x.(y+1)"
   ```

2. **Update Changelog**
   ```bash
   # Create entry in dev_notes/changes/YYYY-MM-DD_HH-MM-SS_release-notes.md
   ```

3. **Run Final Tests**
   ```bash
   pytest
   black --check src/
   pylint src/pigeon/
   ```

4. **Commit Release**
   ```bash
   git commit -m "release: v0.x.(y+1)

   [Release notes]

   Co-Authored-By: Agent Name <noreply@anthropic.com>"
   ```

## Common Commands Reference

### Configuration

```bash
# View effective configuration
python3 -c "from pigeon.config import Config; c = Config.from_env(); print(f'Folder: {c.drive_folder}\nInterval: {c.poll_interval}s\nInbox: {c.get_inbox_dir()}')"

# Test configuration validity
python3 -c "from pigeon.config import Config; Config.from_env(); print('✓ Config valid')"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pigeon --cov-report=html

# Run specific test file
pytest tests/test_config.py -v

# Run specific test
pytest tests/test_config.py::test_from_env -v

# Run tests matching pattern
pytest -k "test_auth" -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check formatting without changing
black --check src/

# Lint
pylint src/pigeon/

# Type check (if using mypy)
mypy src/pigeon/
```

### Daemon Management

```bash
# Start in foreground (Ctrl+C to stop)
pigeon start

# Start in background
pigeon start --daemon

# Start with debug logging
pigeon start --verbose

# Check status
pigeon status

# Stop background daemon
pigeon stop

# View logs
tail -f tmp/pigeon-poller.log
```

### Development

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Create fresh venv
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Clean up Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## File Structure for Changes

### Creating a New Feature

1. Create feature branch (optional)
2. Update `src/pigeon/[module].py`
3. Create `tests/test_[feature].py` with tests
4. Update `docs/implementation-reference.md` with patterns
5. Update `docs/architecture.md` if design changed
6. Update `README.md` if user-facing change
7. Commit with clear message

### Fixing a Bug

1. Create `dev_notes/debugging/YYYY-MM-DD_HH-MM-SS_bug-investigation.md`
2. Document issue and root cause
3. Fix in `src/pigeon/[module].py`
4. Add regression test
5. Verify fix works
6. Commit with reference to issue

### Documentation Changes

1. Edit documentation files in `docs/`
2. Verify cross-references work
3. Run integrity scan: `python3 docs/system-prompts/docscan.py`
4. Commit changes

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Definition of Done](definition-of-done.md) - Quality checklist
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Code patterns
- [Agent Kernel Workflows](system-prompts/workflows/) - Complete workflow documentation

---

Last Updated: 2026-02-01
