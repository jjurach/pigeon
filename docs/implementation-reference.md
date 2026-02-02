# Implementation Reference

This document provides practical implementation patterns and reference implementations for Pigeon.

## Quick Reference

- **Configuration Loading**: See [Configuration Pattern](#configuration-pattern)
- **Google Drive Authentication**: See [OAuth Pattern](#oauth-pattern)
- **File Downloading**: See [File Downloading Pattern](#file-downloading-pattern)
- **State Management**: See [State Management Pattern](#state-management-pattern)
- **Error Handling**: See [Error Handling Pattern](#error-handling-pattern)

## Configuration Pattern

**Use Case:** Loading configuration from environment and `.env` file

**Implementation:**

```python
from pigeon.config import Config

# Load configuration with validation
config = Config.from_env()

# Access validated settings
print(config.drive_folder)      # "/Voice Recordings"
print(config.poll_interval)     # 30 (seconds)
print(config.get_inbox_dir())   # Absolute Path
print(config.get_state_file())  # Absolute Path
```

**Configuration file** (`.env`):

```bash
PIGEON_DRIVE_FOLDER=/Voice Recordings
PIGEON_POLL_INTERVAL=30
PIGEON_INBOX_DIR=../../dev_notes/inbox
PIGEON_GOOGLE_PROFILE=default
```

**Key Points:**
- All paths are resolved to absolute paths
- Inbox directory is created if it doesn't exist
- Google profile directory must exist (from google-personal-mcp)
- Validation raises ValueError if config is invalid

## OAuth Pattern

**Use Case:** Authenticating with Google Drive API using stored credentials

**Implementation:**

```python
from pigeon.drive_client import DriveClient
from pigeon.config import Config

config = Config.from_env()
client = DriveClient(config)  # Authenticates during __init__

# Now client.service is ready to use
files = client.list_folder_files("/Voice Recordings")
```

**Authentication Flow:**

1. Load `token.json` if it exists
2. Try to refresh token
3. If refresh fails or token doesn't exist, run OAuth flow
4. OAuth opens browser for user approval
5. Save token.json for future use

**Key Points:**
- Authentication happens in `__init__`
- Reuses credentials from google-personal-mcp
- Both tools can share the same profile
- Token refresh is automatic

## File Downloading Pattern

**Use Case:** Download a file from Google Drive with timestamped, unique filename

**Implementation:**

```python
from pigeon.drive_client import (
    DriveClient,
    create_timestamped_filename,
    sanitize_filename
)
from pigeon.config import Config

config = Config.from_env()
client = DriveClient(config)

# List files in folder
files = client.list_folder_files("/Voice Recordings")

for file_info in files:
    file_id = file_info["id"]
    original_name = file_info["name"]

    # Create timestamped filename
    timestamped_name = create_timestamped_filename(original_name)

    # Destination path
    destination = config.get_inbox_dir() / timestamped_name

    # Ensure uniqueness
    counter = 1
    original_dest = destination
    while destination.exists():
        name, ext = original_dest.name.rsplit(".", 1) if "." in original_dest.name else (original_dest.name, "")
        if ext:
            destination = original_dest.parent / f"{name}_{counter}.{ext}"
        else:
            destination = original_dest.parent / f"{name}_{counter}"
        counter += 1

    # Download
    client.download_file(file_id, str(destination))
```

**Filename Examples:**

```
Original:    "Recording 4.acc"
Sanitized:   "Recording-4.acc"
Timestamped: "2026-02-01_18-55-09_Recording-4.acc"
Unique:      "2026-02-01_18-55-09_Recording-4_1.acc" (if file exists)
```

**Key Points:**
- Timestamp is ISO format: `YYYY-MM-DD_HH-MM-SS`
- Spaces are replaced with hyphens
- Special characters are removed
- Extension is preserved
- Uniqueness is ensured by appending counter

## State Management Pattern

**Use Case:** Track downloaded files across restarts using JSON state file

**Implementation:**

```python
import json
from pathlib import Path
from datetime import datetime

# Load state
state_file = Path("tmp/pigeon-state.json")
if state_file.exists():
    with open(state_file, "r") as f:
        state = json.load(f)
else:
    state = {}

# Add downloaded file
file_id = "some_file_id"
state[file_id] = {
    "original_name": "Recording.acc",
    "downloaded_at": datetime.now().isoformat()
}

# Save state atomically (write to temp, then rename)
temp_file = state_file.with_suffix(".json.tmp")
with open(temp_file, "w") as f:
    json.dump(state, f, indent=2)
temp_file.replace(state_file)  # Atomic rename
```

**State File Format:**

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

**Key Points:**
- Keyed by Google Drive file ID (not filename)
- Survives filename collisions and renames
- Timestamps help with debugging
- Atomic writes prevent corruption
- State file is in .gitignore (not committed)

## Error Handling Pattern

**Use Case:** Handle transient vs permanent errors gracefully

**Implementation:**

```python
import logging

logger = logging.getLogger(__name__)

def download_file(file_id, original_name, destination):
    """Download file with error handling."""
    try:
        # Attempt download
        client.download_file(file_id, str(destination))

        # Success - update state
        state[file_id] = {
            "original_name": original_name,
            "downloaded_at": datetime.now().isoformat()
        }
        logger.info(f"Downloaded '{original_name}' to '{destination.name}'")

    except Exception as e:
        # Log error but don't stop polling
        logger.error(f"Failed to download file {file_id} ({original_name}): {e}")
        # Don't add to state - will retry on next poll cycle
        # Continue to next file
```

**Error Categories:**

**Transient (Retried):**
- Network timeouts
- Rate limit (429)
- Temporary permission issues

**Strategy:** Log, skip file, retry on next poll

**Permanent (Logged, Skipped):**
- File not found (deleted on Drive)
- Insufficient permissions
- Disk full
- Invalid file type

**Strategy:** Log error, skip file, don't retry

**Key Points:**
- Errors logged but don't stop polling
- Failed files not added to state (automatic retry)
- Logging includes context (file ID, name, error)
- Continues with next file after error

## Polling Pattern

**Use Case:** Main polling loop with graceful shutdown

**Implementation:**

```python
import signal
import time
import logging

logger = logging.getLogger(__name__)

class Poller:
    def __init__(self, config, drive_client):
        self.running = False
        self.config = config
        self.drive_client = drive_client
        self.state = {}

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def start(self):
        """Main polling loop."""
        logger.info("Starting poller")
        self.running = True

        try:
            while self.running:
                self._poll_once()
                time.sleep(self.config.poll_interval)
        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)
        finally:
            self.stop()

    def _poll_once(self):
        """Single poll cycle."""
        try:
            # List files
            files = self.drive_client.list_folder_files(self.config.drive_folder)

            # Find new files
            new_files = [f for f in files if f["id"] not in self.state]

            if new_files:
                logger.info(f"Found {len(new_files)} new file(s)")

            # Download new files
            for file_info in new_files:
                self._download_file(file_info)

        except Exception as e:
            logger.error(f"Error in poll cycle: {e}", exc_info=True)

    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully")
        self.stop()

    def stop(self):
        """Stop and save state."""
        logger.info("Stopping poller")
        self.running = False
        self._save_state()
```

**Key Points:**
- Loop runs while `running` is True
- Errors logged but don't stop polling
- Signal handlers set `running = False`
- State saved before exit
- Sleep interval is configurable

## Signal Handling Pattern

**Use Case:** Graceful shutdown on SIGINT (Ctrl+C) or SIGTERM (daemon stop)

**Implementation:**

```python
import signal
import os

def setup_signal_handlers(callback):
    """Register signal handlers."""
    signal.signal(signal.SIGINT, callback)   # Ctrl+C
    signal.signal(signal.SIGTERM, callback)  # Kill signal

def shutdown_handler(signum, frame):
    """Handle termination signal."""
    logger.info(f"Received signal {signum}, shutting down gracefully")
    # Set flag to stop main loop
    global RUNNING
    RUNNING = False
    # Don't exit immediately - let main loop finish current iteration
```

**Usage in Daemon:**

```bash
# Start daemon
pigeon start --daemon

# Daemon saves PID to tmp/pigeon-poller.pid
# Stop daemon sends SIGTERM
pigeon stop

# daemon_start.py handles signal and saves state
```

**Key Points:**
- SIGINT for foreground (Ctrl+C)
- SIGTERM for daemon (kill signal)
- Both trigger graceful shutdown
- State saved before exit

## Testing Patterns

### Configuration Testing

```python
def test_config_loading():
    """Test configuration loading."""
    config = Config.from_env()
    assert config.poll_interval > 0
    assert config.get_inbox_dir().exists()
    assert config.get_profile_dir().exists()

def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValueError):
        config = Config(
            poll_interval=-1,  # Invalid
            inbox_dir="invalid",
            drive_folder="/",
            google_profile="default"
        )
        config.validate()
```

### Mocking Google Drive

```python
from unittest.mock import Mock, patch

def test_list_files_with_mock():
    """Test file listing with mocked Drive API."""
    mock_service = Mock()
    mock_service.files().list().execute.return_value = {
        "files": [
            {"id": "file1", "name": "Recording.acc", "mimeType": "audio/x-acc"}
        ]
    }

    config = Config.from_env()
    client = DriveClient(config)
    client.service = mock_service

    files = client.list_folder_files("/Voice Recordings")
    assert len(files) == 1
    assert files[0]["name"] == "Recording.acc"
```

### State Management Testing

```python
def test_state_atomic_write():
    """Test state is written atomically."""
    state_file = Path("tmp/test-state.json")

    # Simulate atomic write
    temp_file = state_file.with_suffix(".json.tmp")
    state = {"file_id": {"original_name": "test.acc"}}

    with open(temp_file, "w") as f:
        json.dump(state, f)
    temp_file.replace(state_file)

    # Verify written correctly
    with open(state_file, "r") as f:
        loaded = json.load(f)
    assert loaded == state
```

## See Also

- [Architecture](architecture.md) - System design
- [Workflows](workflows.md) - Development workflows
- [Definition of Done](definition-of-done.md) - Quality standards
- [README.md](../README.md) - User documentation

---

Last Updated: 2026-02-01
