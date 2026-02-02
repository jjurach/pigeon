# Gemini CLI: Workflow Optimization Tips

This document provides practical tips and configurations for optimizing your workflow when using Google Gemini CLI with the Agent Kernel system-prompts infrastructure.

**Note:** This is an optional reference document. The core workflow requirements are in [AGENTS.md](../../../AGENTS.md) and [docs/system-prompts/tools/gemini.md](../tools/gemini.md).

---

## Quick Reference Shell Aliases

### Recommended Aliases

Add these to your `~/.bashrc` or `~/.zshrc` for faster Gemini CLI invocation:

```bash
# System-prompts processes (use Flash for speed, skip permissions)
alias gemini-sys='GEMINI_MODEL=gemini-3-flash gemini --yolo'

# Quick exploration (use Flash for low latency, skip permissions)
alias gemini-quick='GEMINI_MODEL=gemini-3-flash gemini --yolo'

# Full dev work (use Pro for better reasoning, skip permissions)
alias gemini-dev='GEMINI_MODEL=gemini-3-pro gemini --yolo'

# Deep reasoning/Architecture (use Pro for max capability, skip permissions)
alias gemini-think='GEMINI_MODEL=gemini-3-pro gemini --yolo'

# Debug mode (show verbose output)
alias gemini-debug='GEMINI_DEBUG=true gemini --yolo'
```

### Usage Examples

```bash
# Run system-prompts processes
gemini-sys
> apply document-integrity-scan process and fix problems

# Quick exploration and searches
gemini-quick
> find all error handling code
> list all TODOs in the codebase

# Development tasks
gemini-dev
> implement the authentication feature
> fix the bug in the login flow

# Complex architectural decisions
gemini-think
> review the system architecture and suggest improvements
> design the caching strategy for this application
```

---

## Model Selection Guide

Choose the right model for the task to optimize speed and capability:

| Model | Use Case | Speed | Reasoning | When to Use |
|-------|----------|-------|-----------|-------------|
| **Gemini 3 Flash** | Terminal workflows, high-frequency tasks | Fastest | Good | Exploration, file searches, simple processes |
| **Gemini 3 Pro** | Complex multi-step planning, deep insights | Slower | Excellent | Feature implementation, complex debugging, architecture |
| **Gemini 2.5 Pro** | General use (Free tier often available) | Balanced | Very Good | General development if v3 is unavailable |

### Examples by Task Type

**Use Gemini 3 Flash (`gemini-quick`, `gemini-sys`) for:**
- "Find all files that import X"
- "What does this function do?"
- "Apply document-integrity-scan process"
- "Bootstrap the project"

**Use Gemini 3 Pro (`gemini-dev`, `gemini-think`) for:**
- "Implement feature X from scratch"
- "Fix this complex race condition"
- "Refactor this module and update all dependents"
- "Design the API specification"

---

## Working with System-Prompts Processes

### Process Discovery

Gemini CLI uses a ReAct loop to discover and execute processes. When you mention a process, it will typically search for the relevant files in `docs/system-prompts/processes/`.

**Best Practice:** Be explicit about reading the process file first.

```bash
# Explicit instruction (Recommended)
> Read docs/system-prompts/processes/document-integrity-scan.md and then apply it.

# Shorthand (If Gemini has context)
> Apply document-integrity-scan process.
```

### Common Process Commands

```bash
# Run document integrity scan
gemini-sys
> Apply document-integrity-scan process and fix any issues found.

# Bootstrap project
gemini-sys
> Apply bootstrap-project process to update system prompts.

# Close project (wrap up work properly)
gemini-dev
> Apply close-project process to verify work and prepare for commit.
```

---

## Workflow Optimization Patterns

### Pattern 1: Conversational Approval Loop

Gemini CLI emphasizes conversational interaction. Instead of explicit modes, it asks for confirmation.

```text
User: "Implement the login feature"
Gemini: "I\'ll start by analyzing the requirements. I\'ll read src/auth.py..."
Gemini: "I have a plan. 1. Create LoginRequest class. 2. Add route. Proceed?"
User: "Yes, but use JWT."
Gemini: "Understood. Updating plan to use JWT..."
```

**Tip:** You can guide the implementation mid-stream by giving feedback on the plan.

### Pattern 2: Exploration → Implementation

```bash
# Step 1: Quick exploration with Flash
gemini-quick
> "Find all authentication-related code and summarize the current approach."

# Step 2: Switch to Pro for Implementation
gemini-dev
> "Based on the summary (copy-paste if needed or rely on context), implement OAuth2."
```

### Pattern 3: Web-Assisted Development

Gemini has built-in web search. Use it to ground your development in latest best practices.

```bash
gemini-dev
> "Search for 'FastAPI best practices 2026' and refactor src/api.py to match."
```

---

## Project-Specific Settings

### `.gemini/GEMINI.md` Configuration

Ensure your `GEMINI.md` in `.gemini/GEMINI.md` is up to date. It drives Gemini's context.

```markdown
# Second Voice - Gemini Instructions

## Core Workflow
This project follows the **AGENTS.md** workflow.
- **MANDATORY:** Read `AGENTS.md` before starting any task.
...
```

**Tip:** Add project-specific "Tips" or "Common Commands" to `GEMINI.md` if they are relevant to the whole team.

---

## Best Practices

### DO:

✅ Use `gemini-quick` (Flash) for simple queries to save time.
✅ Use `gemini-dev` (Pro) for coding to ensure high quality.
✅ Read `AGENTS.md` at the start of every session (Gemini will remind you).
✅ Be specific in your prompts ("File: src/main.py, Lines: 10-20").
✅ Use the built-in web search to verify library versions and patterns.

### DON'T:

❌ Assume Gemini knows the full context without reading files (it's stateless between sessions unless you use context management features).
❌ Skip the "Plan" phase. Always let Gemini propose a plan before editing code.
❌ Ignore the ReAct loop reasoning. Read it to understand *why* Gemini is making a change.

---

## Troubleshooting

### "Gemini is stuck looping"

**Solution:** Interrupt and provide specific guidance.
> "Stop. You are looking in the wrong place. Check `src/utils/` instead."

### "Code edits are failing"

**Solution:** Provide more context or use a unique string anchor.
> "Replace the function `def old_function():` with this new version..."

### "I need to run a specific shell command"

**Solution:** You can ask Gemini to run it, or run it yourself in another terminal. Gemini can see file system changes made by other processes.

---

## Enabling and Customizing MCP Services for One-Shot Invocations

Gemini CLI supports the Model Context Protocol (MCP) for accessing external tools.

### 1. The `--enable-mcp` Flag

You MUST explicitly enable MCP for it to be active in a one-shot command. This is a safety feature to prevent accidental context pollution.

```bash
# Enable MCP for this specific command
gemini-dev --enable-mcp \
  "Use the internal-api-tool to fetch the latest user metrics"
```

### 2. Guardrails and Safety

When using `--enable-mcp`, Gemini has access to all configured servers.

*   **Best Practice:** Do not use `--yolo` (if available) combined with `--enable-mcp` unless you are in a sandboxed environment.
*   **Approval:** Gemini will ask for confirmation before executing MCP tool calls.

### 3. MCP Configuration

To configure the servers available to `--enable-mcp`:

1.  Edit `~/.gemini/mcp_settings.yaml` (or project equivalent).
2.  Define servers (std-io or websocket).

```bash
# Verify configuration before running one-shot
gemini --list-mcp-servers
```

---

Last Updated: 2026-01-29
```