# Claude Code: Workflow Optimization Tips

This document provides practical tips and configurations for optimizing your workflow when using Claude Code with the Agent Kernel system-prompts infrastructure.

---

## Quick Reference Shell Aliases

### Recommended Aliases

Add these to your `~/.bashrc` or `~/.zshrc` for faster Claude Code invocation:

```bash
# System-prompts processes (skip permissions, use sonnet)
alias claude-sys='claude --model sonnet --dangerously-skip-permissions'

# Quick exploration (skip permissions, use haiku for speed)
alias claude-quick='claude --model haiku --dangerously-skip-permissions'

# Full dev work (skip permissions, use sonnet)
alias claude-dev='claude --model sonnet --dangerously-skip-permissions'

# Deep reasoning (skip permissions, use opus)
alias claude-think='claude --model opus --dangerously-skip-permissions'
```

### Usage Examples

```bash
# Run system-prompts processes
claude-sys 'apply document-integrity-scan process and fix problems'

# Quick exploration and searches
claude-quick 'find all error handling code'
claude-quick 'list all TODOs in the codebase'

# Development tasks
claude-dev 'implement the authentication feature'
claude-dev 'fix the bug in the login flow'

# Complex architectural decisions
claude-think 'review the system architecture and suggest improvements'
claude-think 'design the caching strategy for this application'

# Session resumption (works with all aliases)
claude --continue                    # Resume most recent session
claude -c                            # Short form
claude --resume oauth-impl           # Resume named session
claude -r oauth-impl                 # Short form

# Aliases work with resumption flags
claude-dev --continue 'fix tests and close project'
claude-quick --continue 'summarize what we were working on'
claude-sys -c 'apply document-integrity-scan'
claude-think --resume complex-refactor 'continue architectural review'
```

---

## Model Selection Guide

Choose the right model for the task to optimize cost and speed:

| Model | Use Case | Speed | Cost | When to Use |
|-------|----------|-------|------|-------------|
| **Haiku** | Quick reads, searches, simple tasks | Fastest | Lowest | Exploration, file searches, simple Q&A |
| **Sonnet** | Most development work | Balanced | Medium | Feature implementation, bug fixes, refactoring |
| **Opus** | Complex reasoning | Slower | Highest | Architecture design, security reviews, complex debugging |

### Examples by Task Type

**Use Haiku (`claude-quick`) for:**
- "Find all files that import X"
- "What does this function do?"
- "List all API endpoints"
- "Show me the error handling code"

**Use Sonnet (`claude-dev`, `claude-sys`) for:**
- "Implement feature X"
- "Fix this bug"
- "Refactor this module"
- "Apply document-integrity-scan process"
- "Add tests for this component"

**Use Opus (`claude-think`) for:**
- "Design the authentication system architecture"
- "Review this PR for security vulnerabilities"
- "Suggest improvements to our caching strategy"
- "Debug this complex race condition"

---

## Permission Management

### The `--dangerously-skip-permissions` Flag

**What it does:** Skips all permission approval prompts, allowing Claude to execute tools without asking.

**When to use:**
- ✅ Running documented system-prompts processes
- ✅ Development work in a safe branch
- ✅ Trusted, repeatable operations
- ✅ Exploration and read-only tasks

**When NOT to use:**
- ❌ Running on production systems
- ❌ When unfamiliar with what Claude will do
- ❌ With destructive operations (unless intentional)
- ❌ On the main/master branch without review

**Safety considerations:**
- Claude can execute ANY bash command
- Claude can edit/delete ANY file in the working directory
- Claude can commit and push to git
- Use in development environments you control
- Review git diffs before pushing

### Alternative: Selective Tool Approval

If you want more control, use `--allowedTools`:

```bash
# Allow only specific bash commands
claude --allowedTools 'Bash(python*)' 'Bash(git status)' 'Read' 'Grep' \
  'apply document-integrity-scan process'

# Read-only exploration
claude --allowedTools 'Read' 'Glob' 'Grep' \
  'analyze the codebase structure'
```

---

## Working with System-Prompts Processes

### Process Discovery

When you mention a process by name, Claude should automatically check `docs/system-prompts/processes/` for the specification.

**Shorthand invocations:**

