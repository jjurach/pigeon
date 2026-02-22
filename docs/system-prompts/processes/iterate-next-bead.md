# iterate-next-bead.md — IMPROVED VERSION

**Purpose:** Guide any agent through the process of claiming, executing, and completing the next ready bead in the hatchery project, with built-in safeguards for stalled processes and multi-terminal coordination.

**This document is the interim bead execution workflow** until hatchery daemon is implemented.

---

## Quick Reference: What to Do

When you see "apply iterate-next-bead.md process":

1. **Claim** the bead → `bd update {id} --status=in_progress`
2. **Assess** if work is needed → Check if code already exists
3. **Implement** the gap (if any) → Write code, run tests
4. **Verify** criteria → Tests pass, acceptance criteria met
5. **Close** and commit → `bd update {id} --status closed`

---

## Terminology Note

⚠️ **"Phases" Used in Two Contexts:**

- **Workflow Phase** = Step in THIS process (1-8)
- **Epic Phase** = Implementation phase from project plan (e.g., "Phase 2-4")

Example:
- Bead description: "E1-B Phase 2-4" ← Epic phases
- This process: "Phase 6: Implement the Gap" ← Workflow phase

---

## Bead Execution Decision Tree

```
START: Bead is ready (bd ready shows it)
  ↓
[Phase 1-3] Assess environment and find next bead
  ↓
[Phase 4] Claim the bead
  ├─ bd update {id} --status=in_progress
  └─ bd show {id} to get full requirements
  ↓
[Phase 5] Determine execution type
  ├─ Is this INTERACTIVE? (needs human input/decision)
  │  └─ YES → HALT, wait for human
  └─ Is this NON-INTERACTIVE?
     └─ YES → Continue to Phase 5.4
  ↓
[Phase 5.4 NEW] Check what work actually needs doing
  ├─ All acceptance criteria already met?
  │  └─ YES → Skip to Phase 7 (Close immediately)
  └─ Some/all criteria not yet met?
     └─ YES → Continue to Phase 6 (Implement gap)
  ↓
[Phase 6] Implement and test
  ├─ 6.1: Understand what needs to be done
  ├─ 6.2: Write code, run tests, iterate
  ├─ 6.3: Handle errors (fix or document)
  └─ 6.4: Verify acceptance criteria met
  ↓
[Phase 7] Close the bead and commit
  ├─ bd update {id} --status closed
  ├─ bd sync (commit bead changes)
  ├─ git add / git commit / git push (commit your code)
  └─ Document in change notes
  ↓
[Phase 8] Loop or halt
  ├─ bd ready (check for more work)
  └─ If ready beads exist → Go back to Phase 3
     Else → Halt (no more work)
```

---

## Phase 1: Environmental Assessment

### Step 1.1: Inspect Running Agents

Before claiming any bead, understand the current process landscape:

```bash
python3 docs/system-prompts/planning-running.py --detailed
```

**What you're looking for:**
- Are there other agents running in different terminals?
- Which projects are they working on?
- How long have they been running?
- Are they making progress or stalled?

**Store this information** for later decision-making.

---

## Phase 2: Health Check — Detect & Recover Stalled Beads

### Step 2.1: List All In-Progress Beads

```bash
bd list --status=in_progress
```

### Step 2.2: For Each In-Progress Bead, Check Process Health

For each bead in `in_progress` status:

1. **Get bead metadata:**
   ```bash
   bd show {bead_id}
   ```
   Look for: `grabbed_by_pid`, `grabbed_at`, `grabbed_by_agent`

2. **Check if the process is still alive:**
   ```bash
   ps -p {grabbed_by_pid}
   ```

3. **Decision tree:**

   ```
   IF grabbed_by_pid not set:
     → Use age-based detection (see 2.3)

   ELSE IF ps -p {pid} returns success:
     → Process is alive ✓
     → Skip this bead (another agent is working on it)

   ELSE IF process is dead:
     → Check age (2.3 logic below)
   ```

### Step 2.3: Age-Based Stall Detection (30-minute timeout)

For each dead or unknown-PID in-progress bead:

```
IF grabbed_at is NOT set:
  → Age is unknown, skip recovery (bead is old, no metadata)

ELSE IF age < 30 minutes:
  → Recently grabbed (might be legitimately working)
  → Skip recovery

ELSE IF age >= 30 minutes AND process is dead:
  → STALLED BEAD DETECTED
  → Run Step 2.4
```

### Step 2.4: Recover Stalled Beads

For each stalled bead:

1. **Log the recovery:**
   ```bash
   bd update {bead_id} --notes="Recovered from stalled process {grabbed_by_pid} \
     (age: {age_minutes}min, last_activity: {timestamp})"
   ```

