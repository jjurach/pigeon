# Close Project Process

**Purpose:** Ensure all work is properly completed, verified, and documented before ending an agentic session.

**Status:** Documented

---

## Overview

The close-project process is the final step before ending an agentic session. It ensures:

1. **Definition of Done criteria are met** - All quality standards satisfied
2. **Tests pass** - Code is verified to work correctly
3. **Changes are committed** - Work is saved to git with proper attribution
4. **Change documentation exists** - Audit trail is complete
5. **Human intervention triggered when needed** - Agent knows when to stop and ask for help

This process applies the "landing the plan" checklist to ensure nothing is forgotten before the agent exits.

**Note:** If the user requests to "close a task", interpret this as "close the project" (or "close the plan") and apply this process.

---

## When to Apply This Process

Apply the close-project process:

- ✅ At the end of any development session involving code changes
- ✅ After completing a project plan implementation
- ✅ After making substantial documentation changes
- ✅ When the user indicates they want to wrap up the session
- ✅ Before committing the final changes

**Do NOT apply if:**
- ❌ Work is incomplete or blocked
- ❌ Tests are failing for non-trivial reasons (abort and ask for human help instead)
- ❌ You're in the middle of implementing a multi-step plan
- ❌ Awaiting user approval or feedback

---

## The Close-Project Checklist

### Phase 1: Verify Definition of Done

**Goal:** Ensure all applicable Definition of Done criteria are met.

#### 1.1 Check Universal DoD Criteria

Verify against `docs/system-prompts/principles/definition-of-done.md`:

- [ ] Code follows project patterns and style
- [ ] No hardcoded credentials or secrets
- [ ] Plan status updated to `Completed` (if applicable)
- [ ] Configuration files updated (if config keys added)
- [ ] Documentation updated (if features/APIs changed)

#### 1.2 Check Language-Specific DoD (Python)

Verify against `docs/system-prompts/languages/python/definition-of-done.md`:

- [ ] All new imports in `requirements.txt` AND `pyproject.toml`
- [ ] Type hints present for function signatures
- [ ] Docstrings follow project conventions
- [ ] No circular imports
- [ ] Temporary test scripts deleted (content saved to change docs)

#### 1.3 Check Project-Specific DoD

Verify against `docs/definition-of-done.md`:

- [ ] `config.example.json` updated (if applicable)
- [ ] Reference formatting correct (hyperlinks or backticks, no plain text)
- [ ] File naming conventions followed

**If ANY DoD criterion is not met:** Fix it before proceeding to Phase 2.

---

### Phase 2: Run Tests

**Goal:** Verify that all tests pass before committing.

#### 2.1 Run Test Suite

```bash
# For Python projects
pytest tests/ -v

# Or project-specific test command
```

#### 2.2 Optimization for Documentation-Only Changes

**Optimization Rule:**
- For **documentation-only changes**, do not execute regression tests or apply other measures of `definition-of-done.md` not specific to documentation changes.
- Alternatively, execute regression tests **only for source which our session changed**.
- If work involved both code and documentation, standard regression testing (Phase 2.1) applies.

#### 2.3 Evaluate Test Results

**DECISION POINT:**

**✅ All tests pass** → Proceed to Phase 3

**❌ Tests fail for trivial reasons** (typos, missing imports you can fix immediately):
- Fix the issues
- Re-run tests
- Verify they now pass
- Proceed to Phase 3

**❌ Tests fail for non-trivial reasons** (logic errors, unexpected behavior, mysterious failures):
- **ABORT THE CLOSE-PROJECT PROCESS**
- Do NOT proceed to commit
- Report the failures to the user with full test output
- Explain what's failing and why it needs human intervention
- **Examples of non-trivial failures:**
  - Logic errors in implementation
  - Unexpected test behavior that requires debugging
  - Environment issues (missing dependencies, system config)
  - Integration test failures with external services
  - Flaky tests that pass sometimes and fail other times

**Why abort on non-trivial test failures?**
- The source tree may have unexpected junk not intended for commit
- The implementation may have introduced bugs
- Tests may be revealing design flaws
- Human needs to debug and understand the root cause
- Committing broken code violates Definition of Done

