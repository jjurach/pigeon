# Planning Doctor Process

**Purpose:** Detect and fix problems in the beads database to maintain healthy task tracking state.

**Status:** Documented

**Prerequisites:**
- Beads initialized in project (`.beads/` exists)
- Python 3.8+

---

## Overview

The planning-doctor process diagnoses common issues in beads task tracking:

1. **Orphaned beads** - Beads blocked by non-existent beads
2. **Circular dependencies** - Beads that block each other (deadlock)
3. **Stale in-progress beads** - Beads claimed but abandoned by workers
4. **Missing labels** - Beads without type labels
5. **Malformed descriptions** - Beads with incomplete or unclear descriptions

This process can detect issues automatically and offer fixes (some automated, some require human intervention).

---

## When to Use This Process

**Use planning-doctor when:**
- ✅ Beads seem stuck or not becoming ready
- ✅ Orchestrator reports issues with work dispatch
- ✅ Periodic health check (recommended weekly)
- ✅ After manual bead manipulation
- ✅ Debugging workflow problems

**Skip this process when:**
- ❌ Beads not initialized in project
- ❌ Everything working normally (though periodic checks still recommended)

---

## Usage

### Automated Check (Recommended)

```bash
# Run planning doctor
python3 docs/system-prompts/planning-doctor.py
```

**Note:** The script includes a **fallback mechanism** that reads directly from `.beads/issues.jsonl` if the `bd` CLI is not available or fails. This ensures health checks work in restricted environments.

**Output example:**
```
Beads Health Check
==================

Checking for issues...

✓ No orphaned beads found
✗ Found 2 circular dependencies
✓ No stale in-progress beads
⚠ Found 3 beads without labels
✓ All bead descriptions well-formed

=== Issues Found ===

1. Circular Dependencies (2):
   - bd-a1b2 blocks bd-c3d4, bd-c3d4 blocks bd-a1b2
   - bd-e5f6 blocks bd-g7h8, bd-g7h8 blocks bd-e5f6

   Manual fix required:
   bd dep remove <child-id> <parent-id>

2. Missing Labels (3):
   - bd-i9j0: "Update API documentation"
   - bd-k1l2: "Fix test failures"
   - bd-m3n4: "Deploy to staging"

   Suggested fixes:
   bd update bd-i9j0 --label documentation
   bd update bd-k1l2 --label verification
   bd update bd-m3n4 --label implementation

=== Summary ===

Issues: 5
Warnings: 3
Auto-fixable: 0
Manual fix required: 5

Run with --fix to automatically fix issues (where possible)
```

### With Auto-Fix

```bash
# Run with automatic fixes
python3 docs/system-prompts/planning-doctor.py --fix
```

**Auto-fixes:**
- Remove orphaned dependencies
- Add suggested labels (with confirmation)

**Cannot auto-fix:**
- Circular dependencies (ambiguous which dependency to remove)
- Stale in-progress beads (unclear if work is complete)

---

## The Planning-Doctor Process

### Check 1: Orphaned Beads

**Issue:** Bead A is `blocked_by` Bead B, but Bead B doesn't exist

**Cause:**
- Bead B was manually deleted
- Database corruption
- Incorrect manual manipulation

**Detection:**
```bash
# For each bead, check if its blockers exist
for bead in $(bd list --json | jq -r '.[].id'); do
    blockers=$(bd show $bead --json | jq -r '.blocked_by[]?')

    for blocker in $blockers; do
        if ! bd show $blocker > /dev/null 2>&1; then
            echo "✗ $bead blocked by non-existent $blocker"
        fi
    done
done
```

**Fix:**
```bash
# Remove orphaned dependency
bd dep remove $bead $blocker

# After fix, bead should become ready (if no other blockers)
```

**Auto-fix:** Yes (safe to automatically remove)

---

### Check 2: Circular Dependencies

**Issue:** Bead A blocks Bead B, and Bead B blocks Bead A (or longer cycles)

**Cause:**
- Incorrect manual dependency additions
- Logic error in dependency planning
- Copy-paste error when creating beads

**Detection:**
```bash
# Build dependency graph
# Perform depth-first search to detect cycles
# (Implementation in planning-doctor.py)
```

**Example:**
```
bd-a1b2 (blocked_by: bd-c3d4)
bd-c3d4 (blocked_by: bd-a1b2)

Result: Both beads stuck, neither can become ready
```

**Fix (manual):**
```bash
# Determine which dependency is incorrect
# Remove incorrect dependency

# Example: If A should depend on C (not vice versa)
bd dep remove bd-c3d4 bd-a1b2  # Remove C blocked by A

# Result: C becomes ready, then A becomes ready after C closed
```

**Auto-fix:** No (ambiguous which dependency to remove)

**Recommendation:** Report to human with graph visualization

---

### Check 3: Stale In-Progress Beads

**Issue:** Bead has status "in-progress" but worker abandoned it

**Cause:**
- Worker crashed without creating failure bead
- Worker timeout (orchestrator killed worker)
- Manual claim without implementation
- Worker forgot to close bead

