# Workflow Improvement Analysis Process

**Purpose:** Analyze change documentation to identify friction points and generate improvement plans for system prompts and tooling.

**Status:** Documented

**When to Run:**
- At the end of every Epic/Milestone.
- As a scheduled "Continuous Improvement" task.

---

## 1. Discovery Phase
Scan all `dev_notes/changes/` files created since the last analysis (or for the current Epic).
- Search for the "Workflow & Tooling Feedback" section.
- Look for phrases like "Error", "Failed", "Workaround", "Confusing", "Wait time", "Lock file".
- Identify patterns: Are multiple agents hitting the same issue?

## 2. Categorization
Group identified issues into categories:
- **System Prompts:** Ambiguous instructions, missing steps, outdated templates.
- **Beads CLI:** Bugs, missing features, performance issues, lock contention.
- **Project Structure:** File organization, naming conventions.
- **Environment:** Dependencies, setup scripts, permissions.

## 3. Analysis & Solutioning
For each category, propose a solution:
- **Quick Fix:** Can be applied immediately (e.g., update a doc).
- **Tooling Fix:** Requires code changes to tools (e.g., `beads` update).
- **Process Change:** Requires updating workflows (e.g., `AGENTS.md`).

## 4. Output: Improvement Plan
Create a new Project Plan (`dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_workflow-improvements.md`) that outlines:
- **Problem Statement:** Summary of issues found.
- **Proposed Solutions:** Specific actions to take.
- **Tasks:** Breakdown of work (e.g., "Update planning-init.py", "Revise plan-and-dispatch.md").

## 5. Execution (New Epic)
- Create a new Milestone/Epic bead for this improvement plan.
- Create implementation beads for each task.
- Dispatch for execution.

---

**Example Output Plan:**

```markdown
# Project Plan: Workflow Improvements (Cycle 1)

## Overview
Address recurring issues identified in the Mobile App Migration epic.

## Issues Identified
1. **Beads Lock Contention:** Agents frequently hit lock timeouts on `bd update`.
2. **Ambiguous Specs:** Spec template lacks "Non-Goals" section leading to scope creep.

## Tasks
### 1. Update Beads Config
- Increase default lock timeout in `.beads/config`.

### 2. Revise Spec Template
- Add "Non-Goals" section to `docs/system-prompts/templates/structure.md`.
```
