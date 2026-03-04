# Python Provider Integration: Subprocess AI Agents

**Purpose:** Patterns for implementing and testing Python providers that execute AI agents
as subprocess workers, using hatchery's `BaseProvider` ABC as the reference implementation.

**Basis:** Phase 4 (Gemini Provider) implementation from the hatchery-improvements epic.

**Status:** Active ✓

---

## 1. The BaseProvider ABC

All subprocess providers must implement three required methods:

```python
from hatchery.providers.base import BaseProvider, ExecutionResult, AgentEvent

class MyProvider(BaseProvider):
    def execute_bead(self, bead_id: str) -> ExecutionResult: ...  # sync mode
    def is_available(self) -> bool: ...                           # binary availability check
    def get_name(self) -> str: ...                               # human-readable name
```

Optionally override the async interface for concurrent execution:

```python
    def spawn(self, bead_id: str, db_path: Path, context: dict) -> int: ...  # returns PID
    def stream_events(self, pid: int) -> Iterator[AgentEvent]: ...
    def wait(self, pid: int, bead_id: str, db_path: Path, timeout: Optional[int] = None) -> ExecutionResult: ...
```

---

## 2. Gemini CLI Provider Pattern

### Invocation

```bash
gemini --yolo --output-format stream-json --model <model> -p "<prompt>"
```

**Required flags:**
- `--yolo`: Skip interactive confirmation prompts. **MANDATORY for non-interactive (orchestrated) use.** Without this, gemini may pause and wait for user input, causing the bead to hang indefinitely.
- `--output-format stream-json`: Structured streaming output. See §3 for how this is used.
- `--model <model>`: Model selection (e.g., `auto`, `gemini-2.5-pro`). Configurable via `HATCHERY_GEMINI_MODEL` (default: `auto`).
- `-p "<prompt>"`: Inline prompt. For long prompts, use a temp file approach if your shell has command-line length limits.

**Configuration env vars:**
```bash
HATCHERY_GEMINI_BINARY="gemini"          # default: 'gemini' from PATH
HATCHERY_GEMINI_MODEL="auto"             # default: 'auto'
```

### Availability Check

Always check binary availability before spawning. Absolute paths and PATH-relative names need different checks:

```python
def is_available(self) -> bool:
    if os.path.isabs(self.binary_path):
        return os.path.isfile(self.binary_path) and os.access(self.binary_path, os.X_OK)
    else:
        result = subprocess.run(["which", self.binary_path], capture_output=True, timeout=5)
        return result.returncode == 0
```

---

## 3. Activity Detection: Byte-Level vs. JSON-Event Parsing

### What --output-format stream-json Provides

Gemini outputs a JSON stream where each line is a structured event:

```json
{"type": "content", "data": {"text": "Analyzing bead requirements..."}}
{"type": "tool_call", "data": {"name": "read_file", "args": {...}}}
{"type": "tool_result", "data": {"name": "read_file", "result": "..."}}
{"type": "complete", "data": {"exit_code": 0}}
```

### Why Byte-Level Detection Is Sufficient

For activity monitoring (is the agent still doing work?), **byte-level detection is simpler and more robust than JSON-event parsing:**

- Any new bytes in the output stream indicate live execution
- JSON parsing adds complexity: incomplete JSON lines, encoding issues, format changes across gemini versions
- For the hatchery use case (activity timeout detection), the signal is binary: "new output exists" or "no new output for N seconds"

**Implemented pattern** (from `GeminiProvider.stream_events`):

```python
def stream_events(self, pid: int) -> Iterator[AgentEvent]:
    tmp_path = GeminiProvider._pid_to_tempfile.get(pid)
    if not tmp_path or not tmp_path.exists():
        return

    read_pos = GeminiProvider._pid_to_read_pos.get(pid, 0)
    with open(tmp_path, "rb") as f:
        f.seek(read_pos)
        new_data = f.read(8192)   # Read in 8KB chunks
        if new_data:
            GeminiProvider._pid_to_read_pos[pid] = read_pos + len(new_data)
            yield AgentEvent(
                event_type="output",
                timestamp=datetime.now().isoformat(),
                data={"bytes_read": len(new_data)},
            )
```

**When to use JSON-event parsing instead:**
- If you need to extract structured results (specific tool outputs, exit codes)
- If you need per-event timestamps for activity granularity beyond "bytes arrived"
- If you want to trigger specific behavior on `"type": "complete"` events

---

## 4. Temp File Capture Pattern

The canonical pattern for non-blocking subprocess output capture:

```python
# 1. Create temp file before spawning
tmp = tempfile.NamedTemporaryFile(
    prefix=f"hatchery-{bead_id}-",
    suffix=".log",
    delete=False,
)
tmp_path = Path(tmp.name)
tmp.close()

# 2. Spawn subprocess writing to temp file
with open(tmp_path, "wb") as outfile:
    proc = subprocess.Popen(
        cmd,
        stdout=outfile,
        stderr=subprocess.STDOUT,   # merge stderr into same stream
        cwd=str(project_dir),       # run in the project directory
    )

# 3. Track PID → temp file mapping for incremental reads
self._pid_to_tempfile[proc.pid] = tmp_path
self._pid_to_read_pos[proc.pid] = 0

# 4. Incremental reads (in stream_events) without blocking
# 5. Cleanup on wait() completion:
#    - Keep temp file on failure (post-mortem analysis)
#    - Delete temp file on success (unless keep_files=True for debugging)
```

**Why this pattern instead of `subprocess.PIPE`:**
- `subprocess.PIPE` requires reading stdout in a separate thread to avoid deadlock
- Temp files allow random-access seek + incremental reads without blocking
- Temp files survive process crashes; a pipe would be lost

