# Tool-Specific Workflow Guides

This directory contains **generic, reusable, comprehensive workflow guides** for integrating different AI development tools with the `AGENTS.md` workflow.

**Related:** Entry point files ([.claude/CLAUDE.md](../../../.claude/CLAUDE.md), [.aider.md](../../../.aider.md), [.clinerules](../../../.clinerules), [.gemini/GEMINI.md](../../../.gemini/GEMINI.md)) are minimal navigation hubs that redirect users to these comprehensive guides.

## Available Guides

- **[claude-code.md](./claude-code.md)** - Claude Code (Python CLI, Anthropic)
  - Interactive development IDE with explicit approval gates (ExitPlanMode)
  - Comprehensive toolset (Read, Write, Edit, Bash, Task)
  - Best for structured workflows with detailed planning

- **[aider.md](./aider.md)** - Aider (Terminal-based code editor)
  - Trust-based collaboration with cascade agents
  - Multi-file refactoring with automatic testing
  - Git-first workflow with readable commits

- **[cline.md](./cline.md)** - Cline (Code editor CLI)
  - Open-source interactive development tool
  - Multi-file editing with auto-commit to git
  - Flexible approval modes (suggest, auto, conversational)

- **[codex.md](./codex.md)** - OpenAI Codex (Code editor CLI)
  - Native AGENTS.md discovery
  - Granular approval modes (suggest, auto-edit, full-auto)
  - GPT-5.2 optimization for long-horizon tasks

- **[gemini.md](./gemini.md)** - Google Gemini (Open-source AI agent CLI)
  - ReAct loop architecture with reasoning transparency
  - MCP (Model Context Protocol) for custom integrations
  - Web search grounding and SWE-bench verified models

## Purpose & Reusability

These guides are **generic documentation** explaining how each tool integrates with AGENTS.md workflow patterns. They are **not project-specific** and can be:

- Copied to other projects
- Referenced by bootstrap.py
- Integrated into system-prompts infrastructure
- Used as reference material for developers

## Entry Point → Guide Hierarchy

**User Discovery Flow:**

```
1. User enters project with Tool X
2. Finds entry point in project root (e.g., CLAUDE.md)
3. Entry point provides 4 quick links
4. User follows tool guide link
5. Arrives at comprehensive guide (this directory)
```

**Entry Point Characteristics:**
- **Anemic format** - 20 lines maximum
- **Navigation only** - No detailed content
- **Auto-generated** - Created by bootstrap.py templates
- **Validated** - Checked by docscan.py

**Tool Guide Characteristics (this directory):**
- **Comprehensive** - 200-600+ lines
- **Generic** - Reusable across projects
- **Reference material** - Not mandatory instructions
- **Canonical** - Single source of truth per tool

**Relationship:** Entry points → Point to → Tool guides

For details on managing entry points, see [Tool Entry Points Process](../processes/tool-entry-points.md) (if present).

## Project-Specific Tool Guides

For guides specific to individual projects (e.g., how Cline integrates with second_voice), see the project's `docs/tool-specific-guides/` directory.

## How Agents Use These Guides

These guides are **reference material**, not mandatory loading for agents. Agents should:

- Consult these when they need to understand a tool's capabilities
- Use them for troubleshooting tool-specific issues
- Reference patterns and examples as needed
- NOT treat them as imperative instructions to follow

Mandatory tool instructions (how to use ExitPlanMode, basic workflow mapping) are located in `AGENTS.md` or tool-specific configuration files (`.claude/CLAUDE.md`, `.gemini/GEMINI.md`, `.aider.md`, `.clinerules`).

## Conditional References

These guides contain **optional technique documentation**:

- Timestamped file naming patterns (used if logs-first is enabled)
- Approval gate mechanisms (used if tool supports them)
- Dev_notes workflow examples (used if logs-first is enabled)

**All techniques are described as conditional:** "If you need to...", "When using...", "Optional pattern...". They do NOT mandate specific behavior.

## Updates & Maintenance

When updating these guides:

1. Maintain **tool-agnostic language** where possible
2. Use **conditional phrasing** for project-specific patterns
3. Keep **technique-focused** rather than prescriptive
4. Document **as reference material**, not mandatory instructions
5. Test **referential integrity** across projects
