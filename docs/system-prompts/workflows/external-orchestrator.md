# External Orchestrator Architecture

**Purpose:** Define the architecture and operation of external orchestrators that dispatch ready beads to worker agents.

**Audience:** Orchestrator implementers, planner agents (to understand what orchestrator expects), worker agents (to understand dispatch mechanism)

**Status:** Reference Architecture

---

## Overview

The **external orchestrator** is a **separate process** (not part of this codebase) that:

1. **Watches** the beads database for state changes
2. **Discovers** ready beads via `bd ready`
3. **Manages** a pool of worker agents (enforces max concurrency)
4. **Dispatches** ready beads to available workers
5. **Tracks** worker sessions for monitoring

The orchestrator is the **automation layer** that enables parallel execution of independent tasks without human intervention.

---

## Why External?

The orchestrator is external to this project because:

- **Separation of concerns** - Planning (planner agent) vs execution (orchestrator) vs implementation (worker agents)
- **Flexibility** - Different projects may use different orchestration strategies
- **Scalability** - Orchestrator can manage N worker agents across multiple machines
- **Independence** - This codebase focuses on task definition, not execution management

**This document defines what orchestrators should do, not how to implement them.**

---

## Orchestrator Responsibilities

### 1. Work Discovery

**Mechanism:** Watch beads JSONL export file for changes

**Rationale:** Beads exports task state to JSONL files for git portability. File modification indicates state changes (beads closed, new beads created, dependencies updated).

**Implementation approaches:**

**Option A: File watching (recommended)**
```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BeadsWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.beads/export.jsonl'):
            # Beads state changed, check for ready work
            self.discover_ready_work()

observer = Observer()
observer.schedule(BeadsWatcher(), path='.beads/', recursive=False)
observer.start()
```

**Option B: Polling**
```python
import subprocess
import time

def poll_for_ready_work():
    while True:
        result = subprocess.run(['bd', 'ready', '--json'], capture_output=True, text=True)
        ready_beads = json.loads(result.stdout)

        if ready_beads:
            dispatch_work(ready_beads)

        time.sleep(10)  # Poll every 10 seconds
```

**Option C: Git hook trigger**
```bash
# .git/hooks/post-commit
#!/bin/bash
# Trigger orchestrator on every commit (beads commits state changes)
/path/to/orchestrator check-for-work
```

### 2. Ready Bead Discovery

**Command:**
```bash
bd ready --json
```

**Output format:**
```json
[
  {
    "id": "bd-a1b2.1",
    "title": "Copy Lambda functions to new structure",
    "labels": ["implementation"],
    "status": "ready",
    "created_at": "2026-02-15T10:30:00Z"
  },
  {
    "id": "bd-a1b2.2",
    "title": "Update IAM policies for new roles",
    "labels": ["implementation"],
    "status": "ready",
    "created_at": "2026-02-15T10:30:05Z"
  }
]
```

**Selection strategy:**

**Simple FIFO:**
```python
ready_beads = get_ready_beads()
if ready_beads:
    next_bead = ready_beads[0]  # Oldest first
    dispatch_worker(next_bead['id'])
```

**Priority-based:**
```python
# Priority order: verification > implementation > documentation
priority_order = ['verification', 'implementation', 'documentation', 'research']

for label in priority_order:
    matching = [b for b in ready_beads if label in b['labels']]
    if matching:
        dispatch_worker(matching[0]['id'])
        break
```

**Load balancing:**
```python
# Distribute work evenly across workers
# (Useful if some beads are larger than others)
# Implementation varies by orchestrator design
```

### 3. Worker Pool Management

**Responsibility:** Enforce maximum concurrency limit

