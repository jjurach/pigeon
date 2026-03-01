# Dolt Server Coordination Guide

**For:** Agents, orchestrators, and automation systems
**Purpose:** Coordinate safe startup, operation, and shutdown of the shared Dolt server
**Status:** Mandatory for multi-agent deployments

---

## Multi-Project Architecture (hentown)

The `hentown` repository is the **top-level project** that owns the single shared Dolt server
for all its submodules. There is **one Dolt server per machine**, not one per project.

```
hentown/                        ← TOP-LEVEL: owns and starts the Dolt server
  .beads/dolt/                  ← Server data directory (all databases live here)
    beads_hentown/              ← hentown issues database
    beads_hatchery/             ← hatchery issues database
    beads_pigeon/               ← pigeon issues database
    beads_chatterbox/           ← chatterbox issues database
    beads_mellona/              ← mellona issues database
    beads_pitchjudge/           ← pitchjudge issues database
    beads_second_voice/         ← second_voice issues database

modules/hatchery/               ← SUBMODULE: connects to hentown's server
  .beads/config.yaml            ← dolt.auto-start: false, port: 3307
modules/pigeon/                 ← SUBMODULE: same pattern
  ...
```

**Server:** `127.0.0.1:3307` (fixed port, configured in all `.beads/config.yaml` files)

### Top-Level Project Responsibilities

- **hentown** starts and stops the Dolt server: `bd dolt start` / `bd dolt stop`
- Run from `~/hentown` (or wherever hentown is checked out)
- The server auto-starts when `bd` commands are run from hentown, if not already running

### Submodule Responsibilities

- **DO NOT** start a Dolt server from a submodule directory
- **DO** connect to the superproject's server at `127.0.0.1:3307`
- **ABORT** if the server is not running — do not attempt to start it

### Finding the Superproject Root

From inside any submodule, use git to locate the superproject working tree:

```bash
SUPERPROJECT=$(git rev-parse --show-superproject-working-tree)
# Returns the absolute path to the superproject root, e.g. /Users/you/hentown
# Returns an empty string if not inside a submodule
```

Use this to start the server without hardcoding paths:

```bash
SUPERPROJECT=$(git rev-parse --show-superproject-working-tree)
if [ -z "$SUPERPROJECT" ]; then
  echo "ERROR: Not inside a submodule — run bd dolt start from the project root."
  exit 1
fi
cd "$SUPERPROJECT" && bd dolt start
```

### Submodule Pre-Flight Check (MANDATORY)

Before any `bd` command in a submodule, verify the shared server is reachable:

```bash
# Check shared server is running (run from the submodule directory)
if ! nc -z 127.0.0.1 3307 2>/dev/null; then
  echo "ERROR: Dolt server not running at 127.0.0.1:3307"
  echo "Start it from the hentown root: cd ~/hentown && bd dolt start"
  exit 1
fi
```

Or use `bd dolt test` which will fail with a clear error if unreachable.

---

## Architecture Overview (Single Project)

This project uses a **shared Dolt server** model where all agents and tools communicate with a single server instance. This differs from ad-hoc instance creation and ensures:

- ✓ One database source of truth
- ✓ Efficient resource usage
- ✓ Graceful state preservation
- ✓ Safe concurrent access

**File Location:** `.beads/dolt/` (the Dolt database directory)
**Configuration:** `.beads/config.yaml`
**State Files:** `.beads/dolt-server.{pid,port,activity}` (gitignored)

---

## Process Files & Their Meaning

| File | Purpose | Persistence | Updated |
|------|---------|-------------|---------|
| `.beads/dolt-server.pid` | Server process ID | Across sessions | On startup |
| `.beads/dolt-server.port` | TCP port (usually 3306) | Across sessions | On startup |
| `.beads/dolt-monitor.pid` | Watchdog process | Across sessions | On startup |
| `.beads/dolt-server.activity` | Last mutation timestamp | Across sessions | On write |
| `.beads/bd.sock` | Unix socket for CLI | Across sessions | On startup |
| `.beads/bd.sock.startlock` | Startup synchronization lock | Temporary | During init |

**Key:** All these files are **gitignored**. Never commit them. They are safe to delete and will be recreated on startup.

---