**Detection:**
```bash
# Find beads in-progress for > threshold time (e.g., 24 hours)
threshold_hours=24

for bead in $(bd list --status in-progress --json | jq -r '.[].id'); do
    claimed_at=$(bd show $bead --json | jq -r '.claimed_at')
    now=$(date +%s)
    age_hours=$(( ($now - $claimed_at) / 3600 ))

    if [ $age_hours -gt $threshold_hours ]; then
        echo "⚠ $bead in-progress for ${age_hours}h (claimed by $(bd show $bead --json | jq -r '.assignee'))"
    fi
done
```

**Fix (manual):**

**Option 1: Work is actually complete**
```bash
# Close bead
bd update $bead --close
```

**Option 2: Work is incomplete**
```bash
# Unclaim bead so it becomes ready again
bd update $bead --unclaim
```

**Option 3: Work failed but no failure bead**
```bash
# Create failure bead documenting the issue
bd create "STALE: $bead abandoned by worker" --label failure \
  --body "Bead $bead was in-progress for ${age_hours}h but worker appears to have abandoned it.

Review work status and determine if:
- Work is complete (close bead)
- Work is incomplete (unclaim and retry)
- Work failed (investigate and create proper failure bead)"

# Block original bead
bd dep add $bead $failure_bead_id
```

**Auto-fix:** No (requires human judgment)

**Recommendation:** List stale beads with details, let human decide

---

### Check 4: Missing Labels

**Issue:** Bead has no `--label` or has generic label

**Cause:**
- Created with `bd create "title"` without `--label` flag
- Forgot to add label
- Label not meaningful (e.g., `--label todo`)

**Detection:**
```bash
# Find beads without labels or with generic labels
for bead in $(bd list --json | jq -r '.[].id'); do
    labels=$(bd show $bead --json | jq -r '.labels[]?')

    if [ -z "$labels" ]; then
        echo "⚠ $bead has no labels"
    elif [[ "$labels" =~ ^(todo|task|item)$ ]]; then
        echo "⚠ $bead has generic label: $labels"
    fi
done
```

**Fix:**
```bash
# Add appropriate label based on bead title/description

# Examples:
bd update $bead --label approval       # If title contains "Approve"
bd update $bead --label implementation # If title contains "Implement"
bd update $bead --label documentation  # If title contains "Document"
bd update $bead --label verification   # If title contains "Test" or "Verify"
bd update $bead --label research       # If title contains "Research" or "Investigate"
```

**Auto-fix:** Partial (can suggest labels based on title, require confirmation)

**Heuristics for label suggestion:**
```python
title_lower = bead_title.lower()

if 'approve' in title_lower or 'approval' in title_lower:
    suggested_label = 'approval'
elif 'implement' in title_lower or 'add' in title_lower or 'create' in title_lower:
    suggested_label = 'implementation'
elif 'document' in title_lower or 'docs' in title_lower:
    suggested_label = 'documentation'
elif 'test' in title_lower or 'verify' in title_lower:
    suggested_label = 'verification'
elif 'research' in title_lower or 'investigate' in title_lower:
    suggested_label = 'research'
elif 'milestone' in title_lower or 'epic' in title_lower:
    suggested_label = 'milestone'
else:
    suggested_label = 'implementation'  # Default
```

---

### Check 5: Malformed Descriptions

**Issue:** Bead description is unclear, incomplete, or doesn't follow conventions

**Problems to detect:**

**5.1: Empty or very short descriptions**
```bash
# Find beads with no body or very short body
for bead in $(bd list --json | jq -r '.[].id'); do
    body=$(bd show $bead --json | jq -r '.body // ""')
    length=${#body}

    if [ $length -lt 20 ]; then
        echo "⚠ $bead has very short description ($length chars)"
    fi
done
```

**5.2: Approval beads without plan reference**
```bash
# Find approval beads that don't reference plan file
for bead in $(bd list --label approval --json | jq -r '.[].id'); do
    body=$(bd show $bead --json | jq -r '.body')

    if ! echo "$body" | grep -q "Plan:"; then
        echo "⚠ Approval bead $bead doesn't reference plan file"
    fi
done
```

**5.3: Failure beads without error details**
```bash
# Find failure beads without error context
for bead in $(bd list --label failure --json | jq -r '.[].id'); do
    body=$(bd show $bead --json | jq -r '.body')

    if ! echo "$body" | grep -q "Error Details:"; then
        echo "⚠ Failure bead $bead missing error details"
    fi
done
```

**Fix:** Report issues to human for manual correction

**Auto-fix:** No (requires understanding of context)

---

## Planning Doctor Output Format

### Check Mode (Default)

