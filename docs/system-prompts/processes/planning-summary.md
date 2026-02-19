# Planning Summary Process

**Purpose:** Display execution status and summary information for beads task tracking across Hentown and all git submodules.

**Status:** Documented

**Prerequisites:**
- Beads initialized in project (`.beads/` exists)
- Python 3.8+

---

## Overview

The planning-summary process provides a comprehensive view of task execution status across all active projects:

1. **Recently closed beads** - What work was completed
2. **In-progress beads** - What's currently being worked on
3. **Ready beads** - What's available for work
4. **Blocked beads** - What's waiting on dependencies
5. **Failure beads** - What needs human intervention

This provides unified visibility across Hentown and all git submodules in a single command.
Submodules with a `.beads/` directory are automatically discovered and included.

### Multi-Project Support

By default, the script:
- Reads beads from the root Hentown `.beads/` directory
- Discovers git submodules from `.gitmodules`
- Includes beads from any submodule that has a `.beads/` directory
- Displays each project with a labeled header section
- Shows aggregate statistics across all projects at the end

Use `--no-submodules` to view only root project beads, or `--submodules name1,name2` to
include only specific submodules.

---

## When to Use This Process

**Use planning-summary when:**
- ✅ Checking overall project status
- ✅ Planning next work session
- ✅ Monitoring orchestrator progress
- ✅ Reporting to stakeholders
- ✅ Debugging workflow issues

**Use daily for:**
- Active projects with parallel work streams
- Projects using external orchestration
- Multi-agent workflows

---

## Usage

### Basic Summary

```bash
# Show all beads by status (includes submodules by default)
python3 docs/system-prompts/planning-summary.py

# Root project only (no submodules)
python3 docs/system-prompts/planning-summary.py --no-submodules

# Specific submodules only
python3 docs/system-prompts/planning-summary.py --submodules cackle,pigeon
```

**Example output:**
```
Beads Status Summary
====================

Recently Closed (last 5):
  ✓ bd-a1b2.3  Update IAM policies                    (closed 2h ago)
  ✓ bd-a1b2.2  Copy Lambda functions                  (closed 4h ago)
  ✓ bd-a1b2.1  Migrate DynamoDB schemas               (closed 6h ago)
  ✓ bd-c3d4    Research OAuth2 providers              (closed 1d ago)
  ✓ bd-e5f6    Approve: Backend Restructure Plan      (closed 1d ago)

Currently In Progress (2):
  → bd-g7h8    Implement API endpoint                 (claimed 30m ago)
  → bd-i9j0    Write integration tests                (claimed 15m ago)

Ready to Work (3):
  ○ bd-k1l2    Document API changes                   [documentation]
  ○ bd-m3n4    Update README                          [documentation]
  ○ bd-o5p6    Deploy to staging                      [implementation]

Blocked (2):
  ✗ bd-q7r8    Deploy to production                   (blocked by: bd-verification-1)
  ✗ bd-s9t0    Update client SDKs                     (blocked by: bd-k1l2)

Failures (1):
  ❌ bd-fail-1  Test errors in bd-g7h8                 (requires human review)

──────────────────────────────────────────────────────────────────────

Total Beads: 14
  Closed:      6 (43%)
  In Progress: 2 (14%)
  Ready:       3 (21%)
  Blocked:     2 (14%)
  Failed:      1 (7%)

Progress: ████████░░░░░░░░ 43% complete
```

### Filter by Status

```bash
# Show only ready beads
python3 docs/system-prompts/planning-summary.py --status ready

# Show only in-progress beads
python3 docs/system-prompts/planning-summary.py --status in-progress

# Show only closed beads
python3 docs/system-prompts/planning-summary.py --status closed
```

### Filter by Label

```bash
# Show only approval beads
python3 docs/system-prompts/planning-summary.py --label approval

# Show only failures
python3 docs/system-prompts/planning-summary.py --label failure

# Show only documentation beads
python3 docs/system-prompts/planning-summary.py --label documentation
```

### Verbose Mode

```bash
# Show full bead descriptions
python3 docs/system-prompts/planning-summary.py --verbose
```

**Example output:**
```
Beads Status Summary (Verbose)
===============================

Recently Closed (last 5):

  ✓ bd-a1b2.3  Update IAM policies
    Labels: implementation
    Closed: 2h ago
    Description:
      Update IAM policies to grant new Lambda functions
      access to DynamoDB tables and S3 buckets.

      Files:
      - infrastructure/iam/lambda-policies.json

      Verified: All Lambda functions can access resources

  ✓ bd-a1b2.2  Copy Lambda functions
    Labels: implementation
    Closed: 4h ago
    Description:
      Copy Lambda function code from old structure
      to new directory layout.
      ...
```