**State tracking:**
```python
class WorkerPool:
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.active_workers = {}  # {session_id: worker_info}

    def can_spawn_worker(self):
        return len(self.active_workers) < self.max_workers

    def spawn_worker(self, bead_id):
        if not self.can_spawn_worker():
            return None

        session_id = str(uuid.uuid4())
        worker_process = subprocess.Popen([
            'claude', 'implement', bead_id
        ])

        self.active_workers[session_id] = {
            'bead_id': bead_id,
            'process': worker_process,
            'started_at': datetime.now(),
        }

        # Create worker session bead for audit trail
        subprocess.run([
            'bd', 'create',
            f'Worker session {session_id}',
            '--label', 'worker-session',
            '--body', f'Implementing: {bead_id}\nStarted: {datetime.now()}'
        ])

        return session_id

    def cleanup_finished_workers(self):
        for session_id, info in list(self.active_workers.items()):
            if info['process'].poll() is not None:
                # Worker finished
                del self.active_workers[session_id]

                # Close worker session bead
                # (Find bead ID for this session first)
                # bd update <session-bead-id> --close
```

**Configuration:** Max workers should be configurable

```python
# orchestrator.config.json
{
    "max_workers": 3,
    "poll_interval_seconds": 10,
    "worker_timeout_minutes": 60
}
```

### 4. Worker Dispatch

**Mechanism:** Spawn worker agent with bead ID in prompt

**Implementation:**
```python
def dispatch_worker(bead_id):
    """
    Spawn a worker agent to implement the given bead.

    The worker receives a prompt with the bead ID and knows to:
    1. Claim the bead (bd update --claim)
    2. Read task details (bd show <id>)
    3. Implement the task
    4. Follow close-project.md (includes closing bead)
    """
    prompt = f"""Implement bead {bead_id}

Use `bd show {bead_id}` to see task details.
Follow close-project.md process when complete.
Include bead ID in change documentation: `Bead: {bead_id}`
"""

    # Spawn Claude agent with prompt
    # (Implementation varies by orchestration platform)

    # Option A: CLI invocation
    subprocess.Popen([
        'claude',
        '--prompt', prompt
    ])

    # Option B: API invocation
    anthropic.messages.create(
        model="claude-sonnet-4-5",
        messages=[{"role": "user", "content": prompt}]
    )

    # Option C: Custom agent framework
    agent_framework.spawn_worker(
        task_type="implement_bead",
        bead_id=bead_id,
        prompt=prompt
    )
```

**Critical:** Orchestrator must **not block** waiting for worker completion. Workers run asynchronously.

### 5. Worker Monitoring

**Responsibility:** Track worker health and handle failures

**Health checks:**

```python
def monitor_workers(self):
    """Check for stale or failed workers"""
    timeout = timedelta(minutes=self.config['worker_timeout_minutes'])

    for session_id, info in self.active_workers.items():
        runtime = datetime.now() - info['started_at']

        if runtime > timeout:
            # Worker timeout
            self.handle_timeout(session_id, info)

def handle_timeout(self, session_id, info):
    """Handle worker that exceeded timeout"""

    # Option 1: Kill worker and mark bead as failed
    info['process'].kill()
    bead_id = info['bead_id']

    # Create failure bead
    subprocess.run([
        'bd', 'create',
        f'TIMEOUT: Worker exceeded {timeout}m on {bead_id}',
        '--label', 'failure',
        '--body', f'''Worker session {session_id} timed out after {timeout} minutes.

Original bead: {bead_id}

The worker may be:
- Stuck on a complex task
- Waiting for unavailable resources
- Experiencing system issues

Recommendation: Human should review bead and decide whether to retry or revise approach.
'''
    ])

    # Block original bead
    # bd dep add {bead_id} {failure_bead_id}

    # Clean up worker
    del self.active_workers[session_id]

    # Option 2: Alert human but don't kill
    # (Useful if worker may still succeed)
    logging.warning(f'Worker {session_id} timeout on {bead_id}')
```

**Failure detection:**

Orchestrator detects failures by watching for failure beads:

```python
def check_for_failures(self):
    """Check if any workers created failure beads"""
    result = subprocess.run(
        ['bd', 'ready', '--label', 'failure', '--json'],
        capture_output=True,
        text=True
    )

    failure_beads = json.loads(result.stdout)

    for failure in failure_beads:
        # Alert human
        self.alert_human(f"Worker failure: {failure['title']}")

        # Optionally: pause orchestration until human reviews
        if self.config.get('pause_on_failure', False):
            self.paused = True
            break
```

---

