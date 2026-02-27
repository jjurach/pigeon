# Agent Beads Detection & Integration Guide

**For:** AI agents starting work on any project
**Purpose:** Detect beads workflow and integrate it into project planning
**When to Read:** At the start of EVERY session before planning work

---

## Quick Start: 30-Second Beads Check

Before creating any project plan:

```bash
# Check if beads is active
if [ -d ".beads" ]; then
  echo "✓ Beads is sticky - include beads commands in plan"
  bd list --status=ready   # Show ready work
else
  echo "✗ Beads not active - use logs-only workflow"
fi
```

**Result:**
- If `.beads/` exists → Use beads in your project plans
- If `.beads/` missing → Use dev_notes/changes/ documentation

---

## The Decision: Will This Plan Use Beads?

### YES: Use Beads Commands In Your Plan

**Condition:** `.beads/` directory exists in project root

**What to do:**
- Reference existing beads in your plan ("Pick up sv-3 from bd ready")
- Create new beads for work items ("Create beads for feature X")
- Use `bd create`, `bd list`, `bd close`, `bd update` in workflows
- Include `bd sync` in session completion steps

**Example Plan Section:**
```markdown
## Beads Integration

**Active Beads:** sv-15 (enhancement)

### Tasks
1. bd list --status=ready  → Find actionable work
2. bd update sv-15 --status=in_progress
3. [Do the work]
4. bd close sv-15 --reason="Completed"
5. bd sync  → Commit beads changes

### New Beads (if creating)
- Create sv-16: "Add authentication UI"
- Create sv-17: "Update API docs"
```

### NO: Use Logs-Only Workflow

**Condition:** `.beads/` directory does NOT exist in project root

**What to do:**
- Don't create or mention beads commands
- Use dev_notes/changes/ for documentation
- Keep plans focused on code changes, not task tracking
- End session with `git push` (no `bd sync` needed)

**Example Plan Section:**
```markdown
## Documentation

After implementation:
- Create dev_notes/changes/YYYY-MM-DD_HH-MM-SS_feature-x.md
- Document: what changed, why, verification results
- Commit and push
```

---

## Session Start Checklist

Every agent should run this checklist at session start:

```bash
# Step 1: Check for beads
if [ -d ".beads" ]; then
  BEADS_ACTIVE=true
  echo "✓ Beads workflow detected"
else
  BEADS_ACTIVE=false
  echo "✗ No beads (logs-only workflow)"
fi

# Step 2: Check git status
git status

# Step 3: If beads active, show ready work
if $BEADS_ACTIVE; then
  echo ""
  echo "=== Ready Work (from beads) ==="
  bd ready
  echo ""
fi
```

**Record findings in your mental context:**
- Beads active? (yes/no)
- Any ready work? (if yes, list it)
- Current branch status? (ahead/behind)

---

## Project Planning: Include Beads If Sticky

### Beads-Enabled Project (`.beads/` exists)

**Your project plan should:**

1. **Start with beads status:**
   ```markdown
   ## Beads Status

   **Project Issue:** sv-12 (Feature: Add authentication)
   **Current Status:** Ready
   **Assigned:** [Your agent name]
   ```

2. **Use beads commands in workflow:**
   ```markdown
   ## Implementation Steps

   1. Mark bead as in-progress: `bd update sv-12 --status=in_progress`
   2. [Your implementation work here]
   3. Create sub-beads if needed: `bd create --parent=sv-12 ...`
   4. Close bead: `bd close sv-12 --reason="Completed"`
   ```

3. **Include bd sync in completion:**
   ```markdown
   ## Session Completion

   - [ ] Implementation complete
   - [ ] Tests pass
   - [ ] bd close sv-12 [with reason]
   - [ ] bd sync
   - [ ] git push
   ```

### Logs-Only Project (`.beads/` missing)

**Your project plan should:**

1. **Skip beads entirely:**
   ```markdown
   # Project Plan: Feature X

   [No beads-related content]
   ```