```bash
# Long form
claude-sys 'apply the document-integrity-scan.md process'

# Short form (recommended)
claude-sys 'apply document-integrity-scan process'

# Even shorter
claude-sys 'run docscan'
claude-sys 'scan docs'
```

### Available Processes

| Process | Command | Description |
|---------|---------|-------------|
| **document-integrity-scan** | `claude-sys 'apply document-integrity-scan'` | Validate documentation correctness |
| **bootstrap-project** | `claude-sys 'apply bootstrap-project'` | Initialize/update Agent Kernel |
| **close-project** | `claude-dev 'apply close-project process'` | Properly complete and land work before ending session |

### Common Process Commands

```bash
# Run document integrity scan
claude-sys 'apply document-integrity-scan process and fix any issues'

# Run docscan directly
claude-sys 'run python3 docs/system-prompts/docscan.py and fix issues'

# Bootstrap with workflow analysis
claude-sys 'apply bootstrap-project with --analyze-workflow flag'

# Check current bootstrap state
claude-sys 'what is the current bootstrap state?'

# Close project (wrap up work properly)
claude-dev 'apply close-project process'
claude-dev 'close this project and commit changes'
```

---

## Workflow Optimization Patterns

### Pattern 1: Exploration → Implementation

```bash
# Step 1: Quick exploration with haiku
claude-quick 'find all authentication-related code'

# Step 2: Detailed implementation with sonnet
claude-dev 'add OAuth2 support to the authentication module'
```

### Pattern 2: Research → Deep Analysis

```bash
# Step 1: Quick search
claude-quick 'what are our current caching mechanisms?'

# Step 2: Deep architectural review
claude-think 'design a comprehensive caching strategy for the entire system'
```

### Pattern 3: Validate → Fix → Verify

```bash
# Step 1: Run validation
claude-sys 'apply document-integrity-scan process'

# Step 2: Fix reported issues
claude-dev 'fix the broken links reported in the scan'

# Step 3: Re-validate
claude-sys 'apply document-integrity-scan process'
```

### Pattern 4: Development → Close Project

**Complete development cycle with proper project closure:**

```bash
# Step 1: Implement the feature
claude-dev 'implement user authentication with OAuth2'

# Step 2: Run tests and verify
claude-dev 'run tests and verify all pass'

# Step 3: Close the project properly
claude-dev 'apply close-project process'
```

**What close-project does:**
1. ✅ Verifies Definition of Done criteria
2. ✅ Runs tests (aborts if non-trivial failures)
3. ✅ Checks/creates change documentation
4. ✅ Commits changes with proper attribution
5. ✅ Reports final status

**When to use close-project:**
- ✅ At end of development sessions
- ✅ After completing a feature
- ✅ Before switching contexts
- ✅ When ready to commit work

**When close-project will abort:**
- ❌ Tests fail for non-trivial reasons (logic errors)
- ❌ Unexpected files in source tree
- ❌ Definition of Done criteria not met

### Pattern 5: Resuming Previous Sessions

**Claude Code has built-in session resumption** - each session is stored and can be continued later with full context:

```bash
# Resume the most recent session
claude --continue
claude -c

# Resume a named session (best practice)
claude --resume auth-refactor
claude -r auth-refactor

# Interactive session picker (browse all sessions)
claude --resume
claude -r

# Resume with alias and continue work
claude-dev --continue 'fix the test failures and apply close-project process'
```

**Best practice workflow:**

```bash
# Session 1: Start work, name it, tests fail
claude-dev 'implement OAuth authentication'
> /rename oauth-implementation
# Session ends (tests failed, need to stop)

# Session 2: Resume by name with full context
claude --resume oauth-implementation
# Claude remembers everything from session 1
# Fix issues, then:
> apply close-project process
```

**Why this works:**
- Claude Code stores full conversation history per session
- Sessions are local to the project directory
- Resuming restores complete context automatically
- No need to manually read files or reconstruct state

**Session management tips:**

```bash
# Always name important sessions (inside Claude)
> /rename feature-name

# Resume by name is easier than browsing
claude -r feature-name

# Fork a session to try different approaches
claude --resume feature-name --fork-session
```

**Combining aliases with resumption flags:**