---

## The Planning-Summary Process

### Data Collection

**Get all beads:**
```bash
# List all beads with full details
bd list --json > /tmp/beads.json
```

**Parse bead data:**
```python
import json

with open('/tmp/beads.json') as f:
    all_beads = json.load(f)

# Group by status
closed = [b for b in all_beads if b['status'] == 'closed']
in_progress = [b for b in all_beads if b['status'] == 'in-progress']
ready = [b for b in all_beads if b['status'] == 'ready']
blocked = [b for b in all_beads if b['status'] == 'not-ready']
```

**Get failure beads:**
```bash
# Failures may be ready or blocked
failures = [b for b in all_beads if 'failure' in b.get('labels', [])]
```

### Formatting Output

**Section 1: Recently Closed**

```python
# Sort by closed time (most recent first)
recent_closed = sorted(closed, key=lambda b: b['closed_at'], reverse=True)[:5]

print("Recently Closed (last 5):")
for bead in recent_closed:
    time_ago = format_time_ago(bead['closed_at'])
    print(f"  ✓ {bead['id']:<12} {bead['title']:<40} (closed {time_ago})")
```

**Section 2: Currently In Progress**

```python
print("\nCurrently In Progress:")
for bead in in_progress:
    time_ago = format_time_ago(bead['claimed_at'])
    assignee = bead.get('assignee', 'unknown')
    print(f"  → {bead['id']:<12} {bead['title']:<40} (claimed {time_ago})")
```

**Section 3: Ready to Work**

```python
print("\nReady to Work:")
for bead in ready:
    labels = ', '.join(bead.get('labels', []))
    print(f"  ○ {bead['id']:<12} {bead['title']:<40} [{labels}]")
```

**Section 4: Blocked**

```python
print("\nBlocked:")
for bead in blocked:
    blockers = ', '.join(bead.get('blocked_by', []))
    print(f"  ✗ {bead['id']:<12} {bead['title']:<40} (blocked by: {blockers})")
```

**Section 5: Failures**

```python
print("\nFailures:")
for bead in failures:
    print(f"  ❌ {bead['id']:<12} {bead['title']:<40} (requires human review)")
```

**Section 6: Statistics**

```python
total = len(all_beads)
closed_pct = int(len(closed) / total * 100) if total > 0 else 0

print(f"\nTotal Beads: {total}")
print(f"  Closed:      {len(closed)} ({closed_pct}%)")
print(f"  In Progress: {len(in_progress)} ({int(len(in_progress)/total*100)}%)")
print(f"  Ready:       {len(ready)} ({int(len(ready)/total*100)}%)")
print(f"  Blocked:     {len(blocked)} ({int(len(blocked)/total*100)}%)")

# Progress bar
progress_bar = '█' * (closed_pct // 5) + '░' * (20 - closed_pct // 5)
print(f"\nProgress: {progress_bar} {closed_pct}% complete")
```

### Time Formatting

**Format relative time:**
```python
from datetime import datetime

def format_time_ago(timestamp):
    """Format timestamp as relative time (e.g., '2h ago', '1d ago')"""
    now = datetime.now()
    delta = now - datetime.fromisoformat(timestamp)

    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    elif seconds < 2592000:  # 30 days
        days = int(seconds / 86400)
        return f"{days}d ago"
    else:
        months = int(seconds / 2592000)
        return f"{months}mo ago"
```

---

## Summary Views

### View 1: Progress Dashboard (Default)

Shows complete status across all categories.

**Use case:** Daily standup, status reports

```bash
python3 docs/system-prompts/planning-summary.py
```

### View 2: Ready Work Queue

Shows only beads ready for implementation.

**Use case:** Selecting next task, orchestrator monitoring

```bash
python3 docs/system-prompts/planning-summary.py --status ready
```

**Example output:**
```
Ready to Work
=============

  ○ bd-k1l2    Document API changes                   [documentation]
  ○ bd-m3n4    Update README                          [documentation]
  ○ bd-o5p6    Deploy to staging                      [implementation]

Total ready: 3
```

### View 3: Active Work

Shows only beads currently in progress.

**Use case:** Monitoring worker status, debugging stalls

```bash
python3 docs/system-prompts/planning-summary.py --status in-progress
```