2. **Reset the bead:**
   ```bash
   bd update {bead_id} --status=open
   ```

3. **Print to user:**
   ```
   ✓ Recovered {bead_id} from stalled PID {grabbed_by_pid} (grabbed {age_minutes}min ago)
   ```

### Step 2.5: Summary of Recovered Beads

After processing all in-progress beads, print summary:

```
=== HEALTH CHECK SUMMARY ===
✓ Recovered: 2 beads from stalled processes
→ {bead_id_1} (stalled 2h15m)
→ {bead_id_2} (stalled 1h30m)

⏳ Still Working: 1 bead
→ {bead_id_3} (PID 40604, 18 min)

Ready to proceed to next bead ✓
```

---

## Phase 3: Find Ready Work

### Step 3.1: List Ready Beads

```bash
bd ready
```

### Step 3.2: Handle "All Blocked" Scenario

If `bd ready` returns empty:

1. **Print blockage analysis:**
   ```bash
   bd blocked
   ```
   Shows which beads are blocking others.

2. **Identify root blockers:**
   ```
   Example output:
   {bead_id_1} (in_progress, 45 min)
     ← blocks: {bead_id_2}, {bead_id_3}
   {bead_id_4} (in_progress, 2h30m)
     ← blocks: {bead_id_5}
   ```

3. **Decision:**
   - If root blockers are old in-progress beads → they might be stalled
     - Offer: "Should I attempt recovery? Y/n"
   - If root blockers are recent → they're being worked on
     - Print: "Cannot proceed, waiting for {bead_id}"
     - Halt (no further action)

4. **If user allows recovery:**
   - Go back to Phase 2, force recovery on root blockers
   - Re-run Phase 3

---

## Phase 4: Claim and Inspect the Next Bead

### Step 4.1: Select First Ready Bead

```bash
# Grab the first ready bead (from bd ready output, typically first in order)
NEXT_BEAD={first_ready_bead_id}
```

### Step 4.2: Multi-Terminal Safety Check

Before claiming, verify no other agent has it:

```bash
# Get bead details
bd show {NEXT_BEAD}

# Check grabbed_by_pid
IF grabbed_by_pid is set AND NOT empty:
  → Another process has this bead!
  → Check: ps -p {grabbed_by_pid}
  → IF alive: DO NOT CLAIM (return to Phase 3, find next)
  → IF dead: Go to Phase 2 recovery first
```

### Step 4.3: Claim the Bead

```bash
bd update {NEXT_BEAD} \
  --status=in_progress \
  --notes="Claimed by {agent_type} PID {my_pid}"
```

### Step 4.4: Fetch Bead Details

```bash
bd show {NEXT_BEAD}
```

Review:
- Title and description (what is the work?)
- Dependencies (what must be done first?)
- Related files/documentation
- Any previous notes

---

## Phase 5: Determine Execution Type

### Step 5.1: Is This Bead Interactive (Needs Human Input)?

Check if the bead requires human intervention:

```
IF bead type is "research" OR "decision":
  → INTERACTIVE (human needs to answer questions or make decisions)

ELSE IF description contains keywords:
  ["clarify", "clarifying questions", "approval", "human gate", "research"]
  → INTERACTIVE

ELSE IF bead is "{project}: RESEARCH - ...":
  → INTERACTIVE

ELSE:
  → NON-INTERACTIVE (can be executed autonomously)
```

### Step 5.2: Interactive Bead Path

If INTERACTIVE:

```
Print: "This bead requires human input ({bead_id})"
       "{title}"

Action: HALT execution
        Skip this bead for now
        Return to Phase 3, find next ready bead

Later: When human provides answers:
  - Answers get added to bead notes
  - Bead status set back to open
  - iterate-next-bead runs again, bead is ready
```

### Step 5.3: Non-Interactive Bead Path

If NON-INTERACTIVE:

```
Proceed to Phase 5.4 (Pre-Implementation Completeness Check)
```

---

## Phase 5.4: Pre-Implementation Completeness Check (NEW)

**⭐ KEY ADDITION:** Before assuming work needs doing, verify what's already complete.

### Step 5.4.1: Understand Acceptance Criteria

Read the bead description carefully:

```bash
# Display bead details again
bd show {NEXT_BEAD}
```

Answer:
- What exactly must this bead accomplish?
- What files must be created/modified/deleted?
- What tests must pass?
- What integration points must work?

### Step 5.4.2: Check Current State

**For each file/component mentioned in the bead:**

```bash
# Check if file exists
ls -la {file_path}

# Check if directory is empty
find {directory} -type f | head -10

# Check git status (has it changed recently?)
git log -1 --oneline {file_path}
```

### Step 5.4.3: Run Existing Tests (if any)