**Example abort message:**

```
ABORT: Close-Project Process Halted

Tests are failing for non-trivial reasons. Human intervention required.

Test Failures:
========================= FAILURES =========================
test_processor.py::test_audio_processing - AssertionError: expected 16000, got 44100
test_config.py::test_provider_validation - KeyError: 'openrouter_api_key'

Reason for Abort:
- test_audio_processing: Sample rate logic may be incorrect
- test_provider_validation: Configuration schema may have changed

Recommendation:
1. Review test failures above
2. Debug the root cause
3. Fix implementation or tests as needed
4. Re-run tests until they pass
5. Then resume close-project process

I have NOT committed any changes. The source tree is in the following state:
[show git status]
```

---

### Phase 3: Document Changes

**Goal:** Create or verify change documentation exists.

#### 3.1 Check for Change Documentation

**If you followed a Project Plan:**
- [ ] Change documentation exists in `dev_notes/changes/`
- [ ] Filename follows `YYYY-MM-DD_HH-MM-SS_description.md` format
- [ ] Status is set to `Completed`
- [ ] Related Project Plan referenced
- [ ] Verification section includes test output
- [ ] All files modified/created are listed

**If this was ad-hoc work (no project plan):**
- [ ] Change documentation exists in `dev_notes/changes/`
- [ ] Status is set to `ad-hoc`
- [ ] Related Project Plan is `N/A`
- [ ] Full details of what changed and why included
- [ ] Verification section included

**If change documentation is missing:**
- Create it now before committing
- Use timestamp from when work started (if known) or current time
- Follow template from `docs/system-prompts/templates/structure.md`

#### 3.2 Verify Change Documentation Quality

Check that the change documentation includes:

- [ ] **Summary:** Clear 1-2 sentence description of what was accomplished
- [ ] **Changes Made:** Detailed breakdown by component/module
- [ ] **Files Modified/Created:** Complete list with descriptions
- [ ] **Verification:** Exact commands used and output showing success
- [ ] **Test Results:** Actual test output (not just "tests pass")
- [ ] **Known Issues:** Any caveats, limitations, or future work noted
- [ ] **Integration with DoD:** Explicit checklist against Definition of Done

#### 3.3 Archive Inbox Requests

**Goal:** Ensure handled inbox requests are properly archived.

- [ ] Identify any `dev_notes/inbox/` files addressed by this session
- [ ] Move them to `dev_notes/inbox-archive/`
- [ ] Rename with timestamp: `YYYY-MM-DD_HH-MM-SS_original-name.md`
- [ ] Verify `dev_notes/inbox/` is clean (or only contains unrelated items)
- [ ] *Note: This serves as a backstop if the logs-first workflow didn't already archive them.*

---

### Phase 4: Commit Changes

**Goal:** Save all work to git with proper attribution.

#### 4.1 Review Git Status

```bash
git status
```

**Check for unexpected files:**
- [ ] No temp files (`tmp-*`, `*.tmp`, `.pyc`, `__pycache__`)
- [ ] No credentials or secrets (`.env`, `credentials.json`)
- [ ] No large binaries or data files (unless intended)
- [ ] No editor artifacts (`.swp`, `.DS_Store`)

**If unexpected files exist:**
- Review with user before committing
- Consider adding to `.gitignore`
- Clean up temp files

#### 4.2 Stage Changes

**For code changes with change documentation:**
```bash
# Stage both code and change documentation together
git add src/
git add tests/
git add requirements.txt
git add dev_notes/changes/YYYY-MM-DD_HH-MM-SS_description.md
git add dev_notes/inbox/ dev_notes/inbox-archive/  # If inbox items were archived
```

**For documentation-only changes:**
```bash
# Stage docs and change documentation together
git add docs/
git add dev_notes/changes/YYYY-MM-DD_HH-MM-SS_description.md
git add dev_notes/inbox/ dev_notes/inbox-archive/  # If inbox items were archived
```

**For project plan updates:**
```bash
# Stage completed plan status update
git add dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_description.md
git add dev_notes/inbox/ dev_notes/inbox-archive/  # If inbox items were archived
```

