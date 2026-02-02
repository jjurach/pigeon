# Codex CLI: Workflow Optimization Tips

This document provides practical tips and configurations for optimizing your workflow when using Codex CLI with the Agent Kernel system-prompts infrastructure.

**Note:** This is an optional reference document. The core workflows in AGENTS.md do not require reading this file.

---

## Quick Reference Shell Aliases

### Recommended Aliases

Add these to your `~/.bashrc` or `~/.zshrc` for faster Codex CLI invocation:

```bash
# System-prompts processes (use default model, auto-approve)
alias codex-sys='codex --approval-mode full-auto'

# Quick exploration (use mini model for speed/cost, auto-approve)
alias codex-quick='codex --model gpt-5-mini --approval-mode full-auto'

# Full dev work (use codex-max model, auto-approve)
alias codex-dev='codex --model gpt-5.1-codex-max --approval-mode full-auto'

# Deep reasoning (use latest frontier model, auto-approve)
alias codex-think='codex --model gpt-5.2-codex --approval-mode full-auto'
```

### Usage Examples

```bash
# Run system-prompts processes
codex-sys 'apply document-integrity-scan process and fix problems'

# Quick exploration and searches
codex-quick 'find all error handling code'
codex-quick 'list all TODOs in the codebase'

# Development tasks
codex-dev 'implement the authentication feature'
codex-dev 'fix the bug in the login flow'

# Complex architectural decisions
codex-think 'review the system architecture and suggest improvements'
codex-think 'design the caching strategy for this application'

# Session resumption (works with all aliases)
codex resume --last                       # Resume most recent session
codex resume <SESSION_ID>                 # Resume specific session
codex resume                              # Interactive session picker

# Aliases work with resumption
codex-dev resume --last 'fix tests and close project'
codex-quick resume <SESSION_ID> 'summarize what we were working on'
```

---

## Model Selection Guide

Choose the right model for the task to optimize cost and speed:

| Model | Use Case | Speed | Cost | When to Use |
|-------|----------|-------|------|-------------|
| **gpt-5-mini** | Quick reads, searches, simple tasks | Fastest | Lowest | Exploration, file searches, simple Q&A |
| **gpt-5-codex** | Most development work | Balanced | Medium | Feature implementation, bug fixes, refactoring |
| **gpt-5.1-codex-max** | Complex features, extensive changes | Moderate | Higher | Multi-file refactoring, complex features |
| **gpt-5.2-codex** | Frontier reasoning, architecture | Slower | Highest | Architecture design, security reviews, complex debugging |

### Examples by Task Type

**Use Mini (`codex-quick`) for:**
- "Find all files that import X"
- "What does this function do?"
- "List all API endpoints"
- "Show me the error handling code"

**Use Codex (`codex-sys` or default) for:**
- "Apply document-integrity-scan process"
- "Add tests for this component"
- "Fix this specific bug"

**Use Codex-Max (`codex-dev`) for:**
- "Implement feature X"
- "Refactor this module"
- "Add comprehensive error handling across the codebase"

**Use Frontier (`codex-think`) for:**
- "Design the authentication system architecture"
- "Review this PR for security vulnerabilities"
- "Suggest improvements to our caching strategy"
- "Debug this complex race condition"

### Switching Models Mid-Session

```bash
# Inside a Codex session, use /model command
> /model gpt-5.2-codex
> /model gpt-5-mini
```

---

## Permission Management

### Approval Policies

Codex uses different approval modes for tool use and edits:

**Configuration options:**
- `approval_policy = "on-request"` - Ask before executing tools/edits (default)
- `approval_policy = "auto"` - Automatically approve tool use
- `sandbox_mode = "workspace-write"` - Restrict to workspace directory

**Modes:**
- **suggest** (default) - Shows proposed changes, requires approval
- **auto-edit** - Automatically applies edits
- **full-auto** - Fully autonomous operation