## Agent Startup Procedure

### Phase 1: Check for Existing Server

Before starting any agent, check if a server is already running:

```bash
#!/bin/bash
# agent-startup-check.sh

BEADS_DIR=".beads"
PID_FILE="$BEADS_DIR/dolt-server.pid"

# Check if PID file exists and process is alive
if [ -f "$PID_FILE" ]; then
  server_pid=$(cat "$PID_FILE" 2>/dev/null)

  if [ -n "$server_pid" ] && kill -0 "$server_pid" 2>/dev/null; then
    # Process is alive
    echo "✓ Dolt server already running (PID: $server_pid)"

    # Verify it's responding (optional, more thorough check)
    if [ -f "$BEADS_DIR/dolt-server.port" ]; then
      port=$(cat "$BEADS_DIR/dolt-server.port" 2>/dev/null)
      if nc -z localhost "$port" 2>/dev/null; then
        echo "✓ Server is responsive on port $port"
        exit 0
      fi
    fi
  else
    # Stale PID file (process is dead)
    echo "⚠ Stale PID file detected. Cleaning up..."
    rm -f "$PID_FILE" "$BEADS_DIR/dolt-server.port" "$BEADS_DIR/dolt-monitor.pid"
  fi
fi

# Server not running, proceed with startup
echo "Starting Dolt server..."
bd init  # or appropriate startup command
```

### Phase 2: Initialize if Needed

```bash
# Only run if server doesn't exist
if ! [ -f ".beads/dolt-server.pid" ] || ! kill -0 $(cat .beads/dolt-server.pid) 2>/dev/null; then
  cd /path/to/project
  bd init
  sleep 1  # Give server time to write PID/port files
fi
```

### Phase 3: Verify Connectivity

```bash
# Test that bd CLI can reach the server
if bd list --json > /dev/null 2>&1; then
  echo "✓ Dolt server is accessible via bd CLI"
else
  echo "❌ Failed to connect to Dolt server"
  exit 1
fi
```

---

## Multi-Agent Coordination Patterns

### Pattern 1: Check-Then-Use (Sequential Agents)

For agents that run sequentially:

```bash
# In agent1:
if ! [ -f .beads/dolt-server.pid ]; then
  bd init
fi
bd create "agent1 work"
bd close agent1-123

# In agent2 (later):
# .beads/dolt-server.pid already exists from agent1
bd list --json  # Reuses existing server
```

### Pattern 2: Parallel Startup (Race Condition Prevention)

For parallel agents, use the startup lock:

```bash
# Both agents detect no server, acquire lock to prevent race
lock_file=".beads/bd.sock.startlock"

(
  flock 9 || exit 1

  # Recheck after acquiring lock (another agent might have started server)
  if ! [ -f .beads/dolt-server.pid ] || ! kill -0 $(cat .beads/dolt-server.pid) 2>/dev/null; then
    bd init
  fi
) 9> "$lock_file"

# Now safe to use server
bd list --json
```

### Pattern 3: Graceful Degradation (Fallback to JSONL)

If Dolt server is unavailable, fall back to read-only JSONL:

```python
from pathlib import Path
import json

def load_beads(prefer_dolt=True):
    """Load beads from Dolt server or fallback to JSONL."""

    # Try Dolt first
    if prefer_dolt:
        try:
            import subprocess
            result = subprocess.run(
                ["bd", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass

    # Fallback to JSONL
    print("⚠ Dolt unavailable, using JSONL fallback (read-only)")
    beads = []
    jsonl_file = Path(".beads/issues.jsonl")

    if jsonl_file.exists():
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    beads.append(json.loads(line))

    return beads
```

---

## Shutdown & Cleanup

### Graceful Shutdown (Preferred)

```bash
# Signal server to shut down cleanly
kill -TERM $(cat .beads/dolt-server.pid 2>/dev/null) 2>/dev/null

# Wait for shutdown (timeout after 10 seconds)
timeout=10
while [ -f .beads/dolt-server.pid ] && [ $timeout -gt 0 ]; do
  sleep 0.5
  timeout=$((timeout - 1))
done

# Verify shutdown
if ! kill -0 $(cat .beads/dolt-server.pid 2>/dev/null) 2>/dev/null; then
  echo "✓ Dolt server shut down gracefully"
else
  echo "⚠ Server did not shut down, force killing..."
  kill -9 $(cat .beads/dolt-server.pid)
fi
```

