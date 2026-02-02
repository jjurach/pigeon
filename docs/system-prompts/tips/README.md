# Workflow Optimization Tips

This directory contains **optional** workflow optimization guides for different AI coding tools.

**Important:** These tips documents are **supplementary and not required** for using the Agent Kernel workflows. The core workflows in [AGENTS.md](../../../AGENTS.md) work without reading these files.

---

## What's in This Directory

Workflow optimization tips for:

- **[claude-code.md](claude-code.md)** - Claude Code CLI tips (shell aliases, session resumption, model selection)
- **[gemini.md](gemini.md)** - Gemini CLI tips (model selection, ReAct loop patterns, web-assisted dev)
- **[codex.md](codex.md)** - Codex CLI tips (session management, model selection, cost optimization)
- **[cline.md](cline.md)** - Cline (VS Code extension + CLI) tips (task management, Plan/Act modes)

---

## What These Tips Cover

Each tips document provides:

1. **Shell Aliases** - Convenient shortcuts for common operations
2. **Model Selection** - When to use which model (cost/speed trade-offs)
3. **Session Management** - How to resume previous work
4. **Workflow Patterns** - Common development patterns
5. **Cost Optimization** - Strategies for reducing API costs
6. **Permission Management** - Safe practices for auto-approval
7. **Troubleshooting** - Common issues and solutions

---

## When to Read These Tips

✅ **Read these tips when:**
- You want to optimize your workflow
- You're looking for shell alias suggestions
- You want to understand session resumption
- You're trying to reduce API costs
- You want to learn advanced features

❌ **You DON'T need these tips for:**
- Basic Agent Kernel workflow usage
- Following AGENTS.md processes
- Running system-prompts processes
- Standard development work

---

## Core Documentation

For required reading, see:

- **[AGENTS.md](../../../AGENTS.md)** - Core workflow (MANDATORY)
- **[docs/definition-of-done.md](../../definition-of-done.md)** - Quality criteria (MANDATORY)
- **[docs/system-prompts/tools/](../tools/)** - Tool-specific Agent Kernel integration guides (REQUIRED for your tool)

---

## Adding New Tips Documents

When creating tips for a new tool:

1. Create `docs/system-prompts/tips/[tool-name].md`
2. Follow the structure of existing tips documents
3. Add note at top: "This is an optional reference document..."
4. Add link in tool's entry point file (e.g., `CLAUDE.md`, `CLINE.md`)
5. Mark as optional: "Note: These tips are supplementary..."

---

Last Updated: 2026-01-29
