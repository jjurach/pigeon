# Pigeon Architecture

This document describes the architecture and design of the Pigeon automation module.

## Overview

Pigeon is a modular system for automating the ingestion, processing, and routing of voice recordings and text specifications. It consists of several independent components that work together:

```
Input Sources → Processing Pipeline → Routing → Bead Creation
                                  ↓
                            File System
```

## Component Architecture

### 1. Input Sources

Input sources are responsible for polling external systems and providing files locally.

**Supported Sources:**
- **Google Drive** (`drive_client.py`): Polls a configured folder at regular intervals
- **Slack** (planned): Listens to designated channels for messages
- **Local Files** (planned): Monitor local directories

**Key Classes:**
- `DriveClient`: Google Drive API integration
- `InputSource` (base): Abstract interface for all sources

**Interface:**
```python
class InputSource:
    def poll(self) -> Optional[SourceFile]:
        """Return new file if available."""
    def start(self) -> None:
        """Start continuous polling."""
    def stop(self) -> None:
        """Stop polling."""
```

### 2. Processing Pipeline

The processing pipeline transforms raw input files into structured specifications.

**Pipeline Stages:**

1. **STT (Speech-to-Text)**: Convert audio to text
   - Detects audio formats (m4a, mp3, wav, acc, ogg, flac)
   - Calls STT API (Whisper or Mellona)
   - Generates `.txt` transcription files

2. **Professionalization**: Improve text quality
   - Uses Mellona LLM provider for intelligent improvement
   - Fallback to basic formatting if Mellona unavailable
   - Generates `.md` specification files

**Key Classes:**
```python
class Processor(ABC):
    def process(self, file_path: Path) -> Optional[Path]:
        """Process file through this stage."""

class ProcessingPipeline:
    def process(self, file_path: Path) -> Optional[Path]:
        """Run file through all processors."""
    def get_history(self) -> List[Dict]:
        """Track processing history."""
```

**Data Flow:**
```
Audio File
    ↓
STTProcessor: audio.m4a → transcription.txt
    ↓
ProfessionalizerProcessor: transcription.txt → final-spec.md
    ↓
Output Specification
```

### 3. Project Routing

Routes processed specifications to target projects based on content analysis.

**Features:**
- Discovers available projects via git submodules
- Detects target project from file content:
  - "Project: name" header tags
  - "@project-name" mentions
  - Filename patterns
- Copies specs to target project `dev_notes/inbox/`
- Maintains archive for forensic recovery

**Key Classes:**
```python
class ProjectRouter:
    def detect_project(self, spec_file: Path) -> Optional[str]:
        """Identify target project."""
    def get_inbox_path(self, project: str) -> Path:
        """Get target inbox directory."""
    def get_archive_path(self, project: str) -> Path:
        """Get archive directory."""

class BeadCreator:
    def create(self, project_path: Path, spec_file: Path, ...) -> Optional[str]:
        """Create bead issue in target project."""
```

### 4. Main Polling Service

Coordinates all components in a continuous polling loop.

**Key Classes:**
```python
class Poller:
    def start(self) -> None:
        """Main polling loop."""
    def _poll_once(self) -> None:
        """Single poll cycle."""
    def _download_file(self, file_info: Dict) -> None:
        """Download and track files."""
```

**Workflow:**
1. Poll Google Drive for new files
2. Download files to local inbox
3. Process through pipeline
4. Route to target project
5. Create bead issue (if configured)
6. Archive original file
7. Repeat at configured interval

## Component Interactions

### Complete End-to-End Flow

```
1. DriveClient
   └─→ Lists files in Google Drive folder
       └─→ Returns: file_id, name, created_time

2. Poller
   └─→ Downloads new files to dev_notes/inbox/
       └─→ Creates timestamped filenames
           └─→ Saves file state for restart safety

3. ProcessingPipeline
   └─→ STTProcessor: audio → transcription.txt
       └─→ ProfessionalizerProcessor: transcription → spec.md

4. ProjectRouter
   └─→ Analyzes spec content
       └─→ Detects target project
           └─→ Gets target inbox path

5. BeadCreator
   └─→ Creates bead issue in target project
       └─→ Links spec file to issue

6. Cleanup
   └─→ Archives original files
       └─→ Maintains state for next run
```

## Data Structures

### State Management

**State File** (`tmp/pigeon-state.json`):
```json
{
  "google_drive_file_id": {
    "original_name": "Recording 4.acc",
    "downloaded_at": "2026-02-01T18:55:09.123456",
    "processed": true,
    "project": "second-voice"
  }
}
```

### Processing History

