# Beads Usage Guide

This document describes the authoritative interface for reading and writing bead
databases. It supersedes any older documentation that references SQLite directly.

---

## Data Source Hierarchy

| Source | Role | When to use |
|--------|------|-------------|
| **Dolt** (`.beads/dolt/`) | Source of truth | Implicit — all `bd` commands use it |
| **`bd` CLI** | Primary interface | All reads and writes |
| **`.beads/issues.jsonl`** | Git-tracked export | Fallback reads when `bd` is unavailable (e.g. submodule contexts); never write directly |
| **`.beads/*.db` files** | Legacy SQLite artifacts | **Never use** — gitignored, not populated by Dolt |

**Rule:** Always use the `bd` CLI. Never read or write `.db` files or the Dolt binary
directory directly. The JSONL file is a read-only fallback, not a write target.

---

## bd CLI — Command Reference

### Installation

```bash
# Via npm (older, stable)
npm install -g @beads/bd

# Or build from source (Go)
cd /path/to/beads && go build -o bd ./cmd/bd
```

### JSON Output

All commands support `--json` for machine-readable output.

```bash
bd list --json          # Array of IssueWithCounts objects
bd ready --json         # Same, filtered to open/unblocked
bd show <id> --json     # Array (always a list, take [0] for single item)
bd create "..." --json  # Returns created issue object
bd close <id> --json    # Returns closed issue object
```

> **Note for code calling `bd show --json`:** The output is always a JSON array
> even for a single ID. Always handle the list and take the first element.

### Reading Beads

```bash
# All open (unblocked + blocked by deps)
bd list --json

# Only ready (open AND no unsatisfied deps — use for dispatch)
bd ready --json

# Specific bead by ID
bd show hatchery-p91 --json

# Filter by status
bd list --status open --json
bd list --status in_progress --json
bd list --status closed --json
bd list --all --json    # includes closed
```

### Status Values

| Value | Meaning |
|-------|---------|
| `open` | Pending work (may or may not be dep-blocked) |
| `in_progress` | Claimed, actively being worked |
| `blocked` | Explicitly blocked (e.g. external dependency) |
| `deferred` | Hidden until a future date |
| `closed` | Done |

> Use `bd ready` (not `bd list --status open`) to get truly executable work — it
> applies dependency semantics to filter out dep-blocked open beads.

### JSON Field Names (from `bd list --json` / `bd ready --json`)

```json
{
  "id": "hatchery-p91",
  "title": "Create PersistentDispatchQueue",
  "description": "Full description text...",
  "status": "open",
  "priority": 0,
  "issue_type": "task",
  "owner": "user@example.com",
  "created_at": "2026-02-27T16:02:08Z",
  "created_by": "User Name",
  "updated_at": "2026-02-27T16:02:08Z",
  "dependencies": [...],
  "dependency_count": 0,
  "dependent_count": 2,
  "comment_count": 0
}
```

> `bd show --json` returns the full `IssueDetails` which adds `labels`, `comments`,
> `dependents`, `design`, `acceptance_criteria`, `notes`, and `parent`.

### Writing Beads

```bash
# Create a new bead
bd create "Title" \
  --description "Full description of work" \
  --priority 1 \
  --type task

# Create with explicit ID (use in coordinated plans)
bd create "Title" --id prefix-xyz --priority 0 --deps "prefix-a,prefix-b"

# Create silently (returns only the ID)
ID=$(bd create --silent "Title" --priority 2)

# Claim bead (mark in_progress)
bd update <id> --claim

# Append notes (non-destructive)
bd update <id> --append-notes "retry attempt 2"

# Reset to open
bd update <id> --status open

# Close bead
bd close <id>
bd close <id> --reason "Completed successfully"

# Close multiple at once
bd close <id1> <id2> <id3>
```

### Dependencies

```bash
# Add: issue <child> depends on <parent> (parent blocks child)
bd dep add <child-id> <parent-id>

# Remove dependency
bd dep remove <child-id> <parent-id>

# Show dependency tree
bd dep tree <id>
```

---

## MANDATORY Sync Workflow

Dolt commits writes immediately, but `issues.jsonl` (the git-tracked export) is only
updated on `bd sync`. **Always sync after mutations:**

```bash
# After any create/close/update that matters for git history:
bd sync
git add .beads/issues.jsonl
git commit -m "chore: sync beads after <description>"
```

If you skip `bd sync`, Dolt has the change but git history is stale. Other agents
cloning the repo won't see the new bead.

---

## Reading from JSONL (Fallback Only)

When `bd` CLI is unavailable (e.g., reading a submodule's beads from a different
working directory), fall back to `.beads/issues.jsonl`:

```python
import json

def load_beads_fallback(beads_dir: str) -> list:
    """Read beads from JSONL when bd CLI is unavailable."""
    jsonl = f"{beads_dir}/issues.jsonl"
    beads = []
    with open(jsonl) as f:
        for line in f:
            line = line.strip()
            if line:
                beads.append(json.loads(line))
    return beads
```

The JSONL uses the same field names as `bd list --json`. Status values in JSONL
match Dolt: `open`, `in_progress`, `blocked`, `deferred`, `closed`.

**Never write to `issues.jsonl` directly.** It is a read-only export artifact.

---

## Python Integration in Hatchery

Hatchery wraps `bd` via `DoltBeadDatabase` in `hatchery/beads_dolt.py`:

```python
from hatchery.beads import open_bead_db

# Auto-detects Dolt dir vs SQLite file:
db = open_bead_db(path)         # returns DoltBeadDatabase or BeadDatabase

# Interface methods (both backends):
beads = db.list_ready_beads()   # → List[Bead]
bead  = db.get_bead(bead_id)    # → Optional[Bead]
db.mark_grabbed(id, by)         # → bool (bd update --claim)
db.mark_closed(id)              # → bool (bd close)
db.mark_blocked(id, reason)     # → bool (bd update --status=blocked)
db.reset_to_pending(id)         # → bool (bd update --status=open)
db.update_agent_pid(id, pid)    # → bool (bd update --notes=agent_pid=N)
```

The `Bead` dataclass uses hatchery's internal status names (`pending`, `done`,
`in_progress`, `blocked`) which map from Dolt's `open`/`closed`.

---

## What NOT to Do

```python
# ❌ WRONG: reads SQLite (legacy, gitignored, not the Dolt db)
import sqlite3
conn = sqlite3.connect(".beads/beads.db")

# ❌ WRONG: writes SQLite directly (changes won't appear in Dolt or JSONL)
conn.execute("UPDATE beads SET status='closed' WHERE id=?", (bead_id,))

# ❌ WRONG: reading .db files as if they're the source of truth
db_path = ".beads/beads.db"  # This file doesn't exist in Dolt-backed projects

# ✅ CORRECT: use bd CLI or hatchery's DoltBeadDatabase wrapper
db = open_bead_db(Path(".beads"))
db.mark_closed(bead_id)
```

---

## `.beads/` Directory Layout

```
.beads/
├── config.yaml          # bd configuration (git-tracked)
├── dolt/                # Dolt binary database (gitignored)
│   └── <db-name>/       # Actual database files
├── export-state/        # Sync state (gitignored)
├── hooks/               # Git hook scripts
├── interactions.jsonl   # Agent interaction log (git-tracked)
├── issues.jsonl         # Dolt export — THE git-tracked bead store
├── metadata.json        # Backend declaration (git-tracked)
└── README.md            # Label conventions (git-tracked)
```

The `.beads/.gitignore` explicitly excludes `dolt/`, `*.db`, `*.db-wal`, and all
legacy SQLite artifacts.