### View 4: Completed Work

Shows recently closed beads.

**Use case:** Progress reports, weekly reviews

```bash
python3 docs/system-prompts/planning-summary.py --status closed
```

### View 5: Approval Queue

Shows beads awaiting approval.

**Use case:** Human review workflow

```bash
python3 docs/system-prompts/planning-summary.py --label approval --status ready
```

### View 6: Failure Dashboard

Shows only failures requiring attention.

**Use case:** Error monitoring, incident response

```bash
python3 docs/system-prompts/planning-summary.py --label failure
```

**Example output:**
```
Failures Requiring Attention
=============================

  ❌ bd-fail-1  Test errors in bd-g7h8
    Created: 1h ago
    Original bead: bd-g7h8
    Error: test_api.py::test_endpoint - AssertionError

  ❌ bd-fail-2  TIMEOUT: Worker exceeded 60m on bd-i9j0
    Created: 30m ago
    Original bead: bd-i9j0
    Status: Worker timed out, requires review

Total failures: 2

Next steps:
1. Review failure details: bd show bd-fail-1
2. Fix underlying issue
3. Close failure bead: bd update bd-fail-1 --close
4. Retry or close original bead
```

---

## JSON Output for Automation

```bash
# Output JSON for programmatic use
python3 docs/system-prompts/planning-summary.py --json
```

**Example output:**
```json
{
  "summary": {
    "total": 14,
    "closed": 6,
    "in_progress": 2,
    "ready": 3,
    "blocked": 2,
    "failed": 1,
    "completion_percentage": 43
  },
  "recently_closed": [
    {
      "id": "bd-a1b2.3",
      "title": "Update IAM policies",
      "status": "closed",
      "labels": ["implementation"],
      "closed_at": "2026-02-15T10:30:00Z"
    }
  ],
  "in_progress": [
    {
      "id": "bd-g7h8",
      "title": "Implement API endpoint",
      "status": "in-progress",
      "labels": ["implementation"],
      "claimed_at": "2026-02-15T11:00:00Z",
      "assignee": "worker-abc123"
    }
  ],
  "ready": [
    {
      "id": "bd-k1l2",
      "title": "Document API changes",
      "status": "ready",
      "labels": ["documentation"]
    }
  ],
  "blocked": [
    {
      "id": "bd-q7r8",
      "title": "Deploy to production",
      "status": "not-ready",
      "blocked_by": ["bd-verification-1"],
      "labels": ["implementation"]
    }
  ],
  "failures": [
    {
      "id": "bd-fail-1",
      "title": "Test errors in bd-g7h8",
      "status": "ready",
      "labels": ["failure"],
      "created_at": "2026-02-15T10:00:00Z"
    }
  ]
}
```

---

## Integration with Workflows

### Planner Workflow

**After creating beads:**
```bash
# Show summary to verify beads created correctly
python3 docs/system-prompts/planning-summary.py

# Check that approval bead blocks implementation beads
python3 docs/system-prompts/planning-summary.py --status blocked
```

### Human Approval Workflow

**Before approving:**
```bash
# Check how many beads will become ready
python3 docs/system-prompts/planning-summary.py --status blocked

# After closing approval bead, verify beads are now ready
bd update bd-approval-123 --close
python3 docs/system-prompts/planning-summary.py --status ready
```

### Orchestrator Monitoring

**Orchestrator can query summary for health checks:**
```python
import json
import subprocess

result = subprocess.run(
    ['python3', 'docs/system-prompts/planning-summary.py', '--json'],
    capture_output=True,
    text=True
)

summary = json.loads(result.stdout)

if summary['summary']['failed'] > 0:
    # Alert human
    logging.warning(f"{summary['summary']['failed']} failures detected")

if summary['summary']['ready'] == 0 and summary['summary']['in_progress'] == 0:
    # No work available
    logging.info("No work available, pausing orchestrator")
```

### Daily Status Reports

**Generate daily report:**
```bash
#!/bin/bash
# daily-status.sh

echo "Daily Beads Status Report - $(date +%Y-%m-%d)"
echo "=============================================="
echo ""

python3 docs/system-prompts/planning-summary.py

# Email report (optional)
python3 docs/system-prompts/planning-summary.py | mail -s "Daily Status Report" team@example.com
```

---

## Command-Line Interface

### planning-summary.py Usage