**Pipeline History**:
```python
{
    "input": "/path/to/audio.m4a",
    "stages": [
        {
            "processor": "stt",
            "status": "success",
            "input": "/path/to/audio.m4a",
            "output": "/path/to/transcription.txt"
        },
        {
            "processor": "professionalize",
            "status": "success",
            "input": "/path/to/transcription.txt",
            "output": "/path/to/spec.md"
        }
    ],
    "timestamp": "2026-02-01T18:55:09.123456",
    "status": "success"
}
```

## Configuration System

### Environment Variables

Primary configuration via `.env` or environment:
- `PIGEON_DRIVE_FOLDER`: Google Drive folder path
- `PIGEON_POLL_INTERVAL`: Polling frequency (seconds)
- `PIGEON_ENABLE_STT`: Enable/disable STT processing
- `PIGEON_ENABLE_PROFESSIONALIZE`: Enable/disable professionalization
- `PIGEON_MELLONA_PROFILE`: LLM profile for professionalization

### YAML Configuration

Advanced configuration via `~/.config/pigeon/config.yaml`:
```yaml
google:
  drive_folder: /Voice Recordings
  auth_profile: default

processing:
  enable_stt: true
  enable_professionalize: true
  mellona_profile: worker

polling:
  interval: 60
  timeout: 300
```

## Error Handling Strategy

### Error Categories

1. **Transient Errors** (retried):
   - Network timeouts
   - API rate limits
   - Temporary permission issues
   - Service unavailable

2. **Permanent Errors** (logged, skipped):
   - File not found
   - Invalid format
   - Insufficient permissions
   - Disk full

### Recovery Mechanisms

- **Automatic Retry**: Exponential backoff for transient errors
- **State Persistence**: Survives restarts without re-processing
- **Archive System**: Failed files moved to archive for manual review
- **Logging**: Comprehensive error logging for debugging
- **Graceful Degradation**: Continue processing despite individual file failures

## Performance Considerations

### Optimization Strategies

1. **API Call Minimization**:
   - Google Drive: ~2,880 calls/day at 30-second interval
   - Caching of submodule list
   - Rate limit awareness

2. **File Processing**:
   - Sequential processing (one file at a time)
   - Streaming where possible
   - Temporary file cleanup

3. **Polling Configuration**:
   - Default 60-second interval (configurable)
   - Backoff on consecutive failures
   - Graceful shutdown

## Security Model

### Credentials

- **Google Drive**: OAuth2 via google-personal-mcp
- **Slack**: Bot token (environment variable)
- **Never**: Credentials in git repository
- **Storage**: `~/.config/` with restricted permissions

### File Permissions

- Downloaded files: 644 (user readable, group/others readable)
- Archive: 755 (user rwx, others rx)
- Logs: 640 (user rw, group r)

### Systemd Service

- Runs as dedicated `pigeon` user
- Limited to required directories
- Resource limits enforced
- Process isolation with systemd

## Deployment Models

### 1. Development (Foreground)

```bash
cd modules/pigeon
pigeon start
```

Quick testing with visible logs.

### 2. Production (Systemd)

```bash
sudo systemctl start pigeon
sudo systemctl status pigeon
```

Full production deployment with monitoring.

### 3. Docker

```bash
docker run -d pigeon:latest
```

Container-based deployment for cloud environments.

## Testing Strategy

### Test Levels

1. **Unit Tests**: Individual components in isolation
   - Mock external APIs (Google Drive, Mellona)
   - Test error conditions
   - Verify state management

2. **Integration Tests**: Component interactions
   - End-to-end processing pipeline
   - Routing and bead creation
   - Error recovery

3. **System Tests**: Full system with mocks
   - Complete workflow simulation
   - Performance under load

### Coverage Goals

- Core modules: ≥80% code coverage
- Error paths: All major error cases tested
- Edge cases: File handling, naming conflicts, etc.

## Future Architecture Enhancements

### Planned Improvements

1. **Slack Integration**: Listen to Slack messages
2. **Batch Processing**: Optimize for high-volume scenarios
3. **Advanced Routing**: ML-based project detection
4. **Webhook Notifications**: Real-time processing events
5. **Admin Dashboard**: Web UI for monitoring

### Migration Path

Pigeon is designed as a **temporary solution**. When more sophisticated orchestration is needed:

- **n8n**: Low-code workflow automation
- **Apache Airflow**: DAG-based orchestration
- **Temporal**: Distributed workflow engine

Key design patterns support easy migration:
- Modular components
- Clear data boundaries
- State files in standard formats
- Documented integration points

## Related Documents

- [README.md](../README.md) - User guide and quick start
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment guide
- [Processes and Workflows](../../docs/system-prompts/workflows/) - System prompt documentation

---

**Last Updated:** 2026-02-20
**Status:** Production Ready (MVP)