```bash
# From the project directory
cd {project_root}

# Run tests for this component
pytest tests/test_{component}.py -v

# Or run all tests
pytest -v
```

**Note:** Tests may pass even if work seems incomplete - that's OK, indicates work is done!

### Step 5.4.4: Compare Current State to Acceptance Criteria

Create a mental checklist:

```
BEAD: {bead_id} - {title}

ACCEPTANCE CRITERIA (from bead description):
□ Criterion 1: {specific requirement}
□ Criterion 2: {specific requirement}
□ Criterion 3: {specific requirement}
...

CURRENT STATE:
✓ Criterion 1: ALREADY MET (test_xyz.py passes, code exists)
✓ Criterion 2: ALREADY MET (function works as expected)
✗ Criterion 3: NOT MET (missing feature)
? Criterion 4: UNCLEAR (need to test)

WORK NEEDED (GAP):
- Implement criterion 3 (add feature X)
- Verify criterion 4 (test edge case)
```

### Step 5.4.5: Make Decision

```
IF all acceptance criteria are already met:
  → Go to Phase 7 (Close the Bead immediately)
  → Do NOT re-implement existing working code

ELSE IF some criteria are met, some are not:
  → Go to Phase 6.2 (Implement ONLY the gap)
  → Document what was already there

ELSE IF all criteria need work:
  → Go to Phase 6.1 (Full implementation)

ELSE IF criteria are unclear:
  → Ask human for clarification
  → Mark bead with question in notes
  → Proceed to next ready bead
```

**Example decisions:**

| Scenario | Action |
|----------|--------|
| "config.py exists, tests pass, validates correctly" | Close immediately |
| "config.py done, discovery.py partially done" | Implement only discovery.py |
| "Neither config.py nor discovery.py exist" | Full implementation |
| "Code exists but tests fail" | Debug and fix |
| "Requirements unclear" | Ask human |

---

## Phase 6: Implement the Gap

### Step 6.1: Understand the Implementation Scope

Based on Phase 5.4, you now know exactly what needs doing.

**Ask yourself:**

- What code needs to be ADDED (new files/functions)?
- What code needs to be CHANGED (modified existing)?
- What code needs to be DELETED (cleanup)?
- What tests need to be ADDED or FIXED?
- What documentation needs updating?

**Reference the related epic planning document** (if it exists):

```bash
# Find the epic plan
find dev_notes/project_plans -name "*epic*" -type f | grep {project}

# Read the relevant section
cat dev_notes/project_plans/{timestamp}_epic.md | grep -A 20 "Phase {number}"
```

### Step 6.2: Implement the Work

Implement according to the gap identified in Phase 5.4:

```bash
# Typical workflow:
1. Create/edit code files
2. Run tests locally
3. Iterate until tests pass
4. Commit changes to git
5. Run full test suite again
6. Verify no regressions
```

**Monitoring (for health checks in future sessions):**
- Git commits show activity
- File modifications trigger file system changes
- planning-running.py will detect active file handles

### Step 6.3: Handle Execution Errors

If something doesn't work:

```
1. Attempt to fix the root cause
   → Debug the issue
   → Review error messages
   → Check related code

2. If fixable:
   → Fix it
   → Re-run tests
   → Continue to 6.4

3. If not fixable:
   → Update bead with error notes:
     bd update {NEXT_BEAD} --notes="Failed: {error_description}"
   → Reset status:
     bd update {NEXT_BEAD} --status=open
   → Report to user/log for review
   → Halt (wait for human intervention)
```

### Step 6.4: Verify Acceptance Criteria

Before proceeding to close, verify ALL criteria are met:

```
FINAL ACCEPTANCE CHECKLIST:

□ Code written matches bead description
□ All acceptance criteria from bead are met
□ All tests pass (unit + integration)
□ No regressions in related code
□ Git commits have clear messages
□ No secrets or sensitive data committed

DEFINITION OF DONE (from close-project.md):

Code Quality:
□ Type hints on public functions
□ Docstrings on public classes/methods
□ Code follows project style guide
□ No obvious bugs or leftover TODOs

Testing:
□ Unit tests exist for new code
□ All tests pass locally
□ Critical paths covered by tests
□ Edge cases handled

Documentation:
□ Change documentation created (dev_notes/changes/{timestamp}_*.md)
□ Linked bead ID to changes
□ Architecture impacts documented
□ No breaking changes without migration plan

Git & Commit:
□ Commits pushed to repo
□ Commit messages are descriptive
□ Co-authored properly
```

**If any checkbox is unchecked:** Go back to 6.2 and fix it.
**If all checkboxes are checked:** Proceed to Phase 7.

---

## Phase 7: Close the Bead & Sync

### Step 7.1: Update Bead with Summary

