# System Architecture

This document describes the architecture of the Pigeon Google Drive polling service.

## High-Level Architecture

Pigeon is a polling service that monitors a Google Drive folder and automatically downloads new audio files to a local inbox directory. The system is designed as a lightweight, stateful polling daemon with graceful error handling and clean process management.

```
┌─────────────────────────────────────┐
│   Google Drive                      │
│   /Voice Recordings folder          │
└──────────────┬──────────────────────┘
               │
               │ DriveClient
               │ (list & download)
               │
┌──────────────▼──────────────────────┐
│   Poller (State Machine)            │
│   - Track downloaded files          │
│   - Poll at intervals               │
│   - Handle signals gracefully       │
└──────────────┬──────────────────────┘
               │
               │ Download & timestamp
               │
┌──────────────▼──────────────────────┐
│   Local Inbox                       │
│   dev_notes/inbox/                  │
│   2026-02-01_HH-MM-SS_Recording.acc │
└──────────────────────────────────────┘
               │
               │ State file
               │
┌──────────────▼──────────────────────┐
│   State Tracking                    │
│   tmp/pigeon-state.json             │
│   {file_id: metadata}               │
└──────────────────────────────────────┘
```

## Project Structure

```
modules/pigeon/
├── src/pigeon/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management (env vars, validation)
│   ├── drive_client.py       # Google Drive API integration
│   ├── poller.py             # Main polling logic and state management
│   └── main.py               # CLI entry point (start, stop, status)
├── scripts/
│   └── run-poller.sh         # Background process manager script
├── tests/
│   └── __init__.py           # Test infrastructure
├── docs/
│   ├── system-prompts/       # Agent Kernel (read-only)
│   ├── architecture.md       # This file
│   ├── workflows.md          # Project-specific workflows
│   └── definition-of-done.md # Project-specific DoD
├── tmp/                      # Runtime files (not in git)
│   ├── pigeon-state.json     # Downloaded files tracking
│   ├── pigeon-poller.pid     # Process ID
│   └── pigeon-poller.log     # Service logs
├── venv/                     # Virtual environment
├── .env.example              # Configuration template
├── .env                      # Configuration (git-ignored)
├── pyproject.toml            # Package metadata and dependencies
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── README.md                 # User documentation
├── AGENTS.md                 # Agent workflow and rules
└── .claude/CLAUDE.md         # Claude Code tool entry point
```

## Core Components

### Config (config.py)

Loads and validates configuration from environment variables and `.env` file.

**Responsibilities:**
- Load from `.env` file using python-dotenv
- Provide defaults for all settings
- Validate configuration values
- Resolve paths to absolute paths
- Manage Google profile directory paths
- Manage state file path

**Key Methods:**
- `Config.from_env()` - Load and validate configuration
- `get_profile_dir()` - Get Google profile directory
- `get_inbox_dir()` - Get absolute inbox directory path
- `get_state_file()` - Get state file path

### DriveClient (drive_client.py)

Google Drive API integration with authentication and file operations.

**Responsibilities:**
- Authenticate with Google Drive API using google-auth-oauthlib
- List files in a folder (recursive path resolution)
- Download files by ID
- Get file metadata
- Handle authentication refresh and token management

**Key Methods:**
- `__init__(config)` - Authenticate
- `list_folder_files(path)` - List files in folder
- `download_file(file_id, destination)` - Download file
- `get_file_metadata(file_id)` - Get file metadata
- `_authenticate()` - Handle OAuth flow
- `_get_folder_id(path)` - Resolve folder path to ID

**Helper Functions:**
- `sanitize_filename(original)` - Sanitize filename
- `create_timestamped_filename(original)` - Add timestamp prefix

### Poller (poller.py)

Main polling logic with state management and signal handling.

**Responsibilities:**
- Maintain polling loop with configurable interval
- Track downloaded files in JSON state file
- Compare Drive folder files against state
- Download new files to inbox
- Ensure filename uniqueness
- Handle graceful shutdown (SIGINT, SIGTERM)
- Load and save state atomically

**Key Methods:**
- `start()` - Main polling loop
- `stop()` - Stop and save state
- `_poll_once()` - Single poll cycle
- `_download_file(file_info)` - Download and update state
- `_load_state()` - Load state from file
- `_save_state()` - Save state atomically
- `_handle_signal(signum, frame)` - Signal handler

### Main (main.py)

CLI entry point with command routing.

**Commands:**
- `pigeon start` - Run poller in foreground
- `pigeon start --daemon` - Run as background daemon
- `pigeon start --verbose` - Enable debug logging
- `pigeon stop` - Stop background daemon (SIGTERM → SIGKILL)
- `pigeon status` - Check if daemon is running

**Key Functions:**
- `main()` - Parse arguments and route
- `_handle_start()` - Route to foreground or daemon
- `_start_foreground()` - Run poller interactively
- `_start_daemon()` - Fork subprocess, save PID
- `_handle_stop()` - Graceful shutdown with timeout
- `_handle_status()` - Check process status

## Data Flow

### Polling Cycle