```bash
# Continue with sonnet (dev work)
claude-dev --continue
claude-dev -c 'fix the tests and apply close-project'

# Continue with haiku (quick check)
claude-quick --continue 'what were we working on?'
claude-quick -c 'summarize recent changes'

# Resume named sessions with specific models
claude-dev --resume oauth-impl 'continue OAuth implementation'
claude-think --resume arch-review 'continue architectural analysis'
claude-sys --resume docscan-fixes 'finish fixing documentation'

# Short forms work too
claude-dev -r oauth-impl 'fix remaining issues'
claude-quick -c 'quick status check'
```

**Alternative: Manual context reconstruction** (if session is lost/unavailable):

```bash
# Read change documentation to understand previous work
claude-dev 'read dev_notes/changes/2026-01-29_14-22-00_add-oauth-auth.md and continue implementing OAuth'
```

---

## Project-Specific Settings

### For This Project (`second_voice`)

You can configure project-specific settings in `.claude/settings.json`:

```json
{
  "model": "sonnet",
  "appendSystemPrompt": "When user mentions a 'process', check docs/system-prompts/processes/ first. When user mentions 'workflow', check docs/system-prompts/workflows/ first."
}
```

This automatically applies when running Claude Code in this project directory.

### Settings Hierarchy

Claude Code uses a scope-based hierarchy:

1. **Command line flags** (highest priority)
2. **Local settings** (`.claude/settings.local.json` - gitignored, personal)
3. **Project settings** (`.claude/settings.json` - shared with team)
4. **User settings** (`~/.claude/settings.json` - applies to all projects)

**Tip:** Use project settings for shared team preferences, local settings for personal overrides.

---

## Command-Line Tips

### Inline Prompts

```bash
# Use quotes for prompts with spaces
claude-dev 'implement user authentication'

# Use single quotes to avoid shell variable expansion
claude-dev 'show all $variables in the code'

# Multi-line prompts with heredoc
claude-dev << 'EOF'
Implement the following features:
1. User authentication
2. Session management
3. Password reset flow
EOF
```

### Chaining Operations

```bash
# Run multiple commands sequentially
claude-sys 'apply document-integrity-scan, fix issues, and report results'

# Conditional operations
claude-dev 'implement feature X, add tests, and commit if all tests pass'
```

### Context Management

```bash
# Reference specific files
claude-dev 'refactor src/auth.py to use async/await'

# Reference documentation
claude-dev 'follow the patterns in docs/implementation-reference.md'

# Reference previous work
claude-dev 'continue the work from the previous session'
```

---

## Best Practices

### DO:

✅ Use `claude-quick` for exploration (faster, cheaper)
✅ Use `claude-dev` for most implementation work (balanced)
✅ Use `claude-think` when you need deep reasoning (better quality)
✅ Use `claude-sys` for running system-prompts processes
✅ Review git diffs before pushing
✅ Use aliases to save typing
✅ Be specific in your prompts
✅ Reference relevant documentation

### DON'T:

❌ Use `--dangerously-skip-permissions` on production systems
❌ Use Opus for simple tasks (unnecessary cost)
❌ Use Haiku for complex architectural decisions (insufficient reasoning)
❌ Forget to review changes before committing
❌ Run destructive operations without understanding them
❌ Skip reading the process documentation

---

## Troubleshooting

### "Permission denied" errors

```bash
# Solution: Use --dangerously-skip-permissions or approve tools
claude-sys 'task'  # Uses --dangerously-skip-permissions via alias
```

### "Model not available"

```bash
# Check available models
claude --list-models

# Use explicit model ID instead of alias
claude --model claude-sonnet-4-5-20250929 'task'
```

### "Can't find process/workflow"

```bash
# Claude doesn't know about a process - help it discover:
claude-sys 'read docs/system-prompts/processes/README.md and then apply document-integrity-scan'
```

### Slow responses

```bash
# Use haiku for faster (but less thorough) responses
claude-quick 'task'

# Or specify haiku explicitly
claude --model haiku 'task'
```

---

## Advanced Usage

### Custom Aliases for Specific Workflows