#### 4.3 Create Commit

Follow the project's commit message conventions:

```bash
git commit -m "$(cat <<'EOF'
<type>: <short description>

<longer description if needed>

Changes:
- Bullet point of what changed
- Another change
- etc.

<verification note if relevant>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

**Commit message types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Build/tooling changes

**Example commit:**
```bash
git commit -m "$(cat <<'EOF'
feat: add OAuth2 authentication support

Implement OAuth2 authentication flow for external API access.

Changes:
- Add OAuth2Client class in src/auth/oauth.py
- Add token refresh mechanism
- Update config.example.json with OAuth2 keys
- Add 15 new tests for auth flow

All tests passing (pytest: 109 passed)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

#### 4.4 Verify Commit

```bash
git log -1 --stat
```

Check:
- [ ] Commit message is clear and descriptive
- [ ] All intended files are included
- [ ] Change documentation is committed with code changes
- [ ] Co-author attribution present

#### 4.5 Close Bead (If Beads Enabled)

**If this work was dispatched via beads:**

1. **Identify bead ID**
   - Check if you received bead ID in prompt: "implement bd-a1b2"
   - Or check change documentation for bead reference: `Bead: bd-a1b2`

2. **Close the bead**
   ```bash
   bd close <bead-id>
   ```

3. **Verify closure**
   ```bash
   bd show <bead-id>
   # Should show status: closed
   ```

**If not using beads:**
- Skip this step

**Example:**
```bash
# If bead ID is bd-a1b2.1
bd close bd-a1b2.1

# Verify
bd show bd-a1b2.1
# Output should include: status: closed
```

---

### Phase 5: Final Status Report

**Goal:** Provide clear summary of what was accomplished.

#### 5.1 Report to User

Provide a concise summary:

```
✅ Project Complete

Summary:
[1-2 sentence description of what was accomplished]

Tests:
✅ All [X] tests passing

Changes Committed:
✅ Commit [hash]: [commit message]

Change Documentation:
✅ dev_notes/changes/YYYY-MM-DD_HH-MM-SS_description.md

Files Modified:
- [list key files changed]

Next Steps:
[Any recommended follow-up work or future considerations]
```

#### 5.2 Clean Up

- [ ] Remove any temporary files created during the session
- [ ] Close any background processes
- [ ] Clear any cached data (if applicable)

---

## Abort Scenarios

### Scenario 1: Tests Fail (Non-Trivial)

**Trigger:** Tests fail with logic errors, unexpected behavior, or mysterious failures.

**Action:**
1. Do NOT proceed with commit
2. Report full test output to user
3. Explain why human intervention is needed
4. List what's failing and potential causes
5. Show current git status
6. **Wait for user to fix issues**

**DO NOT:**
- ❌ Commit broken code
- ❌ Comment out failing tests
- ❌ Attempt complex debugging without approval
- ❌ Guess at fixes for logic errors

### Scenario 2: Unexpected Files in Source Tree

**Trigger:** `git status` shows unexpected files (credentials, large binaries, temp files not cleaned up).

**Action:**
1. Do NOT proceed with commit
2. List unexpected files
3. Ask user how to handle them:
   - Should they be committed?
   - Should they be added to `.gitignore`?
   - Should they be deleted?
4. **Wait for user guidance**

### Scenario 3: Missing Change Documentation

**Trigger:** Code changes exist but no change documentation file present.

**Action:**
1. Pause at Phase 3
2. Create change documentation before committing
3. Include all required sections (Summary, Changes, Verification, etc.)
4. Commit change documentation with code changes

### Scenario 4: Definition of Done Not Met

**Trigger:** DoD checklist has unchecked items.

**Action:**
1. Pause at Phase 1
2. Report which DoD criteria are not met
3. Fix the issues:
   - Add missing type hints
   - Update config.example.json
   - Add missing docstrings
   - etc.
4. Re-verify DoD checklist
5. Proceed once all criteria met

---

## Common Patterns

### Pattern 1: Standard Code Change

```
1. Verify DoD → Pass
2. Run tests → Pass
3. Check change docs → Exists and complete
4. Commit → Code + change docs together
5. Report → Success summary
```