```bash
bd update {NEXT_BEAD} --status closed \
  --append-notes="Implementation complete. All acceptance criteria met. {brief_summary_of_work}"
```

Example:
```bash
bd update {bead_id} --status closed \
  --append-notes="Config class with validation, Discovery with enumeration, Monitor with polling. 35 tests passing."
```

### Step 7.2: Sync Beads Database

```bash
bd sync
```

This commits bead changes to git.

### Step 7.3: Create Change Documentation

Create a change documentation file:

```bash
timestamp=$(date +%Y-%m-%d_%H-%M-%S)
cat > dev_notes/changes/${timestamp}_description.md << 'EOF'
# Change Documentation: {Bead Title}

**Bead:** {bead_id}
**Date:** {date}
**Agent:** {your_name}

## Summary
{1-3 sentence summary of work}

## What Was Already Done
{List components that existed before}

## What You Added/Changed
{List new code and modifications}

## Verification
{List tests run, acceptance criteria verified}

## Files Modified
- {file_path}
- {file_path}

## Test Results
{Paste test output showing all passing}

## Lessons Learned
{Any insights or process improvements?}
EOF

git add dev_notes/changes/${timestamp}_description.md
```

### Step 7.4: Commit Code Changes

```bash
# Verify what's staged
git status

# Stage relevant files (may be already staged from earlier commits)
git add {relevant_files}

# Commit with bead reference
git commit -m "$(cat <<'EOF'
Close {BEAD_ID}: {Brief description of work}

{Slightly longer description of changes}

Test Results: {num} tests passing
Acceptance Criteria: All met

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

### Step 7.5: Final Sync

```bash
bd sync
```

Commit bead closure to git (if bead database is git-tracked).

### Step 7.6: Push to Remote (if available)

```bash
git push
```

**Note:** May fail in sandbox environments - that's OK.

---

## Phase 8: Loop or Halt

### Step 8.1: Check for More Work

```bash
bd ready
```

### Step 8.2: Decision

```
IF ready beads exist:
  → Continue to Phase 3 (find next bead)
  → You can work on multiple beads in one session!

ELSE:
  → Print: "No more ready beads. All hatchery work blocked or complete."
  → Halt (wait for human to unblock or create new work)
```

---

## Failure Recovery

### Scenario: Agent Crashes Mid-Execution

When an agent resumes after crash:

1. **Run Phase 1** (inspect agents)
2. **Run Phase 2** (health check)
   - Your stalled bead will be detected (grabbed >30min)
   - Recovery will reset it to `open`
3. **Continue from Phase 3** (find ready work)

Your bead is automatically rescued and available for retry.

---

## Scenario: Human Needs to Interrupt

If a user needs to interrupt a running agent:

1. **Find the bead being worked on:**
   ```bash
   bd list --status=in_progress
   ```

2. **Decide action:**
   - Let it finish? (leave as in_progress)
   - Resume later? (leave as in_progress, will be recovered after 30min)
   - Cancel? (reset to open, next agent will retry)
   ```bash
   bd update {bead_id} --status=open --notes="Cancelled by user, needs retry"
   ```

---

## Implementation Notes for Agents

### If You're Claude Code

When you see "apply iterate-next-bead.md process":

```
1. Run: python3 docs/system-prompts/planning-running.py --detailed
2. Run: bd ready
3. If stuck: bd blocked (understand why)
4. If clear: follow this document from Phase 1 onwards
5. Claim bead with: bd update {id} --status=in_progress
6. Execute work (with Phase 5.4 completeness check)
7. Close with: bd update {id} --status closed --append-notes "..."
8. Create change documentation
9. Run: bd sync && git add/commit/push
```

### If You're Another Agent (Gemini, etc.)

Same workflow, different process. The key is:
- Check health first (Phase 2)
- Claim safely (Phase 4)
- Determine interactivity (Phase 5)
- Check completeness (Phase 5.4) ← NEW and IMPORTANT
- Implement only the gap (Phase 6)
- Close and sync (Phase 7)

---

## Key Safeguards

✓ **No duplicate work:** Refuse to grab beads owned by live processes
✓ **Automatic recovery:** Stalled beads reset after 30 minutes
✓ **Interactive awareness:** Skip beads needing human input
✓ **Multi-terminal safe:** PID-based coordination prevents collisions
✓ **Self-healing:** Health checks on every iteration
✓ **Completeness check:** NEW - Verify work is needed before implementing
✓ **Early exit:** Close immediately if work already done

---

## Reference

- **planning-running.py:** `docs/system-prompts/planning-running.py`
- **Beads CLI:** `bd --help`
- **Project Plans:** `dev_notes/project_plans/`
- **Definition of Done:** `docs/system-prompts/processes/close-project.md`
- **Git workflow:** `AGENTS.md`