## Orchestrator Operation

### Starting the Orchestrator

**Main loop:**
```python
def main_loop(self):
    """Main orchestration loop"""

    logging.info("Orchestrator started")
    logging.info(f"Max workers: {self.config['max_workers']}")
    logging.info(f"Poll interval: {self.config['poll_interval_seconds']}s")

    while not self.should_stop:
        # Clean up finished workers
        self.cleanup_finished_workers()

        # Check for failures
        self.check_for_failures()
        if self.paused:
            logging.info("Orchestrator paused due to failure. Resume with: orchestrator resume")
            time.sleep(self.config['poll_interval_seconds'])
            continue

        # Check for ready work
        if self.can_spawn_worker():
            ready_beads = self.get_ready_beads()

            if ready_beads:
                next_bead = self.select_next_bead(ready_beads)
                self.spawn_worker(next_bead['id'])
                logging.info(f"Dispatched worker for {next_bead['id']}: {next_bead['title']}")
            else:
                logging.debug("No ready beads found")
        else:
            logging.debug(f"Worker pool full ({len(self.active_workers)}/{self.max_workers})")

        # Sleep until next poll
        time.sleep(self.config['poll_interval_seconds'])

    logging.info("Orchestrator stopped")
```

**Start command:**
```bash
# Example orchestrator CLI
orchestrator start --config orchestrator.config.json
```

### Stopping the Orchestrator

**Graceful shutdown:**
```python
def shutdown(self, wait_for_workers=True):
    """Gracefully shutdown orchestrator"""

    logging.info("Shutdown requested")
    self.should_stop = True

    if wait_for_workers:
        logging.info(f"Waiting for {len(self.active_workers)} workers to finish...")

        # Wait for all workers to complete
        while self.active_workers:
            self.cleanup_finished_workers()
            time.sleep(5)

        logging.info("All workers finished")
    else:
        # Kill all workers immediately
        for session_id, info in self.active_workers.items():
            logging.warning(f"Killing worker {session_id}")
            info['process'].kill()

    logging.info("Orchestrator stopped")
```

**Stop command:**
```bash
# Graceful stop (wait for workers)
orchestrator stop

# Force stop (kill workers)
orchestrator stop --force
```

### Pausing/Resuming

**Pause (stop dispatching new work, but let active workers finish):**
```bash
orchestrator pause
```

**Resume (continue dispatching work):**
```bash
orchestrator resume
```

---

## Status and Monitoring

### Viewing Orchestrator Status

**Command:**
```bash
orchestrator status
```

**Example output:**
```
Orchestrator Status
===================

State: RUNNING
Workers: 2/3 active
Uptime: 2h 15m

Active Workers:
  - Worker abc123: bd-a1b2.1 "Copy Lambda functions" (running 15m)
  - Worker def456: bd-a1b2.2 "Update IAM policies" (running 8m)

Recently Completed (last 5):
  ✓ bd-a1b2.3 "Migrate DynamoDB schemas" (completed 5m ago by worker ghi789)
  ✓ bd-a1b2.4 "Update API endpoints" (completed 12m ago by worker jkl012)
  ...

Ready Beads: 3
  - bd-a1b2.5 "Write integration tests"
  - bd-a1b2.6 "Update documentation"
  - bd-a1b2.7 "Deploy to staging"

Failures: 0
```

### Integration with planning-summary.py

Orchestrator status complements `planning-summary.py` (which shows bead state):

```bash
# Show bead state (from beads database)
python3 docs/system-prompts/planning-summary.py

# Show orchestrator state (from orchestrator runtime)
orchestrator status
```

**Typical workflow:**
1. Planner creates beads
2. Human closes approval bead
3. `planning-summary.py` shows beads are ready
4. Orchestrator detects ready beads
5. Orchestrator spawns workers
6. `orchestrator status` shows active workers
7. Workers complete and close beads
8. `planning-summary.py` shows beads are closed

---

## Error Handling

### Worker Crashes

**Scenario:** Worker process crashes before completing work