2. **Plan for dev_notes documentation:**
   ```markdown
   ## Documentation

   - Create dev_notes/changes/YYYY-MM-DD_HH-MM-SS_feature-x.md
   - Include: what changed, verification, known issues
   ```

3. **Standard git completion:**
   ```markdown
   ## Session Completion

   - [ ] Implementation complete
   - [ ] Tests pass
   - [ ] git commit -m "..."
   - [ ] git push
   ```

---

## Common Scenarios

### Scenario 1: First Session, No Beads

```
Agent: Check .beads/ → NOT FOUND
Action: Use logs-only workflow
Plan includes: dev_notes/changes documentation
Session ends with: git push (no bd sync)
```

### Scenario 2: First Session, Beads Requested

```
Agent: Check .beads/ → NOT FOUND
User prompt: "Set up beads for this project"
Action: Execute bootstrap-project.md Phase 6.5
Result: .beads/ created → Beads is now STICKY
Plan includes: bd create, bd close, bd sync
```

### Scenario 3: Subsequent Session, Beads Active

```
Agent: Check .beads/ → FOUND
Action: Beads is sticky, use automatically
Plan includes: bd ready, bd list, bd update
Session ends with: bd sync, git push
```

### Scenario 4: Ignore Beads Request If Not Initialized

```
User: "Add authentication"
Agent: Check .beads/ → NOT FOUND
User prompt: No mention of beads
Action: Don't initialize beads
Use logs-only workflow
```

**Note:** User must explicitly request beads setup. Don't initialize it without asking.

---

## ⚠️ CRITICAL: Backend is Dolt — NEVER Manipulate SQLite Directly ⚠️

This project's bead database is backed by **Dolt** (a version-controlled SQL database).
The git-tracked export is `.beads/issues.jsonl`.

**`.db` files are intentionally gitignored as legacy artifacts.** Do not create, read,
or write them.

```bash
# ❌ WRONG — bypasses Dolt, won't appear in issues.jsonl, will confuse hatchery
sqlite3 .beads/beads.db "INSERT INTO beads ..."
python3 -c "sqlite3.connect('.beads/beads.db') ..."

# ✅ CORRECT — always use bd CLI
bd create "Title" --description "..." --priority 1
```

**After every `bd create` or `bd close`, you MUST run `bd sync` and commit:**

```bash
bd sync                            # flush Dolt → .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "chore: sync beads after <operation>"
```

If you skip `bd sync`, the beads exist in Dolt but `issues.jsonl` is stale and the
git history will be missing the change.

---

## Commands Reference

### Check Beads Status

```bash
# Is beads initialized?
[ -d ".beads" ] && echo "yes" || echo "no"

# What beads are ready?
bd list --status open

# Show specific bead
bd show <bead-id>
```

### Create Beads

```bash
# Basic create (title is a positional argument)
bd create "Title of the bead" \
  --description "Full description of work to be done" \
  --priority 1

# Create with explicit ID (use when plan references the ID)
bd create --id prefix-p91 \
  --priority 0 \
  --deps "prefix-bk7,prefix-mc4" \
  "Title" \
  --description "Full description..."

# Create silently — returns only the ID (use in scripts)
ID=$(bd create --silent "Title" --description "..." --priority 1)
echo "Created: $ID"

# Common flags
#   --priority N        0=most urgent, 4=backlog (default: 2)
#   --deps "id1,id2"    comma-separated dependency IDs
#   --id PREFIX-xxx     explicit bead ID
#   --type task|feature|bug|chore   (default: task)
#   --silent            output only the bead ID
```

### Work with Beads

```bash
# Close bead
bd close <bead-id>

# List by status
bd list --status open

# MANDATORY after any create/close: sync Dolt → issues.jsonl
bd sync
git add .beads/issues.jsonl
git commit -m "chore: sync beads after <description>"
```

### Common Patterns