**Safety considerations:**
- Codex can execute ANY shell command in auto mode
- Codex can edit/delete ANY file in the workspace
- Use in development environments you control
- Review git diffs before pushing

---

## Working with System-Prompts Processes

### Process Discovery

When you mention a process by name, Codex should automatically check `docs/system-prompts/processes/` for the specification.

**Shorthand invocations:**

```bash
# Long form
codex-sys 'apply the document-integrity-scan.md process'

# Short form (recommended)
codex-sys 'apply document-integrity-scan process'

# Even shorter
codex-sys 'run docscan'
codex-sys 'scan docs'
```

### Available Processes

| Process | Command | Description |
|---------|---------|-------------|
| **document-integrity-scan** | `codex-sys 'apply document-integrity-scan'` | Validate documentation correctness |
| **bootstrap-project** | `codex-sys 'apply bootstrap-project'` | Initialize/update Agent Kernel |
| **close-project** | `codex-dev 'apply close-project process'` | Properly complete and land work before ending session |

### Common Process Commands

```bash
# Run document integrity scan
codex-sys 'apply document-integrity-scan process and fix any issues'

# Run docscan directly
codex-sys 'run python3 docs/system-prompts/docscan.py and fix issues'

# Bootstrap with workflow analysis
codex-sys 'apply bootstrap-project with --analyze-workflow flag'

# Close project (wrap up work properly)
codex-dev 'apply close-project process'
codex-dev 'close this project and commit changes'
```

---

## Workflow Optimization Patterns

### Pattern 1: Exploration → Implementation

```bash
# Step 1: Quick exploration with mini model
codex-quick 'find all authentication-related code'

# Step 2: Detailed implementation with codex-max
codex-dev 'add OAuth2 support to the authentication module'
```

### Pattern 2: Research → Deep Analysis

```bash
# Step 1: Quick search
codex-quick 'what are our current caching mechanisms?'

# Step 2: Deep architectural review
codex-think 'design a comprehensive caching strategy for the entire system'
```

### Pattern 3: Validate → Fix → Verify

```bash
# Step 1: Run validation
codex-sys 'apply document-integrity-scan process'

# Step 2: Fix reported issues
codex-dev 'fix the broken links reported in the scan'

# Step 3: Re-validate
codex-sys 'apply document-integrity-scan process'
```

### Pattern 4: Development → Close Project

**Complete development cycle with proper project closure:**

```bash
# Step 1: Implement the feature
codex-dev 'implement user authentication with OAuth2'

# Step 2: Run tests and verify
codex-dev 'run tests and verify all pass'

# Step 3: Close the project properly
codex-dev 'apply close-project process'
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

**Codex CLI has built-in session resumption** - each session is stored locally and can be continued later with full context:

```bash
# Resume the most recent session
codex resume --last

# Resume a specific session (get ID from picker or ~/.codex/sessions/)
codex resume <SESSION_ID>

# Interactive session picker (browse all sessions)
codex resume

# Resume with follow-up instruction
codex resume --last 'fix the test failures and apply close-project process'

# Resume with aliases
codex-dev resume --last 'continue and close project'
codex-quick resume <SESSION_ID> 'summarize what we were working on'
```

**Session management workflow:**

```bash
# Session 1: Start work, tests fail
codex-dev 'implement OAuth authentication'
# Note the session ID from /status
# Session ends (tests failed, need to stop)

# Session 2: Resume by ID with full context
codex resume <SESSION_ID>
# Codex remembers everything from session 1
# Fix issues, then:
> apply close-project process
```

**Why this works:**
- Codex stores full conversation history per session in `~/.codex/sessions/`
- Sessions include timestamps, messages, output, and token usage
- Resuming restores complete context automatically
- No need to manually read files or reconstruct state

**Session management tips:**

```bash
# View session status inside Codex
> /status

# Resume from inside an active session
> /resume

# Resume with additional options
codex resume --last --cd /different/path
codex resume <SESSION_ID> --add-dir /extra/context

