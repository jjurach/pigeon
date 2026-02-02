# Google Gemini - Code Editor CLI Guide

**Status:** ✅ Supported

## 🚨 MANDATORY READING FIRST 🚨

**STOP!** Before reading this guide, you MUST first read the files listed in the "MANDATORY READING" section of [AGENTS.md](../../../AGENTS.md#mandatory-reading-read-first-every-session).

**Quick links to mandatory files:**
1. [Core Workflow](../workflows/logs-first.md) - How to approach all tasks
2. [Definition of Done](../../definition-of-done.md) - Completion criteria
3. [Project Guidelines](../../mandatory.md) - Second Voice specific rules

**Have you read all three?** ✓ Yes, continue. ✗ No, read them now.

---

This guide describes how to use **Google Gemini CLI** (open-source AI agent) with the AGENTS.md workflow.

## Overview

Gemini CLI is an open-source AI agent that brings Google's latest models (Gemini 3 Flash, Gemini 3 Pro) directly into your terminal. It uses a **ReAct loop** with built-in tools (file operations, shell commands, web search, MCP integration) to complete complex software development tasks.

## Quick Start

```bash
# Install (open-source, via pip or npm)
pip install gemini-cli
# OR: npm install -g @google/gemini-cli

# Set API Key (Google AI Studio or Vertex AI)
export GOOGLE_API_KEY="your-key-here"

# Run in project root
cd /path/to/second_voice
gemini
```

## How Gemini Discovers Project Instructions

Gemini looks for a `GEMINI.md` file in the project. This project uses the namespaced `.gemini/GEMINI.md` to keep the root directory clean.

**Discovery:**
1. **Project-specific:** `./.gemini/GEMINI.md` (This is what we use)
2. **Home Directory:** `~/.gemini/GEMINI.md` (fallback)

## Model Selection & Capabilities

Gemini CLI supports cutting-edge models optimized for different use cases:

| Model | Best For | SWE-Bench | Context |
|-------|----------|-----------|---------|
| **Gemini 3 Flash** | Terminal workflows, high-frequency tasks | 78% verified | Fast, efficient |
| **Gemini 3 Pro** | Complex multi-step planning, deep insights | Higher | Full reasoning |
| **Gemini 2.5 Pro** | Free option (Google account) | — | Limited |

**Configuration:**
```bash
# Set model in ~/.gemini/config.yaml
model: gemini-3-flash        # Fast, recommended for AGENTS.md
# OR: gemini-3-pro           # Powerful, for complex tasks

# Or via environment
export GEMINI_MODEL=gemini-3-flash
```

## Advanced Features

### ReAct Loop Architecture
Gemini uses **Reason + Act** cycle with built-in tools:
- Reads files and context
- Reasons about the task
- Uses tools (shell, file ops, web search)
- Iterates until task complete

### MCP (Model Context Protocol) Support
Integrate custom tools and services:
```bash
# Enable MCP servers for extended capabilities
# Example: Database access, API clients, custom scripts
```

### Conductor Extension (Preview 2026)
New context-driven development approach:
- Structured planning for AI-assisted development
- Better context management for complex tasks
- Integration with dev_notes workflow

## AGENTS.md Workflow Mapping

| AGENTS.md Step | Gemini Action | Implementation |
|---|---|---|
| **A. Analyze** | Analyze request using ReAct reasoning | Conversational analysis |
| **B. Spec** | Write spec file | `write_file` to dev_notes/specs/ |
| **C. Plan** | Write plan file | `write_file` to dev_notes/project_plans/ |
| **D. Approval** | Ask conversationally ("Do you approve?") | **Interactive (no explicit gate)** |
| **E. Implement** | Edit files, run commands step-by-step | `read_file`, `replace`, `run_shell_command` |
| **F. Verify** | Run tests and validate | `run_shell_command` (pytest, etc.) |

## Key Differences from Claude Code

| Feature | Claude Code | Gemini CLI |
|---|---|---|
| **Entry Point** | `.claude/CLAUDE.md` | `.gemini/GEMINI.md` |
| **Approval** | `ExitPlanMode()` (Explicit) | **Conversational** ("Do you approve?") |
| **Git** | `Bash(git ...)` | `run_shell_command(git ...)` |
| **Task Tracking** | Built-in (`TaskCreate`) | **Manual** (via `dev_notes/`) |
| **Context** | ~200k tokens | ~1M+ tokens (1.5 Pro) |

## Configuration: .gemini/GEMINI.md

Create a `GEMINI.md` file in `.gemini/GEMINI.md` with the following content:

```markdown
# Second Voice - Gemini Instructions

## Core Workflow
This project follows the **AGENTS.md** workflow.
- **MANDATORY:** Read `AGENTS.md` before starting any task.
- **MANDATORY:** Read `docs/definition-of-done.md` before marking tasks complete.

## Development Environment
- **Language:** Python 3.12+
- **Testing:** `pytest`
- **Linting:** Standard Python conventions
- **Project Structure:**
  - `src/`: Source code
  - `tests/`: Unit tests
  - `dev_notes/`: Documentation & Plans

## Key Commands
- Run App: `python3 src/cli/run.py`
- Run Tests: `pytest`
- Check Types: `mypy .`
```

## Common Patterns & Examples

### Pattern 1: Feature with Conversational Approval
```
User: "Add user authentication to the API"

Gemini analyzes request, creates spec and plan
Gemini: "I've created dev_notes/specs/... and dev_notes/project_plans/..."
Gemini: "Does this approach look good? Should I proceed?"
User: "Yes, proceed"

Gemini implements step by step:
- Creates auth module
- Adds tests
- Updates docs
- Creates dev_notes/changes/... entry
```

### Pattern 2: Quick Bug Fix
```
User: "Fix the config parsing error in src/config.py"

Gemini analyzes the issue (ReAct reasoning)
Gemini: "I found the issue and fixed it. Running tests..."
[Auto-runs pytest]
Gemini: "✓ All tests pass"
```

### Pattern 3: Test-Driven Refactor
```
User: "Refactor the API module to use dependency injection"

Gemini:
1. Reads current implementation
2. Creates plan in dev_notes/
3. Asks for approval
4. Writes tests first (test-driven)
5. Refactors implementation
6. Verifies all tests pass
7. Documents changes
```

### Pattern 4: Web-Assisted Development
```
User: "Implement async/await patterns in our HTTP client"

Gemini (via built-in web search):
- Searches current best practices
- Implements improvements
- Tests against benchmarks
- Creates detailed change docs
```

## Tool-Specific Commands Reference

| Task | Command | Notes |
|------|---------|-------|
| Start interactive | `gemini` | Opens REPL |
| Use Gemini 3 Flash | Set `GEMINI_MODEL=gemini-3-flash` | Recommended |
| Use Gemini 3 Pro | Set `GEMINI_MODEL=gemini-3-pro` | More powerful |
| View reasoning | Ask "Show your reasoning" | ReAct loop transparency |
| Enable MCP | `gemini --enable-mcp` | Custom integrations |
| Use Conductor | `gemini --conductor` | Preview mode (2026) |
| Check model | `gemini --version` | Shows active model |

## Error Handling & Troubleshooting

**Problem:** "GEMINI.md not found"
**Solution:** Create a GEMINI.md file:
```bash
mkdir -p .gemini
cat > .gemini/GEMINI.md << 'EOF'
# Project - Gemini Instructions

This project follows AGENTS.md workflow.
- See AGENTS.md for core workflow
- See docs/definition-of-done.md for completion criteria
EOF
```

**Problem:** "API key not recognized"
**Solution:** Verify configuration:
```bash
export GOOGLE_API_KEY="your-key"
# OR: Use Google AI Studio free tier (GOOGLE_GENERATIVE_AI_API_KEY)
```

**Problem:** "ReAct loop seems stuck"
**Solution:** Provide clearer context:
```
User: "The HTTP client has a race condition in request pooling.
      File: src/http_client.py, Lines 42-67"
```

**Problem:** "File editing failed - unique context required"
**Solution:** Provide more context lines when asking for edits:
```
User: "In src/api.py, after the 'def get_user()' function (around line 45),
      add validation for empty strings. Show 5 lines before and after."
```

## Verification Status

- ✅ Open-source CLI available (github.com/google-gemini/gemini-cli)
- ✅ Gemini 3 Flash (78% SWE-bench verified) for terminal workflows
- ✅ Gemini 3 Pro for complex multi-step tasks
- ✅ ReAct loop architecture for reasoning
- ✅ MCP (Model Context Protocol) support for custom integrations
- ✅ Conductor extension preview (structured development)
- ✅ Native AGENTS.md support via .gemini/GEMINI.md
- ✅ Web search grounding (for best practices, patterns)
- ✅ Compatible with `second_voice` workflow

## Key Differences from Claude Code

| Feature | Claude Code | Gemini CLI |
|---|---|---|
| **Language** | Python-based | Standalone CLI (multi-lang) |
| **License** | Proprietary | ✅ Open-source |
| **Models** | Claude Opus | ✅ Gemini 3 Flash/Pro/2.5 |
| **Approval** | ExitPlanMode (explicit) | Conversational (flexible) |
| **Context** | ~200k tokens | Model-dependent (1M+) |
| **Entry Point** | .claude/CLAUDE.md | .gemini/GEMINI.md |
| **Web Search** | Via WebSearch tool | ✅ Built-in |
| **MCP Support** | Via tools | ✅ Native |
| **ReAct Loop** | N/A | ✅ Yes (reasoning shown) |
| **Conductor** | N/A | ✅ Preview 2026 |

## Quick Reference Card

```bash
# Configuration
~/.gemini/config.yaml       # Global config
./.gemini/GEMINI.md         # Project instructions
./dev_notes/                # Workflow artifacts

# Environment Variables
GOOGLE_API_KEY              # Auth token
GEMINI_MODEL                # Model selection
GEMINI_DEBUG                # Enable debug output

# Common Commands
gemini                      # Interactive shell
gemini --version            # Show version/model
gemini --help               # Show help

# In-session Commands
/clear                      # Clear conversation
/exit                       # Exit shell
```