**Cleanup policy:**
- `result.success and not keep_files` → delete temp file
- `result.success and keep_files` → keep (for debugging)
- `not result.success` → keep for post-mortem analysis

---

## 5. Timeout Handling

Two timeout levels for subprocess providers:

| Timeout | Default | Purpose |
|---------|---------|---------|
| Spawn timeout | n/a | Binary availability check: 5s (`subprocess.run(["which", ...])`) |
| Execution timeout | 1800s (30 min) | Full bead execution via `execute_bead()` synchronous mode |
| Activity timeout | via daemon config | Daemon kills agents with no new output for N seconds |

**Implementation note:** The 30-minute execution timeout applies only to synchronous `execute_bead()`. In async `spawn()`/`wait()` mode, the activity timeout from `HATCHERY_ACTIVITY_TIMEOUT` governs when to kill the process.

---

## 6. Testing Subprocess Providers

### Use MockProvider for Unit Tests

Never invoke the real binary in unit tests. Use `MockProvider` with configurable outcomes:

```python
from hatchery.providers import MockProvider

# Always succeed
provider = MockProvider(success_rate=1.0)

# Always fail
provider = MockProvider(success_rate=0.0)

# Per-bead outcome control
provider = MockProvider()
provider.configure_bead("hentown-123", outcome="success", summary="Done")
provider.configure_bead("hentown-456", outcome="failure", error="Timed out")
```

### Testing the Provider Itself

When testing a real provider (e.g., `GeminiProvider`), mock at the `subprocess` level:

```python
from unittest.mock import MagicMock, patch
from hatchery.providers import GeminiProvider

def test_gemini_execute_success():
    provider = GeminiProvider(binary_path="gemini", model="auto")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"type":"complete","data":{"exit_code":0}}'
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = provider.execute_bead("test-bead")

    assert result.success is True
    assert result.exit_code == 0
    # Verify correct flags passed to binary
    call_args = mock_run.call_args[0][0]
    assert "--yolo" in call_args
    assert "--output-format" in call_args
    assert "stream-json" in call_args


def test_gemini_binary_not_found():
    provider = GeminiProvider(binary_path="/nonexistent/gemini")
    result = provider.execute_bead("test-bead")

    assert result.success is False
    assert result.exit_code == 127   # Convention: 127 = binary not found
```

### Testing spawn/stream_events

```python
def test_gemini_stream_events(tmp_path):
    """Test byte-level activity detection."""
    provider = GeminiProvider()
    fake_pid = 99999

    # Set up temp file with content
    tmp_file = tmp_path / "hatchery-test.log"
    tmp_file.write_bytes(b'{"type":"content","data":{"text":"Working..."}}\n')

    GeminiProvider._pid_to_tempfile[fake_pid] = tmp_file
    GeminiProvider._pid_to_read_pos[fake_pid] = 0

    events = list(provider.stream_events(fake_pid))

    assert len(events) == 1
    assert events[0].event_type == "output"
    assert events[0].data["bytes_read"] > 0
```

---

## 7. The Provider Registry Pattern

Use a factory function for provider selection by name:

```python
def get_provider(name: str, **config) -> Optional[BaseProvider]:
    """Instantiate a provider by name from config."""
    providers = {
        "claude": lambda: ClaudeProvider(binary_path=config.get("binary_path", "claude")),
        "gemini": lambda: GeminiProvider(
            binary_path=config.get("binary_path", "gemini"),
            model=config.get("model", "auto"),
        ),
        "mock": lambda: MockProvider(
            success_rate=config.get("success_rate", 0.8),
        ),
    }
    factory = providers.get(name)
    if factory is None:
        return None
    provider = factory()
    return provider if provider.is_available() else None
```

---

## 8. Known Issues & Caveats

### Gemini stream-json format versioning

`--output-format stream-json` is a gemini-cli flag. The JSON event schema may change across
gemini-cli versions. Since hatchery uses byte-level activity detection (not JSON parsing), this
is not a breaking change for activity monitoring — but if you add JSON-event parsing for specific
event types, pin your gemini-cli version and update tests when upgrading.

### Long prompts and command-line limits

The `-p "<prompt>"` pattern has OS-level argument length limits (typically 128KB–2MB on macOS/Linux).
For very long system prompts (e.g., prompts that embed entire bead descriptions + context documents),
prefer writing the prompt to a temp file and passing `--prompt-file <path>` if gemini supports it,
or use stdin:

```python
proc = subprocess.Popen(
    ["gemini", "--yolo", "--output-format", "stream-json", "--model", model],
    stdin=subprocess.PIPE,
    stdout=outfile,
    stderr=subprocess.STDOUT,
)
proc.stdin.write(prompt.encode())
proc.stdin.close()
```

### Working directory matters

Set `cwd=str(project_dir)` when spawning. The agent will read AGENTS.md, CLAUDE.md, GEMINI.md
and other project context files relative to its working directory. Running from the wrong directory
causes the agent to miss project instructions.

---

## Related Documentation

- **[Gemini CLI Tool Guide](../../../tools/gemini.md)** — Interactive use of gemini-cli
- **[AI Provider Integration Patterns](../../../guidelines/ai-provider-integration-patterns.md)** — Library integration failure modes
- **[Agent Jurisdiction & Cross-Project Coordination](../../../principles/agent-jurisdiction.md)** — What agents may write

---

**Last Updated:** 2026-03-04
**Basis:** hatchery-improvements epic, Phase 4 (Gemini Provider) implementation
**Status:** Active ✓ — Guides future provider implementations