```bash
# At session start: check what's ready
bd list --status open

# During work: create beads for new tasks
bd create "Fix login bug" --description "..." --priority 1
bd sync && git add .beads/issues.jsonl && git commit -m "chore: add login bug bead"

# On completion: close and sync
bd close <bead-id>
bd sync && git add .beads/issues.jsonl && git commit -m "chore: close <bead-id>"
```

---

## Troubleshooting

### "I'm not sure if I should use beads"

**Decision tree:**
1. Does `.beads/` directory exist?
   - YES → Use beads (it's sticky)
   - NO → Go to step 2
2. Does user's prompt mention beads?
   - YES → Initialize beads first (Phase 6.5), then use
   - NO → Don't use beads

### "User mentioned beads, but .beads/ doesn't exist"

**Action:**
- Execute Phase 6.5 of bootstrap-project.md
- Create `.beads/` directory
- Initialize config and labels
- Beads is now sticky for future sessions

### "What if I remove .beads/ by accident?"

**Recovery:**
1. Check git: `git status` (should show .beads/ as deleted)
2. Ask user: "Should I restore beads or continue without it?"
3. If YES: `git restore .beads/` and `bd sync`
4. If NO: Delete `.beads/` completely and clean up git

### "Should I update a closed bead?"

**No.** Closed beads are final.
- If work reopens: Create a new bead (sv-12b or new ID)
- If work needs continuation: Use `bd update <id> --status=ready` (if not closed yet)

---

## Integration with Agent Workflows

### Step 1: Session Start (First Thing)

```bash
# Beads check
if [ -d ".beads" ]; then
  echo "Beads-enabled project"
  bd ready  # Show what's available
else
  echo "Logs-only project"
fi

# Other checks
git status
git log --oneline -3
```

### Step 2: Planning

- Declare which beads you're working on (if any)
- Create new beads if needed
- Include beads commands in project plan

### Step 3: Implementation

- Update bead status: `bd update <id> --status=in_progress`
- Do the work
- Test thoroughly

### Step 4: Completion

- Close bead: `bd close <id> --reason="..."`
- Run tests: `pytest`, etc.
- Create change documentation
- `bd sync` (if beads-enabled)
- `git commit` and `git push`

### Step 5: Next Session Prep

- Sync: `bd sync` (if beads-enabled)
- Check ready: `bd ready` (if beads-enabled)
- Continue where you left off

---

## Agent Responsibilities

### DO:
- ✅ Check for `.beads/` at session start
- ✅ Use beads commands if directory exists
- ✅ Include `bd sync` in completion if beads is active
- ✅ Create beads for major work items (if beads-enabled)
- ✅ Close beads when work completes (if beads-enabled)
- ✅ Document beads interactions in plans

### DON'T:
- ❌ Initialize beads without user request
- ❌ Ignore beads if `.beads/` exists
- ❌ Mix beads and logs-only workflows (pick one based on project state)
- ❌ Forget `bd sync` before pushing (if beads is active)
- ❌ Close beads prematurely (only close when truly done)

---

## Questions for Agents

After reading this guide, you should be able to answer:

1. **What's the first thing to check?** → Check if `.beads/` exists
2. **What if it exists?** → Use beads commands automatically
3. **What if it doesn't and user mentions beads?** → Initialize beads first
4. **What if it doesn't and user doesn't mention beads?** → Use logs-only
5. **When do I use bd sync?** → Before git push (if beads is active)
6. **Can I initialize beads without permission?** → NO, only if explicitly requested

If you can't answer all of these, re-read this guide.

---

## Related Documentation

- **[bootstrap-project.md Phase 6.5](../processes/bootstrap-project.md#phase-65-optional---initialize-beads-workflow-if-requested)** - How to initialize beads
- **[beads-sticky-attribute.md](beads-sticky-attribute.md)** - What "sticky" means
- **[AGENTS.md](../../AGENTS.md)** - Beads Workflow Integration section
- **[.beads/README.md](../../.beads/README.md)** - Beads labels and workflow

---

**Version:** 1.0
**Last Updated:** 2026-02-15
**Status:** STABLE
**For Agents:** Read at start of EVERY session