```bash
# Documentation work
alias claude-docs='claude --model sonnet --dangerously-skip-permissions --appendSystemPrompt "Focus on documentation quality and consistency"'

# Testing work
alias claude-test='claude --model sonnet --dangerously-skip-permissions --appendSystemPrompt "Prioritize test coverage and edge cases"'

# Security review
alias claude-security='claude --model opus --allowedTools "Read" "Glob" "Grep"'
```

### Environment-Specific Aliases

```bash
# Development environment (permissive)
alias claude-dev='claude --model sonnet --dangerously-skip-permissions'

# Staging review (read-only, careful)
alias claude-staging='claude --model opus --allowedTools "Read" "Grep" "Glob"'

# Production review (read-only, most careful)
alias claude-prod='claude --model opus --allowedTools "Read"'
```

### Wrapper Scripts

Create `~/bin/claude-profile` for more complex configuration management:

```bash
#!/bin/bash
# Usage: claude-profile <profile> <task>

PROFILE="$1"
shift

case "$PROFILE" in
  sys)
    exec claude --model sonnet --dangerously-skip-permissions "$@"
    ;; 
  quick)
    exec claude --model haiku --dangerously-skip-permissions "$@"
    ;; 
  dev)
    exec claude --model sonnet --dangerously-skip-permissions "$@"
    ;; 
  think)
    exec claude --model opus --dangerously-skip-permissions "$@"
    ;; 
  *)
    echo "Unknown profile: $PROFILE"
    exit 1
    ;; 
esac
```

---

## Cost Optimization

### Model Cost Comparison (Approximate)

- **Haiku**: ~1/10th the cost of Sonnet
- **Sonnet**: Baseline cost
- **Opus**: ~3-5x the cost of Sonnet

### Cost-Saving Strategies

1. **Use Haiku for exploration** - Reduces cost for simple queries
2. **Use Sonnet as default** - Best balance for development
3. **Reserve Opus for complex tasks** - Only when you need deep reasoning
4. **Chain operations** - One prompt instead of multiple sessions
5. **Be specific** - Clear prompts reduce back-and-forth iterations

**Example cost-conscious workflow:**

```bash
# $0.10 - Quick exploration with haiku
claude-quick 'find all authentication code'

# $1.00 - Implement with sonnet
claude-dev 'add OAuth2 support based on existing patterns'

# $0.10 - Quick verification with haiku
claude-quick 'verify OAuth2 implementation follows security best practices'

# Total: ~$1.20 instead of $15+ if everything used Opus
```

---

## Enabling and Customizing MCP Services for One-Shot Invocations

To use MCP servers (Model Context Protocol) in a single, autonomous command:

### 1. The `--mcp-server` Flag

Pass server configurations directly to the command (if supported by your version) or ensure they are configured in your config file.

```bash
# Example: Run with tools available (if configured)
claude-dev 'use the postgres-mcp tool to migrate the users table'
```

### 2. Guardrailed Execution

For autonomous tasks involving external tools, ensure you use safe permission settings:

```bash
# Require approval for tool use (default behavior safe for one-shots)
claude-dev --approval-policy "on-request" \
  'analyze the database schema and generate a report'
```

---

## Integration with Git

### Safe Git Practices

```bash
# Work on feature branches
git checkout -b feature/my-feature
claude-dev 'implement the feature'

# Review changes before committing
git diff

# Let Claude commit (but review first)
claude-dev 'review changes and commit with appropriate message if they look good'

# Never let Claude push to main directly
# (Use PRs and code review)
```

### Commit Message Best Practices

When asking Claude to commit:

```bash
# Good: Specific instructions
claude-dev 'commit these changes with message: feat: add OAuth2 authentication'

# Better: Let Claude analyze and suggest
claude-dev 'review the changes and create an appropriate commit message following conventional commits'

# Best: Review before committing
claude-dev 'show me a summary of changes and suggest a commit message, but do not commit yet'
```

---

## See Also

- [`docs/system-prompts/tools/claude-code.md`](tools/claude-code.md) - Comprehensive Claude Code guide
- [`docs/system-prompts/processes/README.md`](processes/README.md) - Available processes
- [`docs/system-prompts/workflows/README.md`](workflows/README.md) - Available workflows
- [.claude/CLAUDE.md](../../../.claude/CLAUDE.md) - Claude Code entry point for this project

---

Last Updated: 2026-01-29