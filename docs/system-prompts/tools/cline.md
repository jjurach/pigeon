# Cline - Code Editor CLI Guide

**Status:** ✅ Supported

## 🚨 MANDATORY READING FIRST 🚨

**STOP!** Before reading this guide, you MUST first read the files listed in the "MANDATORY READING" section of [AGENTS.md](../../../AGENTS.md#mandatory-reading-read-first-every-session).

**Quick links to mandatory files:**
1. [Core Workflow](../workflows/logs-first.md) - How to approach all tasks
2. [Definition of Done](../../definition-of-done.md) - Completion criteria
3. [Project Guidelines](../../mandatory.md) - Second Voice specific rules

**Have you read all three?** ✓ Yes, continue. ✗ No, read them now.

---

This guide describes how to use **Cline CLI** with the AGENTS.md workflow.

## Overview

Cline is an open-source AI agent CLI tool that operates as a code editor, similar to Claude Code and Aider. It enables developers to use AI assistance for code changes, refactoring, and development tasks directly from the terminal.

## Quick Start

```bash
# Install Cline CLI (requires Node.js 16+)
npm install -g cline

# Or via pip
pip install cline-cli

# Run in project root
cd /path/to/project
cline
```

## How Cline Discovers Project Instructions

Cline looks for a `.clinerules` file in the project root. This file serves the same purpose as `CLAUDE.md` and `GEMINI.md` in other tools.

**Discovery:**
1. **Project Root:** `./.clinerules` (This is what we use)
2. **Home Directory:** `~/.cline/CLINE.md` (fallback)

## Configuration

Cline uses configuration at `~/.cline/config.json` or environment variables.

### Recommended Config

```json
{
  "model": "gpt-4o",
  "approvalMode": "suggest",
  "autoCommit": true,
  "cwd": "/path/to/project"
}
```

### Environment Variables

```bash
CLINE_MODEL=gpt-4o              # Model to use
CLINE_APPROVAL_MODE=suggest     # Approval behavior
CLINE_API_KEY=sk-...            # API authentication
CLINE_TIMEOUT=120               # Request timeout (seconds)
```

## AGENTS.md Workflow Mapping

| AGENTS.md Step | Cline Action | Implementation |
|---|---|---|
| **A. Analyze** | Analyze request and context | Internal reasoning |
| **B. Spec** | Write spec file | `write_file` to dev_notes/specs/ |
| **C. Plan** | Write plan file | `write_file` to dev_notes/project_plans/ |
| **D. Approval** | Ask conversationally ("Should I proceed?") | **Interactive (no explicit gate)** |
| **E. Implement** | Edit files, run commands | `read_file`, `replace`, `run_shell_command` |
| **F. Verify** | Run tests and validate | `run_shell_command` (pytest, etc.) |

## Key Capabilities

- **Multi-file editing** - Coordinated changes across multiple files
- **Shell integration** - Can execute commands and read output
- **Git awareness** - Creates commits automatically
- **Iterative refinement** - Maintains context across multiple turns
- **Error handling** - Can respond to test failures and linting errors

## Common Patterns & Examples

### Pattern 1: Feature Development with Approval

```
User: "Implement authentication module"

Cline:
1. Analyzes requirements
2. Creates spec in dev_notes/specs/...
3. Creates plan in dev_notes/project_plans/...
4. Asks "Does this approach look good?"
5. User approves
6. Implements with coordinated file changes
7. Runs tests and verifies
8. Creates change documentation
```

### Pattern 2: Bug Fix

```
User: "Fix the race condition in request pooling"

Cline:
1. Reads relevant code (src/http_client.py, etc.)
2. Identifies root cause
3. Implements fix
4. Runs tests
5. Verifies with test output
```

### Pattern 3: Multi-File Refactoring

```
User: "Rename all config keys from camelCase to snake_case"

Cline:
1. Identifies all affected files
2. Updates imports and usage
3. Updates tests
4. Updates documentation
5. Runs full test suite
6. Creates single git commit with all changes
```

### Pattern 4: Interactive Refinement

```
User: "Add dark mode support"
Cline: [Makes initial implementation]
User: "Make the toggle more prominent"
Cline: [Refines based on feedback]
User: "Add keyboard shortcut"
Cline: [Adds feature while maintaining previous changes]
```

## Tool-Specific Commands Reference

| Task | Command | Notes |
|------|---------|-------|
| Start interactive | `cline` | Opens REPL |
| Specific model | `CLINE_MODEL=gpt-4o cline` | Set via env var |
| Approval mode | `CLINE_APPROVAL_MODE=suggest` | Interactive approval |
| Skip approval | `CLINE_APPROVAL_MODE=auto` | Auto-edit without asking |
| View context | Ask "Show your reasoning" | Transparency |
| Set config | `~/.cline/config.json` | Persistent settings |

## Error Handling & Troubleshooting

**Problem:** ".clinerules not found"
**Solution:** Create a .clinerules file in project root:

```bash
cat > .clinerules << 'EOF'
# Project - Cline Instructions

This project follows AGENTS.md workflow.
- See AGENTS.md for core workflow
- See `docs/definition-of-done.md` for completion criteria
EOF
```

**Problem:** "Approval mode not responding"
**Solution:** Ensure CLINE_APPROVAL_MODE is set correctly:
```bash
export CLINE_APPROVAL_MODE=suggest
```

**Problem:** "Can't find files to edit"
**Solution:** Ensure Cline can read file paths:
```bash
# Provide full paths or ensure Cline is in correct directory
cd /path/to/project && cline
```

**Problem:** "Tests failing silently"
**Solution:** Ask Cline to show test output explicitly:
```
User: "Run pytest and show the full output"
```

## Verification Status

- ✅ CLI Tool exists and is maintained
- ✅ AGENTS.md support via CLINE.md entry point
- ✅ Interactive approval modes working
- ✅ Multi-file editing capability confirmed
- ✅ Git integration operational
- ✅ Workflow compatible with AGENTS.md

## Key Differences from Claude Code

| Feature | Claude Code | Cline |
|---|---|---|
| **Language** | Python-based | Node.js-based |
| **Approval** | ExitPlanMode (explicit) | Conversational (flexible) |
| **Git** | `Bash(git ...)` | `run_shell_command(git ...)` |
| **Task Tracking** | Built-in (TaskCreate) | **Manual** (via dev_notes/) |
| **Context** | ~200k tokens | Depends on model |
| **Entry Point** | `CLAUDE.md` | `.clinerules` |
| **Shell Integration** | Full Bash tool | Via subprocess |
| **Multi-file edits** | Good | **Excellent** |
| **Auto-commit** | Manual | ✅ Automatic |

## Quick Reference Card

```bash
# Configuration files
~/.cline/config.json            # Global config
./CLINE.md                      # Project instructions
./dev_notes/                    # Workflow artifacts

# Environment variables
CLINE_MODEL                     # Model selection
CLINE_API_KEY                   # Authentication
CLINE_APPROVAL_MODE             # Approval behavior
CLINE_TIMEOUT                   # Timeout (seconds)

# Common commands
cline                           # Start interactive
CLINE_MODEL=gpt-4o cline       # Use specific model
cline --version                 # Show version
cline --help                    # Show help
```

## Further Reading

- [Cline Repository](https://github.com/cline/cline)
- [Official Cline Documentation](https://docs.cline.ai)
- AGENTS.md - Core workflow all tools follow
- `docs/definition-of-done.md` - Completion criteria
