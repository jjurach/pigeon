# Planning Init Process

**Purpose:** Initialize beads in a project with project-specific setup and configuration.

**Status:** Documented

**Prerequisites:**
- Beads CLI installed: `npm install -g @beads/bd` (provides the `bd` command)
- Project uses git version control

---

## About the `bd` Command

The `bd` command is provided by the **`@beads/bd` npm package**. This is the command-line interface for the Beads task tracking system. All commands in this documentation use `bd` as shorthand for this tool.

---

## Overview

The planning-init process sets up beads task tracking in a project. This process:

1. Verifies beads CLI is available
2. Initializes beads database (`.beads/` directory)
3. Creates label documentation for bead patterns
4. Provides example beads for reference
5. Verifies initialization successful

**This process is optional.** Projects can choose not to use beads and continue with project_plans-only workflow.

---

## When to Use This Process

**Use planning-init when:**
- ✅ Setting up beads for the first time in a project
- ✅ Re-initializing beads after accidental deletion
- ✅ Adopting plan-and-dispatch workflow

**Skip this process when:**
- ❌ Beads already initialized (`.beads/` exists)
- ❌ Project doesn't need beads (simple single-agent workflow)
- ❌ Just using logs-first workflow without task tracking

---

## Usage

### Automated Initialization (Recommended)

```bash
# Run helper script
python3 docs/system-prompts/planning-init.py
```

The script will:
- Check if beads CLI is installed
- Check if beads is already initialized
- Run `bd init` if needed
- Create label documentation
- Create example beads (optional)
- Verify initialization

### Manual Initialization

If you prefer manual setup:

```bash
# Initialize beads
bd init

# Verify initialization
ls -la .beads/
```

---

## The Planning-Init Process

### Step 1: Verify Prerequisites

**Check beads CLI is installed:**
```bash
which bd
# Should output: /path/to/bd

bd --version
# Should output version number
```

**If beads not installed:**
```bash
npm install -g @beads/bd
```

The `@beads/bd` package provides the `bd` command-line tool.

**Check git is initialized:**
```bash
git status
# Should NOT error with "not a git repository"
```

**If git not initialized:**
```bash
git init
```

---

### Step 2: Check if Beads Already Initialized

```bash
if [ -d .beads ]; then
    echo "✓ Beads already initialized"
    echo "To re-initialize, remove .beads/ directory first:"
    echo "  rm -rf .beads/"
    exit 0
else
    echo "✗ Beads not initialized, proceeding..."
fi
```

**If `.beads/` exists:**
- Beads is already initialized
- Do NOT re-initialize (will lose existing beads)
- To reset, manually remove `.beads/` directory first

---

### Step 3: Initialize Beads Database

```bash
bd init
```

**Expected output:**
```
Initialized beads database in .beads/
```

**Verify initialization:**
```bash
ls -la .beads/
# Should show:
# drwxr-xr-x  .beads/
# -rw-r--r--  .beads/config
# -rw-r--r--  .beads/beads.jsonl
# (and other beads internal files)
```

---

### Step 4: Configure Project-Specific Settings

**Create `.beads/README.md` documenting bead patterns:**

