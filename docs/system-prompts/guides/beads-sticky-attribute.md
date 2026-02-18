# Beads: Sticky Attribute Guide

**Purpose:** Clarify when beads workflow is active and how agents should respond to its presence

**Version:** 1.0
**Last Updated:** 2026-02-15

---

## What is a "Sticky Attribute"?

A sticky attribute is a project configuration that, once enabled, persists across future work sessions and impacts all subsequent agent work:

- **Initial Decision:** User explicitly requests the feature in their prompt
- **Persistence:** Feature remains active after initial setup
- **Future Sessions:** All subsequent agents see the feature as "already configured"
- **Implications:** Future project plans should assume the feature exists and use it

**Example:** If a user says "set up beads for this project" during bootstrap, then beads is sticky. Any agent working on the project in future sessions should assume beads is available and use it.

---

## Beads as a Sticky Attribute

### Initial State: No Beads

**Condition:** Project has no `.beads/` directory

**Agent Behavior:**
- Don't create beads unless explicitly requested
- Use logs-only workflow (dev_notes/changes/ documentation)
- If user mentions beads in prompt → execute Phase 6.5 of bootstrap-project

**Example Prompt (User):**
> "Help me set up this project with beads task tracking"

**Agent Action:**
- Execute Phase 6.5 of bootstrap-project.md
- Create `.beads/` directory and configuration
- Beads becomes STICKY

### Active State: Beads Initialized

**Condition:** Project has `.beads/` directory with `.beads/config.yaml`

**Agent Behavior:**
- ALWAYS check for `.beads/` directory at session start
- Assume beads workflow is active (no user prompt needed)
- Use `bd` commands in project plans and workflows
- Create beads for tasks, use `bd ready`, `bd list`, `bd close`
- Beads remains STICKY for all future sessions

**Example Workflow:**
```bash
# Check if beads is active
if [ -d ".beads" ]; then
  echo "Beads workflow detected"
  bd list --status=ready  # Find work
else
  echo "Logs-only workflow"
fi
```

---

## Decision Tree for Agents

### At Session Start

```
Does the project have a .beads/ directory?
├─ YES → Beads is sticky
│   └─ Use beads workflow automatically
│       ├─ Check bd ready for work
│       ├─ Use bd create for new tasks
│       ├─ Use bd close for completed tasks
│       └─ Run bd sync before git push
│
└─ NO → Logs-only workflow
    └─ Check user's current prompt
        ├─ User mentions "beads"? → Initialize beads (Phase 6.5)
        │   └─ Beads becomes sticky going forward
        │
        └─ User doesn't mention beads? → Continue logs-only
            └─ Keep beads off unless explicitly requested
```

### During Project Planning

**If beads is sticky (`.beads/` exists):**
- Include beads initialization in project plan if plan touches workflow/task management
- Reference `.beads/README.md` for label definitions
- Plan tasks using beads terminology (create issues, track status)
- Example: "Create sv-1 for feature X, use bd create/close"

**If beads is NOT active:**
- Use dev_notes/changes/ for documentation
- No need to mention beads in plans
- Continue logs-first workflow

### Before Session Completion

**Always check sticky state:**

```bash
# At session end
if [ -d ".beads" ]; then
  echo "Syncing beads..."
  bd sync
else
  echo "Logs-only workflow"
fi

git push  # Always push
```

---

## Key Rules

### Rule 1: Don't Surprise with Beads

❌ **Wrong:** User never mentioned beads, but you initialize it anyway
```
User: "Help me add authentication to the app"
Agent: (initializes beads without asking)
```

✅ **Right:** Wait for explicit request or detect existing .beads/ directory
```
User: "Help me add authentication to the app"
Agent: (checks for .beads/, finds nothing, uses logs-only workflow)

---Later---
User: "Set up beads for task tracking"
Agent: (initializes beads, now sticky)
```

### Rule 2: Beads Becomes Automatic After Init

❌ **Wrong:** Initialize beads, then ignore it in future sessions
```
Session 1: Initialize beads
Session 2: Forget to use bd commands, fall back to logs-only
```

✅ **Right:** Once sticky, use it everywhere
```
Session 1: Initialize beads (user requested)
Session 2: Check for .beads/, find it, use bd commands automatically
Session 3: Continue using beads without prompting
```

### Rule 3: Clearly Communicate Stickiness

When initializing beads, clarify that it's sticky:

```markdown
## Beads Initialization Complete

Beads is now active for this project. **This is a sticky attribute:**

- Future work sessions will automatically detect beads
- Subsequent agents should use `bd ready`, `bd create`, `bd close`
- Beads commands required for task tracking going forward
- Always run `bd sync` before pushing to remote
```