# List sessions (stored in ~/.codex/sessions/*.jsonl)
ls -lt ~/.codex/sessions/

# View session content
cat ~/.codex/sessions/<SESSION_ID>.jsonl | jq
```

**Key difference from Claude Code:**
- Codex uses session IDs instead of named sessions
- No `/rename` command (sessions identified by ID)
- Use `--last` flag for quick resume
- Session picker (`codex resume`) shows recent interactive sessions

**Alternative: Manual context reconstruction** (if session is lost/unavailable):

```bash
# Read change documentation to understand previous work
codex-dev 'read dev_notes/changes/2026-01-29_14-22-00_add-oauth-auth.md and continue implementing OAuth'
```

---

## Project-Specific Settings

### For This Project (`second_voice`)

You can configure project-specific settings in `.codex/config.toml` or `.codex/config.json`:

```toml
# Default model
model = "gpt-5-codex"

# Approval policy
approval_policy = "on-request"

# Sandbox mode
sandbox_mode = "workspace-write"

# Enable web search
web_search = true
```

### Settings Hierarchy

Codex uses configuration files:

1. **Command line flags** (highest priority)
2. **Project config** (`~/.codex/config.toml` in project)
3. **Global config** (`~/.codex/config.toml` in home)

**Tip:** Use project settings for shared team preferences, global settings for personal defaults.

---

## Command-Line Tips

### Inline Prompts

```bash
# Use quotes for prompts with spaces
codex-dev 'implement user authentication'

# Use single quotes to avoid shell variable expansion
codex-dev 'show all $variables in the code'

# Multi-line prompts with heredoc
codex-dev << 'EOF'
Implement the following features:
1. User authentication
2. Session management
3. Password reset flow
EOF
```

### Chaining Operations

```bash
# Run multiple commands sequentially
codex-sys 'apply document-integrity-scan, fix issues, and report results'

# Conditional operations
codex-dev 'implement feature X, add tests, and commit if all tests pass'
```

### Context Management

```bash
# Reference specific files
codex-dev 'refactor src/auth.py to use async/await'

# Reference documentation
codex-dev 'follow the patterns in docs/implementation-reference.md'

# Continue from previous session
codex resume --last
```

---

## Slash Commands Reference

Inside a Codex session, you can use these slash commands:

```bash
# Show status (token usage, config, current state)
> /status

# Switch models
> /model gpt-5.2-codex
> /model gpt-5-mini

# View Git diff
> /diff

# Summarize conversation
> /compact

# Start fresh conversation (in same session)
> /new

# Resume another session
> /resume

# Exit Codex
> /quit
> /exit

# View all commands
> /
```

---

## Best Practices

### DO:

✅ Use `codex-quick` for exploration (faster, cheaper)
✅ Use `codex-dev` for most implementation work (balanced)
✅ Use `codex-think` when you need deep reasoning (better quality)
✅ Use `codex-sys` for running system-prompts processes
✅ Use `codex resume --last` to continue recent work
✅ Review git diffs before pushing
✅ Use aliases to save typing
✅ Be specific in your prompts
✅ Reference relevant documentation
✅ Check `/status` to monitor token usage

### DON'T:

❌ Use `full-auto` mode on production systems
❌ Use frontier models for simple tasks (unnecessary cost)
❌ Use mini models for complex architectural decisions (insufficient reasoning)
❌ Forget to review changes before committing
❌ Run destructive operations without understanding them
❌ Skip reading the process documentation

---

## Troubleshooting

### "Permission denied" errors

```bash
# Solution: Check approval_policy in config
# Set to "auto" for automatic approval (use with caution)
# Or approve actions when prompted
```

### "Model not available"

```bash
# Check available models
codex --help