```bash
cat > .beads/README.md <<'EOF'
# Beads Configuration

This project uses beads for task tracking with the plan-and-dispatch workflow.

## Bead Labels

This project uses the following bead label conventions:

### Core Labels

- **approval** - Blocks implementation until human reviews and approves plan
  - Created by planner
  - References project plan file
  - Implementation beads are `blocked_by` approval bead
  - Human closes approval bead when plan is approved

- **implementation** - Standard implementation work
  - Created by planner based on project plan phases
  - May have dependencies on other implementation beads
  - Worker claims, implements, and closes

- **milestone** - Groups related work (epic-level)
  - Uses hierarchical IDs (bd-a1b2 with subtasks bd-a1b2.1, bd-a1b2.2)
  - Closed when all subtasks complete

- **planning** - Converts inbox items into executable plans
  - Created when processing dev_notes/inbox
  - Closes when spec, plan, and beads created

- **research** - Investigation/discovery work (no code changes)
  - Closes when findings documented

- **verification** - Quality gates (e.g., "All tests pass")
  - Blocks deployment or release beads
  - Closes when verification criteria met

- **documentation** - Documentation work
  - Often `blocked_by` implementation beads
  - Closes when docs updated

- **worker-session** - Audit trail of worker agent sessions
  - Created by orchestrator (not manually)
  - Links to work beads via `relates_to`
  - Closes when worker session ends

- **failure** - Tracks worker failures requiring human intervention
  - Created by workers on non-trivial errors
  - Blocks original work bead until resolved
  - Human closes after fixing issue

## Workflow

See [Plan-and-Dispatch Workflow](../docs/system-prompts/workflows/plan-and-dispatch.md) for complete workflow documentation.

## Commands

```bash
# View ready beads
bd ready

# View all beads by status
python3 docs/system-prompts/planning-summary.py

# Detect issues
python3 docs/system-prompts/planning-doctor.py

# Create bead
bd create "Task title" --label <type>

# Show bead details
bd show <bead-id>

# Claim bead for work
bd update <bead-id> --claim

# Close bead
bd update <bead-id> --close

# Add dependency (child blocked by parent)
bd dep add <child-id> <parent-id>
```

## External Orchestrator

This project may use an external orchestrator to dispatch ready beads to worker agents.

See [External Orchestrator](../docs/system-prompts/workflows/external-orchestrator.md) for architecture details.

EOF
```

**Add .beads/ to .gitignore (optional):**

Beads exports to JSONL for git portability, so you can choose whether to track `.beads/` internal files.

**Option A: Track everything (recommended for small teams)**
```bash
# Don't add to .gitignore
# All bead state tracked in git
```

**Option B: Track exports only**
```bash
echo ".beads/*" >> .gitignore
echo "!.beads/*.jsonl" >> .gitignore
echo "!.beads/README.md" >> .gitignore
```

---

### Step 5: Create Example Beads (Optional)

**Create example approval bead:**
```bash
bd create "EXAMPLE: Approve Project Plan" --label approval \
  --body "This is an example approval bead.

Plan: dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_example.md

Review Checklist:
- [ ] Plan phases clear
- [ ] Dependencies identified
- [ ] Risk mitigation adequate

Close this bead to unblock implementation beads."
```

**Create example implementation bead:**
```bash
bd create "EXAMPLE: Implement Feature X" --label implementation \
  --body "This is an example implementation bead.

Task: Implement feature X as described in project plan phase 2.

Details:
- File: src/feature_x.py
- Tests: tests/test_feature_x.py

When complete:
- Follow close-project.md process
- Close this bead: bd update <id> --close"

# Add dependency (blocked by approval)
approval_id=$(bd ready --label approval --json | jq -r '.[0].id')
impl_id=$(bd ready --label implementation --json | jq -r '.[0].id')
bd dep add $impl_id $approval_id
```

**View example beads:**
```bash
bd ready
# Should show approval bead (ready)
# Implementation bead should be blocked (not in ready list)

bd show $approval_id
bd show $impl_id
```

**Clean up examples:**
```bash
# Close example beads
bd update $approval_id --close
bd update $impl_id --close

# Or delete them
# (beads doesn't have delete command, mark as closed)
```

---

### Step 6: Verify Initialization

**Run verification checks:**