**Detection:**
```python
def cleanup_finished_workers(self):
    for session_id, info in list(self.active_workers.items()):
        exit_code = info['process'].poll()

        if exit_code is not None:
            # Worker finished
            if exit_code != 0:
                # Worker crashed
                self.handle_worker_crash(session_id, info, exit_code)
            else:
                # Worker completed normally
                del self.active_workers[session_id]

def handle_worker_crash(self, session_id, info, exit_code):
    """Handle worker crash"""
    bead_id = info['bead_id']

    logging.error(f"Worker {session_id} crashed with exit code {exit_code}")

    # Check if worker already created failure bead
    # (Good workers create failure beads before exiting)
    result = subprocess.run(
        ['bd', 'show', bead_id, '--json'],
        capture_output=True,
        text=True
    )
    bead = json.loads(result.stdout)

    if bead['status'] == 'in-progress':
        # Worker crashed without creating failure bead
        # Orchestrator creates one

        subprocess.run([
            'bd', 'create',
            f'CRASH: Worker crashed on {bead_id}',
            '--label', 'failure',
            '--body', f'''Worker session {session_id} crashed with exit code {exit_code}.

Original bead: {bead_id}

The worker did not create a failure bead, indicating an unexpected crash.

Check orchestrator logs for details.
'''
        ])

        # Unclaim original bead
        subprocess.run(['bd', 'update', bead_id, '--unclaim'])

    del self.active_workers[session_id]
```

### Network/System Failures

**Scenario:** Orchestrator loses access to beads database (network issues, disk full, etc.)

**Handling:**
```python
def get_ready_beads(self):
    """Get ready beads with error handling"""
    try:
        result = subprocess.run(
            ['bd', 'ready', '--json'],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        logging.error("bd ready command timed out")
        return []
    except subprocess.CalledProcessError as e:
        logging.error(f"bd ready failed: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse bd ready output: {e}")
        return []
```

**Recovery:** Orchestrator should be resilient to transient failures. If beads database becomes unavailable, orchestrator should:
1. Log error
2. Wait for next poll interval
3. Retry

Persistent failures may require human intervention.

---

## Configuration

### orchestrator.config.json

**Example configuration:**
```json
{
  "max_workers": 3,
  "poll_interval_seconds": 10,
  "worker_timeout_minutes": 60,
  "pause_on_failure": true,
  "worker_command": ["claude"],
  "log_level": "INFO",
  "log_file": "orchestrator.log",
  "beads_path": ".beads/",
  "priority_labels": ["verification", "implementation", "documentation", "research"]
}
```

**Configuration options:**

- `max_workers` - Maximum concurrent workers (default: 3)
- `poll_interval_seconds` - How often to check for ready work (default: 10)
- `worker_timeout_minutes` - Kill workers that exceed this time (default: 60)
- `pause_on_failure` - Pause orchestration when failure bead detected (default: true)
- `worker_command` - Command to spawn worker agent (default: ["claude"])
- `log_level` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `log_file` - Path to log file
- `beads_path` - Path to beads database (default: .beads/)
- `priority_labels` - Label priority order for work selection

---

## Planner Expectations

**What planners should know about orchestrators:**

1. **Orchestrators dispatch based on `bd ready` output**
   - Only beads with status "ready" will be dispatched
   - Beads become ready when all dependencies closed

2. **Orchestrators don't understand project plans**
   - Bead description should be self-contained
   - Include relevant context in bead body
   - Link to project plan if needed

3. **Orchestrators enforce concurrency limits**
   - Not all ready beads will be dispatched immediately
   - If 10 beads are ready but max_workers=3, only 3 will run at a time

4. **Orchestrators watch for failure beads**
   - If worker creates failure bead, orchestrator may pause
   - Human must resolve failure before work continues

5. **Orchestrators track worker sessions**
   - Worker session beads created for audit trail
   - Don't manually create/modify worker session beads (orchestrator owns these)

---

## Worker Expectations

**What workers should know about orchestrators:**

1. **Bead ID will be in prompt**
   - Worker receives: "Implement bead bd-a1b2.1"
   - Worker should extract bead ID and use it

2. **Worker must claim bead immediately**
   - `bd update <id> --claim`
   - Prevents other workers from claiming same bead