# Use explicit model name
codex --model gpt-5.2-codex 'task'
```

### "Can't find process/workflow"

```bash
# Help Codex discover the process
codex-sys 'read docs/system-prompts/processes/README.md and then apply document-integrity-scan'
```

### "Session not found"

```bash
# List available sessions
ls ~/.codex/sessions/

# Use interactive picker
codex resume
```

### Slow responses

```bash
# Use mini model for faster (but less thorough) responses
codex-quick 'task'

# Or specify mini explicitly
codex --model gpt-5-mini 'task'
```

---

## Cost Optimization

### Model Cost Comparison (Approximate)

- **gpt-5-mini**: ~1/10th the cost of gpt-5-codex
- **gpt-5-codex**: Baseline cost
- **gpt-5.1-codex-max**: ~2-3x the cost of gpt-5-codex
- **gpt-5.2-codex**: ~3-5x the cost of gpt-5-codex

### Cost-Saving Strategies

1. **Use mini for exploration** - Reduces cost for simple queries
2. **Use codex as default** - Best balance for development
3. **Reserve frontier models for complex tasks** - Only when you need deep reasoning
4. **Chain operations** - One prompt instead of multiple sessions
5. **Be specific** - Clear prompts reduce back-and-forth iterations
6. **Monitor with `/status`** - Track token usage in real-time

**Example cost-conscious workflow:**

```bash
# $0.10 - Quick exploration with mini
codex-quick 'find all authentication code'

# $1.00 - Implement with codex
codex-dev 'add OAuth2 support based on existing patterns'

# $0.10 - Quick verification with mini
codex-quick 'verify OAuth2 implementation follows security best practices'

# Total: ~$1.20 instead of $15+ if everything used frontier model
```

---

## Enabling and Customizing MCP Services

**Note:** Codex CLI currently **does not** have native support for the Model Context Protocol (MCP).

### Recommendation

If your autonomous task requires MCP tools (database access, slack integration, specialized API tools), use **Gemini CLI** or **Cline** instead.

```bash
# Instead of codex-dev...
gemini-dev --enable-mcp "task requiring mcp tools"
```

---

## Integration with Git

### Safe Git Practices

```bash
# Work on feature branches
git checkout -b feature/my-feature
codex-dev 'implement the feature'

# Review changes before committing
git diff

# Let Codex commit (but review first)
codex-dev 'review changes and commit with appropriate message if they look good'

# Never let Codex push to main directly
# (Use PRs and code review)
```

### Commit Message Best Practices

When asking Codex to commit:

```bash
# Good: Specific instructions
codex-dev 'commit these changes with message: feat: add OAuth2 authentication'

# Better: Let Codex analyze and suggest
codex-dev 'review the changes and create an appropriate commit message following conventional commits'

# Best: Review before committing
codex-dev 'show me a summary of changes and suggest a commit message, but do not commit yet'
```

---

## See Also

- [docs/system-prompts/tools/codex.md](../tools/codex.md) - Comprehensive Codex guide for AGENTS.md workflow
- [docs/system-prompts/processes/README.md](../processes/README.md) - Available processes
- [docs/system-prompts/workflows/README.md](../workflows/README.md) - Available workflows
- [AGENTS.md](../../../AGENTS.md) - Core workflow for AI agents

---

## Sources

This document was created based on official Codex CLI documentation and community resources:

- [Codex | OpenAI](https://openai.com/codex/)
- [GitHub - openai/codex](https://github.com/openai/codex)
- [Codex CLI Documentation](https://developers.openai.com/codex/cli/)
- [Codex CLI Features](https://developers.openai.com/codex/cli/features/)
- [Command Line Options Reference](https://developers.openai.com/codex/cli/reference/)
- [Slash Commands Documentation](https://developers.openai.com/codex/cli/slash-commands/)
- [Codex vs Claude Code Comparison](https://apidog.com/blog/claude-code-vs-codex-cli/)
- [Codex CLI Developer Guide](https://majesticlabs.dev/blog/202509/codex-cli-developer-guide/)

---

Last Updated: 2026-01-29