```bash
echo "=== Beads Initialization Verification ==="

# 1. Check beads database exists
if [ -d .beads ]; then
    echo "✓ .beads/ directory exists"
else
    echo "✗ .beads/ directory missing"
    exit 1
fi

# 2. Check beads CLI works
if bd ready > /dev/null 2>&1; then
    echo "✓ bd ready command works"
else
    echo "✗ bd ready command failed"
    exit 1
fi

# 3. Check label documentation exists
if [ -f .beads/README.md ]; then
    echo "✓ .beads/README.md exists"
else
    echo "⚠  .beads/README.md missing (optional)"
fi

# 4. Check if can create test bead
test_id=$(bd create "TEST" --label test --body "test" 2>&1 | grep -oP 'bd-[a-z0-9]+' | head -1)
if [ -n "$test_id" ]; then
    echo "✓ Can create beads (created $test_id)"
    # Clean up test bead
    bd update $test_id --close > /dev/null 2>&1
else
    echo "✗ Failed to create test bead"
    exit 1
fi

echo ""
echo "=== Initialization Successful ==="
echo "Beads is now configured and ready to use."
echo ""
echo "Next steps:"
echo "1. See docs/system-prompts/workflows/plan-and-dispatch.md for workflow"
echo "2. Process inbox items with plan-and-dispatch workflow"
echo "3. Use 'python3 docs/system-prompts/planning-summary.py' to view status"
```

---

### Step 7: Document Initialization

**Create change log (optional but recommended):**

```bash
timestamp=$(date +%Y-%m-%d_%H-%M-%S)
cat > dev_notes/changes/${timestamp}_beads-initialization.md <<EOF
# Beads Initialization

**Date:** $(date +%Y-%m-%d)
**Status:** Complete

## Summary

Initialized beads task tracking in project using planning-init process.

## Changes

- Initialized beads database: \`.beads/\`
- Created label documentation: \`.beads/README.md\`
- Configured project for plan-and-dispatch workflow

## Verification

\`\`\`bash
bd ready
# Works correctly

python3 docs/system-prompts/planning-summary.py
# Works correctly
\`\`\`

## Next Steps

- Process inbox items using plan-and-dispatch workflow
- Create approval beads for project plans
- Set up external orchestrator (optional)

---

Bead: N/A (initialization change)
EOF
```

**Commit changes:**
```bash
git add .beads/ dev_notes/changes/${timestamp}_beads-initialization.md
git commit -m "chore: initialize beads task tracking

Initialized beads for plan-and-dispatch workflow.

Changes:
- Created .beads/ database
- Added label documentation
- Verified initialization successful

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Troubleshooting

### Issue: bd command not found

**Cause:** Beads CLI not installed

**Fix:**
```bash
npm install -g @steveyegge/beads

# Verify installation
which bd
bd --version
```

### Issue: bd init fails with "already initialized"

**Cause:** `.beads/` directory already exists

**Fix:**
```bash
# Check if beads is actually initialized
ls -la .beads/

# If you want to re-initialize (WARNING: destroys existing beads)
rm -rf .beads/
bd init
```

### Issue: Permission denied when creating .beads/

**Cause:** Insufficient permissions in project directory

**Fix:**
```bash
# Check directory permissions
ls -ld .

# Fix permissions if needed
chmod u+w .
```

### Issue: Git not initialized

**Cause:** Project directory is not a git repository

**Fix:**
```bash
git init
git add .
git commit -m "Initial commit"

# Now run bd init
bd init
```

---

## Success Criteria

**Beads initialization is complete when:**

- [ ] `.beads/` directory exists
- [ ] `bd ready` command works without errors
- [ ] `.beads/README.md` documents label conventions
- [ ] Can create, show, and close beads
- [ ] Can add dependencies between beads
- [ ] Verification script passes all checks
- [ ] Changes committed to git (optional but recommended)

---

## See Also

- **[Plan-and-Dispatch Workflow](../workflows/plan-and-dispatch.md)** - Workflow using beads
- **[Planning Doctor](planning-doctor.md)** - Detect and fix bead issues
- **[Planning Summary](planning-summary.md)** - View bead status
- **[External Orchestrator](../workflows/external-orchestrator.md)** - Orchestrator setup

---

**Last Updated:** 2026-02-15