```bash
# Default: show all categories (includes all submodules)
python3 docs/system-prompts/planning-summary.py

# Filter by status
python3 docs/system-prompts/planning-summary.py --status <status>
# where <status> is: closed, in-progress, ready, blocked

# Filter by label
python3 docs/system-prompts/planning-summary.py --label <label>
# where <label> is: approval, implementation, documentation, etc.

# Combine filters
python3 docs/system-prompts/planning-summary.py --status ready --label implementation

# Verbose mode (show full descriptions)
python3 docs/system-prompts/planning-summary.py --verbose

# JSON output
python3 docs/system-prompts/planning-summary.py --json

# Limit number of results
python3 docs/system-prompts/planning-summary.py --status closed --limit 10

# Show all (no limit)
python3 docs/system-prompts/planning-summary.py --status closed --limit 0

# Root project only (skip submodules)
python3 docs/system-prompts/planning-summary.py --no-submodules

# Include only specific submodules
python3 docs/system-prompts/planning-summary.py --submodules cackle,pigeon
```

---

## Summary Techniques

### Technique 1: Dependency Visualization

**Show bead with its blockers:**
```bash
# For each blocked bead, show what it's waiting for
for bead in $(bd list --status not-ready --json | jq -r '.[].id'); do
    title=$(bd show $bead --json | jq -r '.title')
    blockers=$(bd show $bead --json | jq -r '.blocked_by | join(", ")')

    echo "$bead: $title"
    echo "  Waiting for: $blockers"

    # Show blocker status
    for blocker in $(bd show $bead --json | jq -r '.blocked_by[]'); do
        blocker_status=$(bd show $blocker --json | jq -r '.status')
        blocker_title=$(bd show $blocker --json | jq -r '.title')
        echo "    - $blocker ($blocker_status): $blocker_title"
    done
done
```

### Technique 2: Velocity Tracking

**Show beads closed per day:**
```python
from datetime import datetime, timedelta
from collections import defaultdict

# Group closed beads by date
closed_by_date = defaultdict(int)

for bead in closed_beads:
    closed_date = datetime.fromisoformat(bead['closed_at']).date()
    closed_by_date[closed_date] += 1

# Show last 7 days
print("Beads Closed (Last 7 Days)")
for i in range(7):
    date = (datetime.now() - timedelta(days=i)).date()
    count = closed_by_date.get(date, 0)
    bar = '█' * count
    print(f"{date}: {bar} ({count})")
```

### Technique 3: Label Distribution

**Show bead count by label:**
```python
from collections import Counter

label_counts = Counter()
for bead in all_beads:
    for label in bead.get('labels', []):
        label_counts[label] += 1

print("Beads by Label:")
for label, count in label_counts.most_common():
    print(f"  {label}: {count}")
```

---

## Troubleshooting

### Summary shows no beads

**Check:**
```bash
# Verify beads is initialized
ls -la .beads/

# Verify beads exist
bd list
```

**Fix:** Create beads or run planning-init.py

### Beads stuck in "blocked" state

**Check:**
```bash
# Show what each blocked bead is waiting for
python3 docs/system-prompts/planning-summary.py --status blocked --verbose
```

**Common causes:**
- Blocker bead not closed
- Circular dependency
- Orphaned dependency

**Fix:** Run planning-doctor.py

### Timestamps showing incorrect relative time

**Cause:** System clock incorrect or timezone mismatch

**Fix:**
```bash
# Check system time
date

# Sync system clock (Linux)
sudo ntpdate pool.ntp.org
```

---

## Success Criteria

**Planning summary is effective when:**

- [ ] Shows all 5 bead categories (closed, in-progress, ready, blocked, failed)
- [ ] Renders in < 1 second for typical projects (< 100 beads)
- [ ] JSON output parseable by automation
- [ ] Supports filtering by status and label
- [ ] Shows recently closed work (last 5 or configurable)
- [ ] Displays progress percentage accurately
- [ ] Time formatting is human-readable ("2h ago" not "7200 seconds ago")

---

## See Also

- **[Planning Init](planning-init.md)** - Initialize beads in project
- **[Planning Doctor](planning-doctor.md)** - Detect and fix bead issues
- **[Plan-and-Dispatch Workflow](../workflows/plan-and-dispatch.md)** - Workflow using beads
- **[External Orchestrator](../workflows/external-orchestrator.md)** - Orchestrator status monitoring

---

**Last Updated:** 2026-02-18
**Recent Updates:** 2026-02-18 - Added multi-project support documentation (submodule discovery, `--no-submodules`, `--submodules` flags)
