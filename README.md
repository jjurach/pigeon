# Pigeon: Google Drive Polling Service

Pigeon is a Python service that polls a Google Drive folder at regular intervals, downloads new audio files with timestamped filenames, and stores them in a local inbox directory. This MVP implementation provides the foundation for processing voice recordings and integrating with downstream systems.

## Table of Contents

- [Overview](#overview)
- [MVP Features](#mvp-features)
- [Medium-Term Vision](#medium-term-vision)
- [Long-Term Vision](#long-term-vision)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

## Overview

Pigeon serves as a bridge between Google Drive and local processing systems. It provides:

- **Continuous polling** of a designated Google Drive folder at configurable intervals (default: 30 seconds)
- **Automatic downloads** of new audio files with timestamped, sanitized filenames
- **State tracking** to prevent duplicate downloads across restarts
- **Graceful error handling** with retry logic for transient failures
- **Background service** management with status monitoring and logging

### Use Case

Store audio recordings in Google Drive's `/Voice Recordings` folder. Pigeon automatically downloads them to your local `dev_notes/inbox/` directory for processing. Files are renamed with timestamps to ensure uniqueness and readability:

- Original: `Recording 4.acc`
- Downloaded as: `2026-02-01_18-55-09_Recording-4.acc`

## MVP Features

The MVP implementation includes:

### Polling Service
- Polls Google Drive folder every 30 seconds (configurable)
- Detects new files by comparing against downloaded state
- Downloads files only once

### File Management
- **Timestamped filenames**: `YYYY-MM-DD_HH-MM-SS_sanitized-name.ext`
- **Sanitized filenames**: Spaces replaced with hyphens, special characters removed
- **Unique filename handling**: Automatic suffix addition if file exists
- **Atomic state persistence**: Safe across restarts

### Authentication
- Profile-based Google authentication via `~/.config/google-personal-mcp/`
- Reuses credentials from google-personal-mcp setup
- Automatic token refresh with fallback re-authentication

### CLI Interface
- `pigeon start` - Run in foreground
- `pigeon start --daemon` - Run as background process
- `pigeon stop` - Stop background process
- `pigeon status` - Check process status
- `pigeon start --verbose` - Enable debug logging

### Background Management
- PID tracking in `tmp/pigeon-poller.pid`
- Centralized logging in `tmp/pigeon-poller.log`
- Shell script wrapper for service-style management:
  ```bash
  ./scripts/run-poller.sh start    # Start in background
  ./scripts/run-poller.sh stop     # Stop gracefully
  ./scripts/run-poller.sh status   # Check status
  ./scripts/run-poller.sh restart  # Restart service
  ```

### Error Handling
- Graceful signal handling (SIGINT, SIGTERM)
- Retry logic with exponential backoff
- Comprehensive logging for debugging
- Continues polling even if individual downloads fail

### State Tracking
- Tracks downloaded files by Google Drive file ID
- Includes original filename and download timestamp
- Persisted in `tmp/pigeon-state.json`
- Survives restarts without re-downloading

## Medium-Term Vision

Future enhancements planned for Pigeon:

### 1. LLM Processing

Automatically process audio files with an LLM provider (OpenRouter or local Ollama):

```
Audio File Download
       ↓
LLM Processing (with system prompt)
       ↓
Result File (.result extension)
       ↓
Inbox Item Marked as Processed
```

**Implementation considerations:**
- Need consistent interface across projects for LLM calls
- Consider: Should `oneshot` become a shared library?
- Consider: Use Python LLM library for multi-provider support?

### 2. Agent Integration

Automatically invoke processing agents:

```
Downloaded File
       ↓
Generate .result from LLM
       ↓
Invoke Agent: "process this inbox item"
       ↓
Downstream Processing
```

**Requirements:**
- Define agent interface for inbox processing
- Determine notification mechanism
- Handle agent success/failure responses

### 3. Batch Processing

Process multiple files as a batch to improve efficiency:

- Collect files over a time window
- Process batch with single LLM call
- Generate combined results

**Tradeoffs:**
- Latency vs. throughput
- API cost efficiency
- State management complexity

## Long-Term Vision

Pigeon is intentionally designed as a **temporary orchestration solution**. Future architectural decisions may replace it:

- **n8n**: Low-code workflow automation
- **Apache Airflow**: Scalable DAG orchestration
- **Temporal**: Reliable distributed workflows
- **Custom event system**: Direct integration with hentown

Pigeon's simple, focused implementation supports easy migration to these platforms when needed. The state file and file naming conventions are designed to survive system changes.

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Drive API credentials (from google-personal-mcp setup)
- Virtual environment

### Step 1: Clone/Access the Module

```bash
cd modules/pigeon
```

### Step 2: Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Package

```bash
pip install -e .
```

Or for development (includes testing tools):

```bash
pip install -e ".[dev]"
```

### Step 4: Verify Installation

```bash
pigeon start --help
```

## Configuration

### Environment Variables

Pigeon uses environment variables for configuration. Copy `.env.example` to `.env` and modify:

```bash
cp .env.example .env
```

#### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `PIGEON_DRIVE_FOLDER` | `/Voice Recordings` | Google Drive folder path to monitor |
| `PIGEON_POLL_INTERVAL` | `30` | Polling interval in seconds |
| `PIGEON_INBOX_DIR` | `../../dev_notes/inbox` | Local directory for downloaded files |
| `PIGEON_GOOGLE_PROFILE` | `default` | Google auth profile name |

### Google Drive Authentication

Pigeon reuses authentication from `google-personal-mcp`. Set up authentication once:

1. **Install google-personal-mcp:**
   ```bash
   pip install google-personal-mcp
   ```

2. **Set up default profile:**
   ```bash
   mkdir -p ~/.config/google-personal-mcp/profiles/default
   ```

3. **Authenticate:**
   Follow google-personal-mcp instructions to create `credentials.json` and `token.json` in the profile directory.

4. **Verify:**
   ```bash
   ls ~/.config/google-personal-mcp/profiles/default/
   # Should show: credentials.json, token.json
   ```

Pigeon will automatically reuse these credentials. Both applications can safely share the same profile.

### Custom Profiles

To use a different Google profile:

```bash
export PIGEON_GOOGLE_PROFILE=my_profile
```

Ensure the profile directory exists with valid credentials.

## Usage

### Run in Foreground (Development)

Monitor logs in real-time:

```bash
pigeon start
```

Stop with `Ctrl+C`.

### Run in Background (Production)

Using Python CLI:

```bash
pigeon start --daemon
pigeon status
pigeon stop
```

Using shell script:

```bash
./scripts/run-poller.sh start
./scripts/run-poller.sh status
./scripts/run-poller.sh stop
./scripts/run-poller.sh restart
```

### Enable Debug Logging

For troubleshooting:

```bash
pigeon start --verbose
```

Or in daemon mode:

```bash
./scripts/run-poller.sh start
tail -f tmp/pigeon-poller.log --verbose
```

### Check Logs

View recent logs:

```bash
tail -n 20 tmp/pigeon-poller.log
```

Follow logs in real-time:

```bash
tail -f tmp/pigeon-poller.log
```

### Monitor State

View downloaded files:

```bash
cat tmp/pigeon-state.json | jq .
```

## Architecture

### Module Structure

```
modules/pigeon/
├── src/pigeon/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── drive_client.py       # Google Drive API integration
│   ├── poller.py             # Main polling logic
│   └── main.py               # CLI entry point
├── scripts/
│   └── run-poller.sh         # Background process manager
├── tmp/                      # Runtime files (not in git)
│   ├── pigeon-state.json     # Downloaded files tracking
│   ├── pigeon-poller.pid     # Process ID
│   └── pigeon-poller.log     # Service logs
└── README.md
```

### Data Flow

```
Google Drive
    ↓
DriveClient (list files, download)
    ↓
Poller (track state, handle downloads)
    ↓
Local Filesystem (dev_notes/inbox/)
    ↓
State File (tmp/pigeon-state.json)
```

### State Management

State file format (`tmp/pigeon-state.json`):

```json
{
  "file_id_1": {
    "original_name": "Recording 4.acc",
    "downloaded_at": "2026-02-01T18:55:09.123456"
  },
  "file_id_2": {
    "original_name": "Voice Note.m4a",
    "downloaded_at": "2026-02-01T19:00:15.654321"
  }
}
```

**Key points:**
- Keyed by Google Drive file ID (not filename)
- Survives filename collisions
- Includes timestamps for debugging
- Atomic writes prevent corruption

### Filename Sanitization

Algorithm:

1. Preserve file extension: `Recording 4.acc` → `name="Recording 4"`, `ext=".acc"`
2. Replace spaces with hyphens: `Recording 4` → `Recording-4`
3. Remove special characters: `<>:"/\|?*()` removed
4. Add timestamp prefix: `2026-02-01_18-55-09_Recording-4.acc`
5. Ensure uniqueness: Add suffix if file exists: `2026-02-01_18-55-09_Recording-4_1.acc`

### Error Handling

**Transient Errors (Retried):**
- Network timeouts
- Google API rate limits
- Temporary permission issues

**Permanent Errors (Logged, Skipped):**
- File not found (already deleted on Drive)
- Insufficient permissions
- Destination disk full
- Invalid file type

**Recovery:**
- Errors logged but don't stop polling
- Failed downloads skipped (not added to state)
- Next poll will retry from current state

## Troubleshooting

### Authentication Issues

**Error:** `credentials.json not found`

**Solution:**
1. Ensure google-personal-mcp is set up:
   ```bash
   ls ~/.config/google-personal-mcp/profiles/default/
   ```

2. If missing, create credentials:
   ```bash
   mkdir -p ~/.config/google-personal-mcp/profiles/default
   # Follow google-personal-mcp setup instructions
   ```

**Error:** `Failed to refresh token`

**Solution:**
Pigeon will automatically re-authenticate. If repeated:
1. Delete the old token: `rm ~/.config/google-personal-mcp/profiles/default/token.json`
2. Restart pigeon to trigger fresh authentication

### Folder Not Found

**Error:** `Folder not found: /Voice Recordings`

**Solution:**
1. Verify folder exists in Google Drive
2. Check folder name spelling and path
3. Ensure you have read access to the folder
4. Update `PIGEON_DRIVE_FOLDER` environment variable if needed

### Files Not Being Downloaded

**Cause:** Pigeon not detecting new files

**Debug Steps:**
1. Check pigeon is running: `pigeon status` or `./scripts/run-poller.sh status`
2. View logs: `tail -f tmp/pigeon-poller.log`
3. Check state file: `cat tmp/pigeon-state.json`
4. Verify drive folder has files (not symlinks)
5. Run with verbose logging: `pigeon start --verbose`

### High API Usage

**Cause:** Frequent polling increases API quota usage

**Solution:**
- Increase polling interval in `.env`:
  ```bash
  PIGEON_POLL_INTERVAL=60
  ```
- Note: At 30-second intervals, ~2,880 queries/day (well within quota)

### Disk Space Issues

**Error:** `No space left on device`

**Solution:**
1. Check inbox directory: `du -sh dev_notes/inbox/`
2. Archive old files to external storage
3. Adjust `PIGEON_INBOX_DIR` to different location if needed

### Background Process Won't Start

**Error:** `Virtual environment not found`

**Solution:**
1. Ensure virtual environment is created:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. Check script runs from project root:
   ```bash
   cd modules/pigeon
   ./scripts/run-poller.sh start
   ```

### Process Remains After Stop

**If:** `./scripts/run-poller.sh stop` doesn't fully stop

**Debug:**
1. Check process manually: `ps aux | grep pigeon`
2. Force kill: `./scripts/run-poller.sh stop && sleep 2 && ./scripts/run-poller.sh stop`
3. View logs for shutdown errors: `tail -n 50 tmp/pigeon-poller.log`

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/pigeon
```

### Code Style

Format code with black:

```bash
black src/pigeon/ scripts/
```

### Adding Features

1. Follow existing patterns in source modules
2. Add type hints to all functions
3. Include docstrings for public APIs
4. Update state tracking if changing file storage
5. Test with actual Google Drive folder

## Future Development

### Short-Term
- [ ] Comprehensive test suite with mocked Google API
- [ ] Handle file modification detection
- [ ] Checksum tracking for file integrity
- [ ] Config file support (YAML/TOML)

### Medium-Term
- [ ] LLM processing integration
- [ ] Agent invocation framework
- [ ] Batch processing optimizations
- [ ] Admin dashboard for monitoring

### Long-Term
- [ ] Migration to orchestration platform
- [ ] Multi-folder support
- [ ] Cloud storage backends (S3, Azure)
- [ ] Webhook notifications for pipeline integration

## Contributing

Please follow the project patterns:

1. **Code Style:** Black formatter, type hints, docstrings
2. **Testing:** Add tests for new functionality
3. **Documentation:** Update README for user-visible changes
4. **Commits:** Clear messages describing changes

## License

Part of the hentown project.

## Support

For issues and questions:

1. Check logs: `tail -f tmp/pigeon-poller.log`
2. Review troubleshooting section above
3. Enable verbose logging: `pigeon start --verbose`
4. Check state file for anomalies: `cat tmp/pigeon-state.json`

---

**Status:** MVP Implementation (v0.1.0)
**Created:** 2026-02-01
**Maintained as:** Temporary orchestration solution
