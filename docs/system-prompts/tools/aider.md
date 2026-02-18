# Aider - Interactive Development IDE Guide

**Status:** ✅ Supported

## 🚨 MANDATORY READING FIRST 🚨

**STOP!** Before reading this guide, you MUST first read the files listed in the "MANDATORY READING" section of [AGENTS.md](../../../AGENTS.md#mandatory-reading-read-first-every-session).

**Quick links to mandatory files:**
1. [Core Workflow](../workflows/logs-first.md) - How to approach all tasks
2. [Definition of Done](../../definition-of-done.md) - Completion criteria
3. [Project Guidelines](../../mandatory.md) - Second Voice specific rules

**Have you read all three?** ✓ Yes, continue. ✗ No, read them now.

---

This guide covers how to use **Aider** (collaborative AI coding tool) with this project's AGENTS.md workflow.

## Quick Start

```bash
# Install Aider
pip install aider-chat

# Start Aider in your project
cd /path/to/your-project
aider

# Example: Ask Aider to fix tests
> fix the pytest warnings

# Example: Ask for a feature
> add user authentication

# Exit Aider
> /exit
```

## How Aider Discovers Project Instructions

Aider reads `AGENTS.md` and any other files specified in `.aider.conf.yml`. We use this to ensure Aider has full context from our core workflow and hidden entry point.

**Discovery order:**
1. `./AGENTS.md` (Project Root)
2. `.aider.md` (Hidden entry point, loaded via config)
3. `.aider.conf.yml` (Configuration)

## Configuration

Ensure your `.aider.conf.yml` includes the following in the `read` list:

```yaml
# Project Context
read:
  - AGENTS.md
  - .aider.md
  - docs/definition-of-done.md
  - `docs/workflow-mapping.md`
```

### Context Loading
By adding files to the `read` list in config, Aider automatically loads your project's core instructions on startup. This ensures it always knows about `AGENTS.md`.

## Using Aider with AGENTS.md

### Workflow for a Feature

```
1. You: Start Aider
   aider

2. You: Request feature with context
   "I want to add caching to the API.
    Caching should:
    - Cache GET requests only
    - Invalidate on POST/PUT/DELETE
    - Use in-memory cache
    - Have tests

    Should I proceed?"

3. Aider: Confirms understanding
   "Yes, I'll implement this step by step."

4. Step 1 - Create cache module:
   You: "Step 1: Create src/cache.py with the cache implementation"
   Aider: Creates file, shows content
   You: Review, say "OK" or ask for changes

5. Step 2 - Integrate with API:
   You: "Step 2: Update src/api.py to use the cache"
   Aider: Shows diff
   You: "The invalidation logic looks wrong, can you fix..."
   Aider: Fixes it, shows new diff
   You: "OK, apply this"

6. Step 3 - Add tests:
   You: "Step 3: Create comprehensive tests in tests/test_cache.py"
   Aider: Creates test file
   Aider: Can run tests
   You: Review test output, ask for more tests if needed

7. Documentation:
   You: "Create change documentation in dev_notes/changes/"
   Aider: Creates the documentation

8. Verify:
   You: "Run the full test suite"
   Aider: Runs pytest
   You: "Great! Let's commit this"
   Aider: (Already auto-committed, but shows summary)

9. You: Exit Aider
   /exit
```

## Aider Commands

```bash
# Inside Aider
/help           # Show all commands
/exit           # Exit Aider
/add file.py    # Add file to context
/remove file.py # Remove file from context
/git diff       # Show git diff
/git add        # Git add (before manual commit)
/git reset      # Git reset (undo changes)
/run command    # Run shell command
```

## Handling Approval without ExitPlanMode

Since Aider has no built-in approval, use **conversational approval**:

### Pattern: Clear Plan First
```
You: "Before I ask you to implement, let me show you the plan:

Step 1: Create cache.py with Cache class
Step 2: Add get(), set(), invalidate() methods
Step 3: Integrate with /api/users endpoint
Step 4: Add tests

Does this sound right?"

Aider: "Yes, this approach makes sense."

You: "Great, let's proceed. Step 1: Create cache.py"

Aider: Creates the file
```

### Pattern: Step-by-Step Confirmation
```
You: "Next step: Integrate cache with API routes.
     Should I proceed?"

Aider: "Yes, I'm ready"

You: "Update src/api.py to use the cache"
     [Aider shows diff]

You: "Looks good, apply these changes"
     [Aider applies and auto-commits]

You: "Next step: Create tests"
```

### Pattern: Undo and Retry
```
You: "Actually, I don't like this approach"
     git undo

Aider: Undoes the commit

You: "Let me try a different approach..."
     [New direction]

Aider: Implements the new approach
```

## When to Use Each Approval Pattern

| Situation | Pattern | Aider Response |
|-----------|---------|---|
| Simple fix (typo) | Just ask | Fixes directly |
| New feature | Show plan first | Confirms understanding |
| Complex change | Step-by-step | Confirms each step |
| Uncertain | Ask for advice | Gives suggestions |
| Mistake | Undo + retry | Implements new approach |

## Key Practices with Aider

### 1. Suggest, Don't Command
```
❌ "Add error handling"
✅ "Let's add error handling for network timeouts.
   Should I proceed?"
```

### 2. Review Changes as Diffs
```
Aider shows diff → You review → You say "OK" or "Change..."
Don't skip this step! Diffs are your approval mechanism.
```

### 3. Use Git Undo if Needed
```
You disagree with a change?
git undo
git log --oneline  # See what was undone
Aider continues from previous commit
```

### 4. Create Specs and Plans as Files
```
You: "Create a spec file for this feature in dev_notes/specs/"
     [Aider creates it]

You: "Now create a plan in dev_notes/project_plans/"
     [Aider creates it]

This maintains AGENTS.md compliance.
```

### 5. Document Changes Manually
```
You: "Create a change documentation in dev_notes/changes/
     describing what we just implemented"

Aider: Creates the documentation file
```

### 6. Use Conversation as Approval Log
```
Since Aider doesn't have approval gates,
the conversation history IS the approval log.

Helpful: Save conversation or take screenshots.
```

## Limitations Unique to Aider

### No Built-in Approval Gates
- Changes apply immediately
- You must review diffs before pressing Enter
- Conversation is your approval mechanism
- Difficult for large teams (no formal approval)

### No Task Tracking
- No TaskCreate/TaskUpdate
- Must track progress manually
- Create tracking in dev_notes/ if needed

### Git Auto-Commit Limitations
- Commit messages are auto-generated (may be generic)
- Hard to have meaningful commit history
- Can be good or bad depending on preference

### No MCP Server Support
- Cannot extend capabilities via MCP
- Limited to built-in functionality

### Model Dependent
- Capabilities depend on which model you use
- Web search depends on model capabilities
- Context window depends on model

## Tips for Success with Aider

### Tip 1: Be Conversational
```
Aider responds better to natural language:
✅ "Can you add validation to the login form?"
❌ "Add validation"
```

### Tip 2: Provide Context
```
✅ "The User model in src/models/user.py needs a new field
   for tracking login attempts. It should..."
❌ "Add login attempts field"
```

### Tip 3: Ask for Explanation
```
You: "Why did you choose this approach?"
Aider: Explains reasoning
You: "Makes sense" or "Actually, let's try..."
```

### Tip 4: Use Files for Large Instructions
```
You: "Read this design document in docs/feature-design.md
     and implement according to this spec"

Aider: Reads file, implements based on design
```

### Tip 5: Check Diffs Carefully
```
Before accepting changes:
- Review the diff
- Check indentation and style
- Verify logic
- Ask for changes if needed
```

## Connecting to AGENTS.md

Aider workflow should still follow AGENTS.md principles:

```
Step A: Analyze ✅ Aider does this
Step B: Spec file ✅ Aider creates (you request)
Step C: Plan file ✅ Aider creates (you request)
Step D: Approval ⚠️ Conversational instead of ExitPlanMode
Step E: Implement ✅ Aider does this step-by-step
```

**Documentation hierarchy:**
```
CLAUDE.md or README
  ↓
AGENTS.md (core workflow)
  ↓
`workflow-mapping.md` (how it maps to Aider)
  ↓
This document (Aider specifics)
  ↓
prompt-patterns.md (general request patterns)
```

## Examples

### Example 1: Add Tests
```
You: "Let's add comprehensive unit tests for src/auth.py

The tests should cover:
- Successful login
- Failed login with wrong password
- Missing required fields
- Valid token generation

Should I proceed?"

Aider: "Yes, I'll create comprehensive tests in tests/test_auth.py"

You: [Aider shows test file]
     "Looks good, apply these changes"

You: [Review test output]
     "Perfect, tests pass"
```

### Example 2: Quick Bug Fix
```
You: "There's a bug in src/config.py line 45 where
     the default value is wrong. It should be 'local'
     not 'remote'. Can you fix it?"

Aider: "I'll fix that"
       [Shows diff]

You: "Good, apply it"
```

### Example 3: Refactoring with Questions
```
You: "Can we refactor the AudioRecorder class for clarity?
     It's getting long and has too many responsibilities."

Aider: "I can break it into smaller classes. Here's my idea:
       - AudioRecorder (main interface)
       - AmplitudeCalculator (amplitude logic)
       - AudioFileManager (file I/O)

       Does this sound good?"

You: "Yes, let's try it"

Aider: [Implements refactoring]
       [Shows diffs]

You: "Review diffs"
     "Looks good, apply"
```

## Troubleshooting

**Problem:** Aider made changes I don't want
**Solution:** `git undo` to revert, then ask Aider differently

**Problem:** Aider doesn't understand my request
**Solution:** Be more specific, provide examples, reference files

**Problem:** Changes look wrong in diff
**Solution:** Ask Aider to revise before accepting (before pressing Enter)

**Problem:** Forgot to request spec/plan file
**Solution:** Use `/run` to create it manually, then ask Aider to help

## Quick Reference

| Need | How to do it | Example |
|------|---|---|
| Create file | Ask directly | "Create src/cache.py with..." |
| Edit code | Describe change | "Add error handling to..." |
| See diff | Aider shows it | After each change, review |
| Run tests | Ask | "Run pytest" |
| Undo change | git undo | git undo |
| Create spec | Ask | "Create dev_notes/specs/..." |
| Create plan | Ask | "Create dev_notes/project_plans/..." |
| Get approval | Ask before step | "Should I proceed?" |
| Document | Ask | "Create change documentation in dev_notes/changes/" |
| Exit | Command | /exit |

---

## Summary: Claude Code vs Aider

**Use Claude Code if:**
- You need explicit approval gates
- You want task tracking
- You need MCP server integration
- You want built-in web search
- Formal approval processes matter

**Use Aider if:**
- You prefer collaborative, conversational approval
- Code awareness is critical
- You like auto-commits
- You want tight git integration
- Working solo or in small teams

**Both can follow AGENTS.md** with appropriate adaptations shown in `workflow-mapping.md`.