1. **Load State** - Read `tmp/pigeon-state.json` at startup
2. **List Folder** - Call DriveClient.list_folder_files()
3. **Compare** - Find files in Drive not in state
4. **Download** - For each new file:
   - Create timestamped filename
   - Check for uniqueness (add suffix if exists)
   - Download to inbox
   - Update state with file_id and metadata
5. **Save State** - Atomically write state.json
6. **Wait** - Sleep for poll_interval seconds
7. **Repeat** - Go to step 2

### State File Format

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

**Key design:**
- Keyed by Google Drive file ID (not filename)
- Survives filename collisions
- Survives file renames on Drive
- Includes timestamps for debugging

## Authentication

### Google Drive API Setup

Pigeon uses profile-based authentication from google-personal-mcp:

1. Credentials stored in `~/.config/google-personal-mcp/profiles/{profile}/`
2. Files needed:
   - `credentials.json` - OAuth2 client secret
   - `token.json` - Access/refresh tokens (created on first auth)
3. Profiles are shareable - Pigeon and other tools can use same credentials

### Flow

1. Check if token.json exists
2. If yes, load it and try to refresh
3. If refresh fails or token doesn't exist, run OAuth flow
4. OAuth flow opens browser for user approval
5. Save token.json for future use

## Error Handling

### Transient Errors (Retried)

Errors that may be temporary:
- Network timeouts
- Google API rate limits (429)
- Temporary permission issues

**Strategy:** Log, skip file, retry on next poll cycle

### Permanent Errors (Logged, Skipped)

Errors that indicate permanent issues:
- File not found (already deleted on Drive)
- Insufficient permissions
- Destination disk full
- Invalid file type

**Strategy:** Log error, skip file, do not retry

### Signal Handling

- **SIGINT** (Ctrl+C) - Graceful shutdown
- **SIGTERM** (from daemon stop) - Graceful shutdown
- Both trigger save state before exiting

## Key Design Decisions

### 1. File ID as State Key

**Decision:** Use Google Drive file ID as state key, not filename

**Rationale:**
- Users can rename files in Drive without re-downloading
- Handle filename collisions
- Survive folder reorganization
- Detect when same file is moved/copied

### 2. Timestamped Filenames

**Decision:** Prefix downloads with ISO timestamp

**Rationale:**
- Unique per-second granularity
- Sortable chronologically
- Preserves order of downloads
- Helps with disk space management ("old files" have earlier timestamps)

### 3. Atomic State Writes

**Decision:** Write to temp file, then atomic rename

**Rationale:**
- Prevent state corruption on crash
- Ensure consistency across restarts
- Allow safe concurrent reads

### 4. Graceful Shutdown

**Decision:** Signal handlers trigger clean shutdown

**Rationale:**
- Save state before exit (no lost downloads on restart)
- Allow in-flight downloads to complete
- Clean process termination

### 5. State Persistence Over Daemon Lifecycle

**Decision:** State survives daemon restarts

**Rationale:**
- Prevents re-downloading files across restarts
- Simple to implement (just JSON file)
- User can manually reset by deleting state file

## Project-Specific Patterns

### Configuration Management

Configuration is loaded from `.env` file with validation:

```python
# Load with defaults
config = Config.from_env()

# Access validated settings
config.drive_folder        # "/Voice Recordings"
config.poll_interval       # 30 (seconds)
config.inbox_dir          # "../../dev_notes/inbox" (resolved to absolute)
config.google_profile     # "default"
```

### Path Handling

All paths are resolved to absolute paths:

```python
# Relative paths in config are resolved
inbox = config.get_inbox_dir()  # Always absolute Path object
```

### Filename Sanitization

1. Preserve extension
2. Replace spaces with hyphens
3. Remove special characters `<>:"/\|?*()`
4. Add ISO timestamp prefix
5. Ensure uniqueness by appending counter

Example:
- Original: `Recording 4.acc`
- Sanitized: `Recording-4.acc`
- Timestamped: `2026-02-01_18-55-09_Recording-4.acc`
- Unique: `2026-02-01_18-55-09_Recording-4_1.acc`

## Security Considerations

1. **Credentials:** Stored in `~/.config/google-personal-mcp/` (user-owned, secure)
2. **Token Refresh:** Automatic, with fallback to re-authentication
3. **File Permissions:** Downloads inherit inbox directory permissions
4. **State File:** Stored in `tmp/` (not committed to git)
5. **API Scope:** Uses minimal scopes (drive.readonly, drive.file)

## Performance Considerations

1. **Polling Interval:** Default 30 seconds (~2880 queries/day, well within quota)
2. **File Listing:** Paginates to 1000 files per request
3. **State File:** Loaded and saved on each poll (JSON parse/write)
4. **Folder ID Caching:** Cached for folder path resolution performance

## Extensibility

The architecture is designed for future extensions:

1. **LLM Processing:** Easy to add async processing stage after download
2. **Agent Invocation:** Can add callback system to notify agents of new files
3. **Batch Processing:** State tracking allows batching multiple files
4. **Multiple Folders:** Could extend to monitor multiple drive folders

## See Also

- [README.md](../README.md) - User documentation
- [Workflows](workflows.md) - Development workflows
- [Definition of Done](definition-of-done.md) - Quality standards
- [AGENTS.md](../AGENTS.md) - Agent workflow

---

Last Updated: 2026-02-01