3. **Worker must close bead on completion**
   - Part of close-project.md process (Phase 4.5)
   - `bd update <id> --close`
   - Signals to orchestrator that work is done

4. **Worker should create failure bead on error**
   - Don't just exit with error code
   - Create failure bead with context
   - Block original bead with failure bead

5. **Worker session beads are for audit only**
   - Orchestrator creates worker session bead
   - Worker doesn't need to interact with it

---

## Example Orchestrator Implementations

### Minimal Python Orchestrator

```python
#!/usr/bin/env python3
"""
Minimal beads orchestrator.
Watches for ready beads and dispatches to worker pool.
"""

import json
import subprocess
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BeadsOrchestrator:
    def __init__(self, max_workers=3, poll_interval=10):
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.active_workers = {}
        self.should_stop = False
        self.paused = False

    def get_ready_beads(self) -> List[Dict]:
        """Get list of ready beads"""
        try:
            result = subprocess.run(['bd', 'ready', '--json'], capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            logging.error(f"Failed to get ready beads: {e}")
            return []

    def can_spawn_worker(self) -> bool:
        """Check if we can spawn another worker"""
        return len(self.active_workers) < self.max_workers

    def spawn_worker(self, bead_id: str):
        """Spawn worker to implement bead"""
        prompt = f"Implement bead {bead_id}\n\nUse bd show {bead_id} to see details.\nFollow close-project.md when done."

        try:
            process = subprocess.Popen(['claude', '--prompt', prompt])
            self.active_workers[bead_id] = {
                'process': process,
                'started_at': datetime.now()
            }
            logging.info(f"Spawned worker for {bead_id}")
        except Exception as e:
            logging.error(f"Failed to spawn worker for {bead_id}: {e}")

    def cleanup_finished_workers(self):
        """Remove finished workers from active list"""
        for bead_id in list(self.active_workers.keys()):
            if self.active_workers[bead_id]['process'].poll() is not None:
                logging.info(f"Worker finished: {bead_id}")
                del self.active_workers[bead_id]

    def run(self):
        """Main orchestration loop"""
        logging.info(f"Orchestrator started (max_workers={self.max_workers})")

        while not self.should_stop:
            self.cleanup_finished_workers()

            if not self.paused and self.can_spawn_worker():
                ready_beads = self.get_ready_beads()
                if ready_beads:
                    # Dispatch first ready bead
                    self.spawn_worker(ready_beads[0]['id'])

            time.sleep(self.poll_interval)

        logging.info("Orchestrator stopped")

if __name__ == '__main__':
    orchestrator = BeadsOrchestrator(max_workers=3, poll_interval=10)
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logging.info("Shutdown requested")
        orchestrator.should_stop = True
```

### Shell Script Orchestrator

```bash
#!/bin/bash
# Simple beads orchestrator in bash

MAX_WORKERS=3
POLL_INTERVAL=10

echo "Orchestrator started (max_workers=$MAX_WORKERS)"

while true; do
    # Count active workers (background jobs)
    active_count=$(jobs -r | wc -l)

    if [ $active_count -lt $MAX_WORKERS ]; then
        # Get ready beads
        ready_json=$(bd ready --json)
        ready_count=$(echo "$ready_json" | jq 'length')

        if [ "$ready_count" -gt 0 ]; then
            # Get first ready bead
            bead_id=$(echo "$ready_json" | jq -r '.[0].id')
            bead_title=$(echo "$ready_json" | jq -r '.[0].title')

            echo "Dispatching worker for $bead_id: $bead_title"

            # Spawn worker in background
            (
                claude --prompt "Implement bead $bead_id

Use bd show $bead_id to see details.
Follow close-project.md when done."
            ) &
        fi
    fi

    sleep $POLL_INTERVAL
done
```

---

## See Also

- **[Plan-and-Dispatch Workflow](plan-and-dispatch.md)** - Core workflow using beads
- **[Planning Summary](../processes/planning-summary.md)** - View bead state
- **[Planning Doctor](../processes/planning-doctor.md)** - Detect orchestration issues

---

**Last Updated:** 2026-02-15