### Pattern 2: Documentation-Only Change (Ad-Hoc)

```
1. Verify DoD → Pass (doc-specific criteria)
2. Run tests → Skip (no code changes)
3. Create ad-hoc change docs → Mark as Status: ad-hoc
4. Commit → Docs + change docs together
5. Report → Success summary
```

### Pattern 3: Tests Failing

```
1. Verify DoD → Pass
2. Run tests → FAIL (non-trivial)
3. ABORT → Report failures, wait for human
   [User fixes issues]
   [Resume process]
4. Run tests → Pass
5. Continue from Phase 3
```

### Pattern 4: Multi-File Refactoring

```
1. Verify DoD → Check all files
2. Run tests → Pass (critical)
3. Check change docs → Verify all modified files listed
4. Review git status → Check for unexpected side effects
5. Commit → All changes + change docs
6. Report → Comprehensive file list in summary
```

---

## Integration with Other Processes

### With Project Plan Workflow

When closing a project that followed a project plan:

1. **Update plan status to `Completed`**
2. **Reference plan in change documentation**
3. **Verify all plan phases were completed**
4. **Note any deviations in change docs**

### With Definition of Done

The close-project process enforces the Definition of Done:

- Phase 1 explicitly checks DoD criteria
- Phase 2 verifies tests (DoD requirement)
- Phase 3 ensures change documentation (DoD requirement)
- Phase 4 commits everything properly (DoD requirement)

### With Document Integrity Scan

For documentation changes:

- Consider running `python3 docs/system-prompts/docscan.py` before committing
- Verify no broken links were introduced
- Check reference formatting is correct

---

## Examples

### Example 1: Successful Code Change Close

```
Starting close-project process...

Phase 1: Definition of Done
✅ Code follows project patterns
✅ Type hints present
✅ No secrets hardcoded
✅ requirements.txt updated
✅ config.example.json updated

Phase 2: Tests
Running: pytest tests/ -v
========================= 94 passed in 2.34s =========================
✅ All tests passing

Phase 3: Change Documentation
✅ Found: dev_notes/changes/2026-01-29_14-22-00_add-oauth-auth.md
✅ Status: Completed
✅ Related Plan: dev_notes/project_plans/2026-01-29_13-45-00_oauth-auth.md
✅ Verification section complete

Phase 4: Commit
Staged:
  - src/auth/oauth.py (new)
  - tests/test_oauth.py (new)
  - requirements.txt (modified)
  - dev_notes/changes/2026-01-29_14-22-00_add-oauth-auth.md (new)

✅ Committed: feat: add OAuth2 authentication support [a1b2c3d]

Phase 5: Summary
✅ Project Complete

Summary: Implemented OAuth2 authentication with token refresh mechanism

Tests: ✅ 94 passed
Commit: a1b2c3d
Change Docs: dev_notes/changes/2026-01-29_14-22-00_add-oauth-auth.md

Files Added:
  - src/auth/oauth.py
  - tests/test_oauth.py

Files Modified:
  - requirements.txt (added oauthlib==3.2.2)
```

### Example 2: Abort on Test Failure

```
Starting close-project process...

Phase 1: Definition of Done
✅ All DoD criteria met

Phase 2: Tests
Running: pytest tests/ -v

========================= FAILURES =========================
test_processor.py::test_audio_processing FAILED
test_config.py::test_load_config FAILED
========================= 2 failed, 92 passed =========================

❌ Tests failing for non-trivial reasons

ABORT: Close-Project Process Halted

Test Failures:
1. test_audio_processing - AssertionError: Sample rate mismatch
   Expected: 16000 Hz
   Got: 44100 Hz
   Location: src/processor.py:145

2. test_load_config - KeyError: 'openrouter_api_key'
   Location: src/config.py:67

Reason for Abort:
These failures indicate logic errors that require debugging:
- Sample rate conversion logic may be broken
- Configuration schema may have changed unexpectedly

I have NOT committed any changes.

Current git status:
  modified: src/processor.py
  modified: src/config.py
  modified: tests/test_processor.py

Recommendation:
1. Debug the sample rate conversion in src/processor.py:145
2. Check if config schema changed in src/config.py:67
3. Fix the issues
4. Re-run: pytest tests/ -v
5. Once tests pass, resume close-project process

Waiting for your guidance on how to proceed.
```