---

## Detection: How to Know if Beads is Sticky

```bash
# Method 1: Check for .beads directory
[ -d ".beads" ] && echo "Beads is active" || echo "No beads"

# Method 2: Check for config
[ -f ".beads/config.yaml" ] && echo "Beads initialized" || echo "Not initialized"

# Method 3: Try bd command
bd list >/dev/null 2>&1 && echo "Beads is working" || echo "Beads not available"
```

---

## Examples

### Example 1: New Project, No Beads

**Session 1:**
- User: "Bootstrap this project"
- Agent: Runs bootstrap-project.md phases 1-6
- Result: No beads, logs-only workflow
- `.beads/` directory: Does not exist

**Session 2:**
- User: "Add the new feature"
- Agent: Checks for .beads/, finds nothing
- Plans use dev_notes/changes/ documentation
- `.beads/` directory: Still doesn't exist

### Example 2: New Project, With Beads

**Session 1:**
- User: "Bootstrap this project with beads workflow"
- Agent: Runs bootstrap-project.md phases 1-7 INCLUDING Phase 6.5
- Result: Beads is initialized and sticky
- `.beads/` directory: EXISTS (sticky)

**Session 2:**
- User: "Add the new feature"
- Agent: Checks for .beads/, FINDS IT
- Plans automatically use `bd create`, `bd close`, `bd list`
- Creates beads for tasks
- `.beads/` directory: Still exists (sticky persists)

**Session 3:**
- User: "Fix the bug in feature X"
- Agent: Checks for .beads/, FINDS IT
- Automatically uses beads workflow
- No need for user to mention beads again
- `.beads/` directory: Still exists (sticky persists)

### Example 3: Detect and Use Existing Beads

```markdown
# Project Analysis

Detected: `.beads/` directory exists
Status: Beads workflow is ACTIVE (sticky attribute)

**Implication:** This project uses beads for task tracking.

## Project Plan: Add Analytics

### Beads Integration
- Create beads for each feature: `bd create --title="..."`
- Check ready work: `bd ready`
- Update status: `bd update <id> --status=in_progress`
- Complete tasks: `bd close <id>`

### Session Completion
- Sync beads: `bd sync`
- Commit: `git commit ...`
- Push: `git push`
```

---

## For Beads-Aware Agents

### Initialization Check

```python
import os
import json

def is_beads_sticky(project_root: str) -> bool:
    """Check if beads is the sticky attribute."""
    beads_dir = os.path.join(project_root, ".beads")
    config_file = os.path.join(beads_dir, "config.yaml")
    return os.path.isdir(beads_dir) and os.path.isfile(config_file)

# Usage
if is_beads_sticky("."):
    print("Beads workflow is active - use bd commands")
    # Include bd commands in plans
else:
    print("Logs-only workflow - use dev_notes/changes/")
    # Don't use beads
```

### Agent Prompt Guidance

If you're an agent working on a beads-enabled project:

1. **Start each session:** Check for `.beads/` directory
2. **If found:** Assume beads is sticky and use it automatically
3. **If not found:** Use logs-only workflow unless user requests beads
4. **When planning:** Include beads commands if sticky
5. **At session end:** Run `bd sync` before pushing (if beads is sticky)

---

## Troubleshooting

### Problem: "User didn't mention beads, should I initialize it?"

**Answer:** NO. Only initialize if:
- User explicitly requests beads, OR
- You're in bootstrap-project.md Phase 6.5 because user requested it

Otherwise, leave it off. Let the user decide when to enable beads.

### Problem: "I initialized beads, but next session ignored it"

**Answer:** This is the stickiness rule failing. Subsequent agents should:
1. Check for `.beads/` at session start
2. If found, automatically use beads
3. Never fall back to logs-only if beads exists

If this happens, file an issue: agent didn't respect sticky attribute.

### Problem: "Should I remove beads if user doesn't want it anymore?"

**Answer:** Don't remove beads without explicit user request:
- "Remove beads" or "Disable beads" → Delete `.beads/` directory
- Otherwise, beads stays (it's sticky)

User must explicitly request removal.

---

## Related Documentation

- **[bootstrap-project.md](../processes/bootstrap-project.md)** - Phase 6.5 beads initialization
- **[.beads/README.md](../../.beads/README.md)** - Beads labels and configuration
- **[AGENTS.md](../../AGENTS.md)** - Beads Workflow Integration section

---

**Version:** 1.0
**Last Updated:** 2026-02-15
**Status:** FINAL