```
Beads Health Check
==================

Running 5 checks...

[1/5] Checking for orphaned beads...
✓ No orphaned beads found

[2/5] Checking for circular dependencies...
✗ Found 2 circular dependencies

[3/5] Checking for stale in-progress beads...
⚠ Found 1 stale bead (in-progress > 24h)

[4/5] Checking for missing labels...
⚠ Found 3 beads without labels

[5/5] Checking for malformed descriptions...
⚠ Found 2 approval beads without plan references

=== Issues Found ===

1. Circular Dependencies (2)
   [Details...]

2. Stale In-Progress Beads (1)
   [Details...]

3. Missing Labels (3)
   [Details...]

4. Malformed Descriptions (2)
   [Details...]

=== Summary ===

Checks passed: 1/5
Issues: 6
Warnings: 6
Auto-fixable: 3
Manual fix required: 3

Next steps:
- Review issues above
- Run with --fix to auto-fix safe issues
- Manually fix remaining issues
```

### Fix Mode (--fix)

```
Beads Health Check
==================

Running 5 checks...

[1/5] Checking for orphaned beads...
✓ No orphaned beads found

[2/5] Checking for circular dependencies...
✗ Found 2 circular dependencies
   (Cannot auto-fix, manual intervention required)

[3/5] Checking for stale in-progress beads...
⚠ Found 1 stale bead
   (Cannot auto-fix, manual review required)

[4/5] Checking for missing labels...
⚠ Found 3 beads without labels

   Fix: bd-i9j0 "Update API documentation"
   Suggested label: documentation
   Apply fix? [y/N]: y
   ✓ Applied label 'documentation' to bd-i9j0

   Fix: bd-k1l2 "Fix test failures"
   Suggested label: verification
   Apply fix? [y/N]: y
   ✓ Applied label 'verification' to bd-k1l2

   Fix: bd-m3n4 "Deploy to staging"
   Suggested label: implementation
   Apply fix? [y/N]: n
   ⊘ Skipped bd-m3n4

[5/5] Checking for malformed descriptions...
⚠ Found 2 approval beads without plan references
   (Cannot auto-fix, requires human context)

=== Summary ===

Fixes applied: 2
Fixes skipped: 1
Manual fixes required: 4

Review remaining issues and fix manually.
```

---

## Integration with Workflows

### Periodic Health Checks

**Recommended schedule:**
- **Daily** if using orchestrator (automated dispatch)
- **Weekly** if manual workflow
- **Before important milestones** (releases, demos)

**Automation:**
```bash
# Add to cron or scheduled task
# Run daily at 9am
0 9 * * * cd /path/to/project && python3 docs/system-prompts/planning-doctor.py --check-only --email-report
```

### Pre-Dispatch Health Check

**Orchestrator integration:**
```python
# In orchestrator main loop
def check_health_before_dispatch(self):
    """Run health check before dispatching work"""
    result = subprocess.run(
        ['python3', 'docs/system-prompts/planning-doctor.py', '--check-only', '--json'],
        capture_output=True,
        text=True
    )

    health = json.loads(result.stdout)

    if health['critical_issues'] > 0:
        logging.warning(f"Beads health check found {health['critical_issues']} critical issues")
        logging.warning("Pausing orchestration, run planning-doctor.py to fix")
        self.paused = True
        return False

    return True
```

---

## Command-Line Interface

### planning-doctor.py Usage

```bash
# Check for issues (no fixes)
python3 docs/system-prompts/planning-doctor.py

# Check and auto-fix safe issues
python3 docs/system-prompts/planning-doctor.py --fix

# Check only (no output unless issues found)
python3 docs/system-prompts/planning-doctor.py --check-only

# Output JSON for automation
python3 docs/system-prompts/planning-doctor.py --json

# Specific checks only
python3 docs/system-prompts/planning-doctor.py --check orphaned
python3 docs/system-prompts/planning-doctor.py --check circular
python3 docs/system-prompts/planning-doctor.py --check stale

# Verbose output
python3 docs/system-prompts/planning-doctor.py --verbose
```

---

## Troubleshooting

### Doctor script reports errors running bd commands

**Check:**
```bash
# Verify beads is initialized
ls -la .beads/

# Verify bd CLI works
bd ready
```

**Fix:** Run planning-init.py if beads not initialized

### False positives for stale beads

**Cause:** Long-running tasks legitimately in-progress

**Fix:** Adjust stale threshold
```bash
# Default: 24 hours
python3 docs/system-prompts/planning-doctor.py --stale-threshold 48
```

### Circular dependency detection takes too long

**Cause:** Large number of beads, complex dependency graph

**Optimization:** Use memoization in cycle detection algorithm (implemented in planning-doctor.py)

---

## Success Criteria

**Planning doctor is effective when:**

- [ ] Detects all 5 categories of issues
- [ ] Auto-fixes safe issues without human intervention
- [ ] Reports manual-fix issues clearly with recommendations
- [ ] Completes health check in < 5 seconds for typical projects
- [ ] JSON output parseable by automation tools
- [ ] No false positives (correct detection rate > 95%)

---

## See Also

- **[Planning Init](planning-init.md)** - Initialize beads in project
- **[Planning Summary](planning-summary.md)** - View bead status
- **[Plan-and-Dispatch Workflow](../workflows/plan-and-dispatch.md)** - Workflow using beads
- **[External Orchestrator](../workflows/external-orchestrator.md)** - Orchestrator health integration

---

**Last Updated:** 2026-02-15