### Example 3: Documentation Change (Ad-Hoc)

```
Starting close-project process...

Phase 1: Definition of Done
✅ File naming: lowercase-kebab.md
✅ Reference formatting correct
✅ No broken links

Phase 2: Tests
Skipped (documentation-only change)

Phase 3: Change Documentation
Creating ad-hoc change documentation...
✅ Created: dev_notes/changes/2026-01-29_15-30-00_tips/claude-code.md
✅ Status: ad-hoc
✅ Related Plan: N/A

Phase 4: Commit
Staged:
  - docs/system-prompts/tips/claude-code.md (new)
  - dev_notes/changes/2026-01-29_15-30-00_tips/claude-code.md (new)

✅ Committed: docs: add Claude Code workflow optimization guide [fb0c396]

Phase 5: Summary
✅ Project Complete

Summary: Created comprehensive workflow optimization guide for Claude Code users

Commit: fb0c396
Change Docs: dev_notes/changes/2026-01-29_15-30-00_tips/claude-code.md (ad-hoc)

Files Created:
  - docs/system-prompts/tips/claude-code.md (478 lines)
```

---

## Troubleshooting

### "Tests are passing locally but I see warnings"

**Decision:** Warnings are generally okay to proceed unless they indicate serious issues.

**Check:**
- Are they deprecation warnings? (Usually safe to proceed)
- Are they performance warnings? (Document in Known Issues)
- Are they security warnings? (Stop and investigate)

### "Change documentation exists but was created earlier in the session"

**Decision:** Verify it's still accurate and complete.

**Check:**
- Does it reflect all changes made?
- Is verification section up to date?
- Are all files listed?
- If not, update it before committing

### "Git status shows files I didn't explicitly modify"

**Decision:** This is common (lock files, generated files).

**Check:**
- Are they expected side effects? (package-lock.json, pyproject.toml)
- Are they test artifacts? (coverage reports, pytest cache)
- Are they config auto-updates? (IDE settings)

### "I made changes across multiple sessions"

**Decision:** Close-project should be run at the end of the final session.

**Pattern:**
- Session 1: Implement Phase 1, create partial change docs
- Session 2: Implement Phase 2, update change docs
- Session 3: Finish implementation, finalize change docs, run close-project

### "How do I resume a previous session?"

**Use case:** Tests failed, session ended, need to continue work later.

**Built-in Claude Code resumption:**

```bash
# Resume the most recent session
claude --continue
claude -c

# Resume a named session (best practice: name your sessions with /rename)
claude --resume auth-refactor
claude -r auth-refactor

# Interactive session picker (browse and select)
claude --resume
claude -r

# Continue with alias and apply close-project
claude-dev --continue 'fix the test failures and apply close-project process'
```

**Best practice:**
1. **Name your sessions** during work: Use `/rename session-name` inside Claude
2. **Resume by name** later: `claude --resume session-name`
3. Claude will have full context from the previous conversation
4. Continue work and apply close-project when ready

**Example workflow:**

```bash
# During session 1 (tests fail, need to stop)
> /rename oauth-implementation
# Session ends

# Later, resume and complete
claude --resume oauth-implementation
# Claude has full context from previous session
# Fix issues, then:
> apply close-project process
```

**Alternative: Manual context reconstruction** (if session was lost):

```bash
# Read change documentation to understand what was being worked on
claude-dev 'read dev_notes/changes/2026-01-29_14-22-00_add-oauth-auth.md and continue the work'
```

---

## See Also

- [Definition of Done - Universal](../principles/definition-of-done.md)
- [Definition of Done - Python](../languages/python/definition-of-done.md)
- [Definition of Done - Project Specific](../../definition-of-done.md)
- [Change Documentation Template](../templates/structure.md#3-change-documentation-template)
- [Core Workflow](../workflows/core.md)
- [Logs-First Workflow](../workflows/logs-first.md)

---

Last Updated: 2026-01-29