### Safe Cleanup (When Restarting)

```bash
# Safe to delete (will be recreated)
rm -f .beads/dolt-server.pid
rm -f .beads/dolt-server.port
rm -f .beads/dolt-monitor.pid
rm -f .beads/dolt-server.activity
rm -f .beads/bd.sock
rm -f .beads/bd.sock.startlock

# Do NOT delete:
# - .beads/dolt/          (the actual database)
# - .beads/issues.jsonl   (git-tracked exports)
# - .beads/config.yaml    (configuration)
```

### Emergency Kill

Only use if graceful shutdown fails:

```bash
# Force kill all Dolt processes
pkill -9 dolt
pkill -9 dolt-server

# Clean state files
rm -f .beads/dolt-server.pid .beads/dolt-server.port .beads/bd.sock

# Then restart with Phase 1 check
```

---

## Troubleshooting

### Symptom: "Address already in use"

**Cause:** Process in PID file is dead, but port is still bound.

**Fix:**
```bash
# Find process holding the port
port=$(cat .beads/dolt-server.port 2>/dev/null || echo 3306)
lsof -i :$port

# Kill the process
kill -9 <PID>

# Clean up state files
rm -f .beads/dolt-server.{pid,port,activity}

# Restart
bd init
```

### Symptom: "Can't connect to Dolt server"

**Cause:** PID file exists but process is dead, or socket is stale.

**Fix:**
```bash
# Check if process is alive
pid=$(cat .beads/dolt-server.pid 2>/dev/null)
kill -0 $pid 2>/dev/null || {
  echo "Process dead, cleaning up..."
  rm -f .beads/dolt-server.{pid,port,activity,sock}
}

# Restart
bd init
bd list  # Verify connectivity
```

### Symptom: "Dolt database is locked"

**Cause:** Concurrent writes from multiple processes (rare with shared server).

**Fix:**
```bash
# Wait for lock to release (usually resolves in seconds)
timeout 30 bash -c 'while [ -f .beads/dolt/.lock ]; do sleep 0.1; done'

# If it persists, check for hung processes
ps aux | grep dolt

# Last resort: restart server
pkill -9 dolt
rm -f .beads/dolt-server.{pid,port,activity}
bd init
```

---

## Best Practices for Agents

1. **Always Check First:** Before starting server, verify no existing instance (see Phase 1).

2. **Use Lock Files:** When starting in parallel, use `.beads/bd.sock.startlock` to prevent race conditions.

3. **Honor .gitignore:** Never commit `.pid`, `.port`, or `.activity` files.

4. **Graceful Shutdown:** Use `SIGTERM`, not `SIGKILL`, to allow clean database flushing.

5. **Document Dependencies:** If your agent spawns Dolt, document the setup in your README.

6. **Fallback to JSONL:** For read-only operations, design fallback to `.beads/issues.jsonl` when server is unavailable.

7. **Log Server State:** In agent logs, record the PID and port of the Dolt server you're using.

8. **Clean on Exit:** Remove temporary state files when your agent exits cleanly (optional for persistent sessions).

---

## Environment Variables

Consider supporting these for container and multi-user environments:

```bash
# Location of .beads directory (default: ./.beads)
export BEADS_DIR="${BEADS_DIR:-./.beads}"

# Dolt server port (default: 3306, randomly assigned if taken)
export DOLT_PORT="${DOLT_PORT:-(auto)}"

# Database name (default: from config.yaml)
export DOLT_DB_NAME="${DOLT_DB_NAME:-$(basename "$PWD")}"

# Server data directory (for container/ephemeral environments)
export DOLT_DATA_DIR="${XDG_RUNTIME_DIR}/dolt-${PROJECT_NAME:-$(basename "$PWD")}"
```

---

## See Also

- [Beads Usage Guide](./beads-usage.md) — Command reference and data access patterns
- [Git Hygiene Audit](../2026-02-28_git-hygiene-audit.md) — Analysis of process file management

---

**Last Updated:** 2026-02-28
**Maintained by:** DevOps & Agentic Systems Team

