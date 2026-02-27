# Claude Code - Interactive Development IDE Guide

**Status:** ✅ Supported

## 🚨 MANDATORY READING FIRST 🚨

**STOP!** Before reading this guide, you MUST first read the files listed in the "MANDATORY READING" section of [AGENTS.md](../../../AGENTS.md#mandatory-reading-read-first-every-session).

**Quick links to mandatory files:**
1. [Core Workflow](../workflows/logs-first.md) - How to approach all tasks
2. [Definition of Done](../../definition-of-done.md) - Completion criteria
3. [Project Guidelines](../../mandatory.md) - Second Voice specific rules

**Have you read all three?** ✓ Yes, continue. ✗ No, read them now.

---

This guide covers how to use **Claude Code** (the official Anthropic Claude CLI tool) with this project's AGENTS.md workflow.

## ⚠️ BEAD MANIPULATION — READ THIS FIRST ⚠️

**See the canonical guide for all agents:**
[docs/system-prompts/guides/agent-beads-detection.md](../guides/agent-beads-detection.md)

The short version: this project's bead database is **Dolt**, not SQLite. Never create
or write `.beads/beads.db` directly. Always use `bd create` / `bd close`, always follow
with `bd sync && git add .beads/issues.jsonl && git commit`.

---

## Quick Start

```bash
# Install Claude Code
pip install anthropic-claude-code

# Initialize in your project
cd /path/to/your-project
claude-code

# Example: Ask Claude Code to fix tests
claude fix pytest warnings

# Example: Ask for a feature with approval
claude add user authentication system
```

## How Claude Code Discovers Project Instructions

When you start Claude Code in your project:
1. It looks for `CLAUDE.md` in the current directory (or `.claude/CLAUDE.md`)
2. Reads it to understand project-specific instructions
3. Uses CLAUDE.md to reference AGENTS.md workflow

**Your current setup:**
- ✅ `.claude/CLAUDE.md` exists and references AGENTS.md
- ✅ AGENTS.md defines the core workflow
- ✅ Tools are fully integrated

## Tools Available in Claude Code

Claude Code provides these tools, all compatible with AGENTS.md:

### File Operations

**Read** - Read file contents
```python
Read(file_path="/absolute/path/to/file.py")
```
- Used for: Understanding code, checking content
- Supports: Any text file, Python files, config files, documentation
- Requires: Absolute path

**Write** - Create new files
```python
Write(file_path="/absolute/path/to/new_file.py", content="...")
```
- Used for: Creating new files
- Creates: Directories automatically if needed
- Overwrites: Existing files (requires reading first)

**Edit** - Modify existing files
```python
Edit(file_path="/absolute/path/to/file.py",
     old_string="old code",
     new_string="new code")
```
- Used for: Targeted modifications
- Requires: Exact match of old_string (including whitespace)
- Replaces: Only the matched portion

**Glob** - Find files by pattern
```python
Glob(pattern="src/**/*.py", path="/absolute/path/to/dir")
```
- Used for: Finding files matching patterns
- Supports: Glob patterns like `**/*.py`, `test_*.py`
- Returns: List of matching file paths

**Grep** - Search file contents
```python
Grep(pattern="def .*transcribe", glob="src/**/*.py")
```
- Used for: Finding code patterns
- Supports: Regex patterns
- Returns: Matching lines with context

### Task Tracking

**TaskCreate** - Create a new task
```python
TaskCreate(
    subject="Fix authentication bug",
    description="Users cannot login with special characters...",
    activeForm="Fixing authentication bug"
)
```
- Used for: Tracking work items
- Returns: Task ID for later reference
- Enables: Progress tracking

**TaskUpdate** - Update task status
```python
TaskUpdate(
    taskId="task-123",
    status="in_progress",
    description="Updated description if needed"
)
```
- Used for: Marking progress, completing tasks
- Statuses: pending → in_progress → completed
- Enables: Work verification

**TaskList** - See all tasks
```python
TaskList()
```
- Returns: All tasks with status
- Used for: Finding available work
- Shows: Dependencies and blockers

**TaskGet** - Get specific task details
```python
TaskGet(taskId="task-123")
```
- Returns: Full task details
- Shows: What task blocks, what blocks it

### Git Operations

**Bash** - Execute shell commands (including git)
```python
Bash(command="git commit -m 'message'",
     description="Commit changes to git")
```
- Used for: Git operations, running tests, executing commands
- Important: Quote file paths with spaces
- Requirements: Commands must complete in < 2 minutes

### Web & Search

**WebFetch** - Get content from URLs
```python
WebFetch(url="https://example.com/api-docs",
         prompt="Extract API endpoint documentation")
```
- Used for: Reading web pages
- Requires: Public URLs (not authenticated)
- Returns: Content processed with your prompt

**WebSearch** - Search the web
```python
WebSearch(query="latest Python best practices 2026")
```
- Used for: Finding current information
- Requires: Internet connection
- Returns: Search results with links

### MCP Servers

Claude Code can integrate with MCP (Model Context Protocol) servers for extended capabilities:

```python
# MCP tools are accessed like normal tools
# Example: If an MCP server provides database access
```

## Complete Workflow Example

Here's how a typical task flows through Claude Code:

### 1. User Request
```
Add caching to the API responses

Requirements:
- Cache GET requests only
- Invalidate on POST/PUT/DELETE
- Use in-memory cache
- Tests required
```

### 2. Claude Code: Analyze & Declare Intent
```
This is a non-trivial feature. I'll create a Project Plan.
```

### 3. Claude Code: Create Spec File
```python
from datetime import datetime
ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
spec_path = f"dev_notes/specs/{ts}_add-api-caching.md"
# Write spec file with requirements
```

### 4. Claude Code: Create Plan & Request Approval
```python
# Write plan to dev_notes/project_plans/...
# Use ExitPlanMode() to formally request approval
ExitPlanMode()
```

### 5. User: Approve or Provide Feedback
```
Approved. Proceed with the implementation.
```

### 6. Claude Code: Implement Step by Step
```
Step 1: Create cache module
  Bash: Create src/cache.py
  Edit: Update src/api.py to use cache
  Bash: Run tests to verify

Step 2: Add cache invalidation
  Edit: Add invalidation logic
  Write: Create test file for cache
  Bash: Run full test suite

Step 3: Documentation
  Write: Update docs/caching.md
```

### 7. Claude Code: Create Change Documentation
```python
# After each step, create change doc
change_path = f"dev_notes/changes/{ts}_cache-implementation.md"
Write(file_path=change_path, content="What changed and why...")
```

### 8. Verification & Completion
```python
# Run full test suite
Bash(command="pytest --cov=src/")

# Update task status
TaskUpdate(taskId="task-123", status="completed")

# Final commit
Bash(command="git commit -m 'Implement API response caching'")
```

## AGENTS.md Workflow - Claude Code Specifics

Here's exactly how AGENTS.md maps to Claude Code:

### Step A: Analyze & Declare Intent
**Claude Code does:** Read user request, categorize immediately
**Tools used:** None (pure analysis)

### Step B: Create Spec File
**Claude Code does:** Write spec file to dev_notes/specs/
**Tool used:** `Write()`
```python
Write(file_path="dev_notes/specs/YYYY-MM-DD_HH-MM-SS_description.md",
      content="spec content...")
```

### Step C: Create Project Plan
**Claude Code does:** Write plan file to dev_notes/project_plans/
**Tool used:** `Write()`
```python
Write(file_path="dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_description.md",
      content="plan content...")
```

### Step D: AWAIT EXPLICIT APPROVAL ⚠️ CRITICAL
**Claude Code does:** Use ExitPlanMode() and block execution
**Tool used:** `ExitPlanMode()`
```python
ExitPlanMode()  # Formal request for approval

# EXECUTION BLOCKED until user responds with:
# - "yes", "approved", "proceed", "ok", "go ahead"
# - OR asks questions (respond and return to approval)
# - OR gives feedback (update plan, re-request approval)
```

**Important:** Claude Code will NOT proceed without explicit approval. Ambiguous responses like "maybe" or "probably" will be met with a clarification question.

### Step E: Implement & Document
**Claude Code does:** Execute plan, create change docs, commit
**Tools used:** `Bash()`, `Edit()`, `Read()`, `Write()`, `TaskUpdate()`
```python
# For each step in plan:
1. Execute: Bash(command="..."), Edit(...), Write(...)
2. Test: Bash(command="pytest ...")
3. Document: Write() to dev_notes/changes/
4. Verify: Bash(command="git status"), TaskUpdate()
```

## Key Claude Code Capabilities

### Approval Gates (UNIQUE to Claude Code)
Claude Code is the **only** tool with built-in approval gate support. Use this!

```
User: "Implement authentication system"
Claude Code: "I'll create a plan and request approval"
ExitPlanMode() → Blocks execution
User: "Approved"
Claude Code: Proceeds with implementation
```

### Task Tracking (UNIQUE to Claude Code)
Track work items from start to completion:

```
User: "Fix 10 bugs"
Claude Code: Creates TaskCreate() for each bug
During work: TaskUpdate() to "in_progress"
After fix: TaskUpdate() to "completed"
Final: TaskList() shows all completed
```

### Code-Aware Tools
Claude Code understands code deeply:
- Glob finds files by pattern
- Grep understands regex
- Edit handles code structure
- Bash runs tests and git

### Built-in Git Integration
Full git support without extra configuration:
```python
Bash(command="git add -A && git commit -m 'message'")
```

## Common Patterns in Claude Code

### Pattern 1: Simple Fix (No Plan Needed)
```
User: "Fix the typo in README"
Claude Code: "This is trivial, I'll fix it directly"
Edit(...) → Change typo
Bash(command="git commit -m 'Fix typo'")
DONE
```

### Pattern 2: Feature with Approval
```
User: "Add database migrations"
Claude Code: "This is non-trivial, creating plan..."
Write(...) → Spec file
Write(...) → Plan file
ExitPlanMode() → Request approval
[User approves]
Bash(...) → Implement
[Repeat for each step]
Bash(command="git commit...")
DONE
```

### Pattern 3: Debugging & Iteration
```
User: "Tests are failing"
Claude Code: Analyze failures
Bash(command="pytest -v") → Show output
Read(...) → Examine failing test
Bash(command="pytest test_specific.py") → Debug
Edit(...) → Fix code
Bash(command="pytest") → Verify all pass
DONE
```

### Pattern 4: Documentation Update
```
User: "Document the caching system"
Claude Code: "This is docs-only, proceeding..."
Read(...) → Look at existing docs
Write(...) → Create new doc
Read(...) → Verify clarity
Bash(command="git commit -m 'Add caching docs'")
DONE
```

## Error Handling & Recovery

### If a Tool Fails
```
Tool fails → Claude Code explains why
You decide: Fix or try different approach
Claude Code: Can retry or use different tool
```

### If Tests Fail
```
Bash(command="pytest") → Tests fail
Claude Code: Shows error output
You clarify: Expected behavior?
Claude Code: Fixes code and retries
```

### If Approval is Ambiguous
```
You say: "Maybe we should do this?"
Claude Code: "I want to confirm: should I proceed? Yes or No?"
You respond: "Yes" or "No"
Claude Code: Proceeds or stops accordingly
```

## Tips & Best Practices for Claude Code

### 1. Be Specific in Requests
```
❌ Bad: "Fix the bug"
✅ Good: "Fix the authentication bug where users
   can't login with special characters"
```

### 2. Use Task Tracking for Complex Work
```
TaskCreate(subject="Add auth system")
TaskCreate(subject="Add password validation")
TaskCreate(subject="Add session tokens")
# Now Claude Code can track and manage all three
```

### 3. Request Explicit Approval for Plans
```
ExitPlanMode() is a formal approval request.
Use it for anything that's more than a few lines.
```

### 4. Let Claude Code Manage Git
```
Claude Code can commit. You can let it:
Bash(command="git add -A && git commit -m 'message'")
Or you can do it manually:
Bash(command="git status") # Just show status
```

### 5. Use Glob & Grep Instead of Shell
```
❌ Less good: Bash(command="find . -name '*.py'")
✅ Better: Glob(pattern="**/*.py")
```

### 6. Read Files Before Editing
```
❌ Risky: Edit(...) without Read() first
✅ Safe: Read(...) then Edit(...) with exact match
```

### 7. Always Verify Test Changes
```
After tests: Bash(command="pytest")
After code: Bash(command="pytest --cov")
After docs: Read(...) to verify clarity
```

## Limitations & Constraints

### Token Limits
- Claude Code uses Claude Haiku 4.5
- ~200k token context window
- Large codebases may need focused exploration

### Time Limits
- Bash commands: Max 2 minutes timeout
- Long operations: May need to be broken into steps
- Remote operations: Consider bandwidth/latency

### Permissions
- Cannot skip git hooks without user request
- Cannot force push to main/master
- Cannot run destructive commands (`rm`, `reset --hard`) without explicit approval

### What Claude Code Cannot Do
- ❌ Run interactive commands (requires user input)
- ❌ Access external URLs (except via WebFetch for public URLs)
- ❌ Modify system files outside project
- ❌ Install system packages (can install Python packages though)

## Connecting to AGENTS.md & Other Docs

Claude Code uses a **hierarchy of documents**:

```
.claude/CLAUDE.md (entry point for this tool)
↓
AGENTS.md (core workflow - all projects)
```

**For any task:**
1. Look at your request
2. Follow AGENTS.md Step A-E
3. Use Claude Code tools as shown above
4. Reference `prompt-patterns.md` for request phrasing

## Getting Help

**Questions about:**
- **AGENTS.md workflow?** → Read AGENTS.md + `workflow-mapping.md`
- **Tool capabilities?** → Read `tools-capabilities.md`
- **How to phrase requests?** → Read `prompt-patterns.md`
- **Claude Code specifics?** → You're reading it now!

## Examples

### Example 1: Adding Tests
```
User: "Add unit tests for the config module"

Claude Code follows AGENTS.md:
1. Analyze: Tests are a coding task, plan may be needed
2. Check codebase: Read config.py
3. Create plan: "Test strategy for config module"
4. Request approval: ExitPlanMode()
5. On approval: Create test_config.py
6. Document: dev_notes/changes/... file
7. Commit: git commit -m "Add config tests"
```

### Example 2: Quick Bug Fix
```
User: "Fix the typo in docs/test-guide.md"

Claude Code analyzes:
1. Analyze: This is trivial (typo fix)
2. Execute immediately: Edit(...) with old/new strings
3. Commit: git commit -m "Fix typo in docs/test-guide.md"
4. Done: No plan or approval needed
```

### Example 3: Complex Feature
```
User: "Add webhook support for external services"

Claude Code:
1. Analyze: Non-trivial feature
2. Create spec: dev_notes/specs/...
3. Create plan: dev_notes/project_plans/...
4. Request approval: ExitPlanMode()
5. Steps: [Implementation with testing at each step]
6. Documentation: dev_notes/changes/...
7. Final commit: git commit with full summary
```

## Troubleshooting

**Problem:** "File not found"
**Solution:** Always use absolute paths. Bash `pwd` to confirm location.

**Problem:** "Exact match required for Edit"
**Solution:** Read the file first, copy exact old_string including whitespace.

**Problem:** "Tests still failing after fix"
**Solution:** Bash(command="pytest -v") to see detailed output, then analyze and fix.

**Problem:** "Want to cancel a task"
**Solution:** Tell Claude Code: "Let's not proceed with this." It will stop.

---

## Quick Reference Card

| Need | Tool | Example |
|------|------|---------|
| Read code | Read() | `Read(file_path="/path/to/file.py")` |
| Create file | Write() | `Write(file_path="...", content="...")` |
| Edit code | Edit() | `Edit(file_path="...", old_string="...", new_string="...")` |
| Find files | Glob() | `Glob(pattern="**/*.py")` |
| Search code | Grep() | `Grep(pattern="def test_", glob="tests/**/*.py")` |
| Run command | Bash() | `Bash(command="pytest", description="Run tests")` |
| Create task | TaskCreate() | `TaskCreate(subject="...", description="...")` |
| Update task | TaskUpdate() | `TaskUpdate(taskId="...", status="completed")` |
| List tasks | TaskList() | `TaskList()` |
| Request approval | ExitPlanMode() | `ExitPlanMode()` |
| Search web | WebSearch() | `WebSearch(query="...")` |
| Fetch URL | WebFetch() | `WebFetch(url="...", prompt="...")` |

---

Start using Claude Code with confidence! Follow AGENTS.md, use this guide for Claude Code specifics, and reference `prompt-patterns.md` for phrasing your requests.
