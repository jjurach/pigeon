# OpenAI Codex - Code Editor CLI Guide

**Status:** ✅ Supported

This guide describes how to use the **OpenAI Codex CLI** with this project's AGENTS.md workflow.

## Overview

Codex is OpenAI's advanced code editor CLI featuring **agentic coding** capabilities powered by GPT-5.2 optimization for long-horizon code changes. It provides sandboxed execution, multi-file refactoring, and native AGENTS.md support.

## Quick Start

```bash
# Install (requires Node.js 16+)
npm install -g @openai/codex

# Set API Key
export OPENAI_API_KEY="sk-..."

# Run in project root
cd /path/to/your-project
codex
```

## How Codex Discovers Project Instructions

**Codex natively supports `AGENTS.md` with intelligent discovery!**

When Codex starts, it builds an instruction chain by reading AGENTS.md files in this order (merging all found):

1. **Home Directory:** `~/.codex/AGENTS.override.md` (if exists), else `~/.codex/AGENTS.md`
2. **Project Path:** Starting at git root, walking down to current directory:
   - `./AGENTS.override.md` (highest priority—allows local overrides)
   - `./AGENTS.md` (standard project instructions - **This is what we use**)
   - Project-specific fallback names from configuration

This discovery means **no special configuration needed**—Codex automatically reads and respects our AGENTS.md workflow.

## Configuration

Codex uses configuration at `~/.codex/config.json` or `.yaml`.

### Recommended Config (`~/.codex/config.yaml`)

```yaml
model: gpt-5.2-codex  # Latest GPT-5.2 optimized for agentic coding
approvalMode: suggest  # or auto-edit / full-auto / skip-approval
sandboxing: enabled   # OS-level sandboxing (macOS/Linux)
notify: true          # Desktop notifications
agent_skills: true    # Enable agent skills for reusable task bundles
```

### Advanced Features

**Agent Skills** (2026 feature): Reusable bundles of instructions plus optional scripts and resources. Invoke with `$skill-name`:

```bash
# Example: Invoke a skill
> $test-all          # Runs comprehensive test suite
> $lint-and-format   # Auto-lints and formats code
```

**GPT-5.2 Optimizations** (Latest 2026):
- Long-horizon work through context compaction
- Stronger performance on large code changes (refactors, migrations)
- Improved Windows environment support
- Significantly stronger cybersecurity capabilities

## AGENTS.md Workflow Integration

Codex respects your AGENTS.md workflow automatically. Here's how it maps:

| AGENTS.md Step | Codex Action | Mode |
|---|---|---|
| **Step A: Analyze & Declare Intent** | Reads request, determines scope | Conversational |
| **Step B: Create Spec** | Writes spec file in `dev_notes/specs/` | Suggest mode |
| **Step C: Create Plan** | Writes plan in `dev_notes/project_plans/` | Suggest mode |
| **Step D: Approval** | Asks "Should I proceed?" | Interactive (approval-mode) |
| **Step E: Implement** | Makes coordinated changes, auto-commits | Auto-commit mode |

**Approval Modes:**
- `suggest`: Interactive; Codex asks before each change ✅ Recommended for AGENTS.md
- `auto-edit`: Shows diffs, then commits
- `full-auto`: Auto-commits without review
- `skip-approval`: For CI/scripting only

## Common Patterns & Examples

### Pattern 1: Creating a Feature with Approval
```bash
codex --approval-mode suggest
> "Add authentication module following AGENTS.md workflow"

# Codex will:
# 1. Create dev_notes/specs/YYYY-MM-DD_HH-MM-SS_auth.md
# 2. Create dev_notes/project_plans/YYYY-MM-DD_HH-MM-SS_auth-plan.md
# 3. Ask "Ready to implement?"
# 4. Execute step by step, showing diffs
# 5. Create dev_notes/changes/YYYY-MM-DD_HH-MM-SS_auth-implementation.md
```

### Pattern 2: Quick Bug Fix (Trivial)
```bash
codex "Fix the typo in docs/README.md line 42"

# Codex recognizes this as trivial
# Makes change immediately, auto-commits
```

### Pattern 3: Multi-File Refactoring
```bash
codex --skill $refactor-config
> "Rename all config keys from camelCase to snake_case"

# Uses cascade architecture for coordinated changes
# Auto-lints and tests each file
# Creates readable, bisectable git commits
```

### Pattern 4: Non-Interactive (CI Pipeline)
```bash
codex --quiet --approval-mode auto-edit \
  --provider openai \
  "Run pytest and fix all failures"
```

## Key Differences from Claude Code

| Feature | Claude Code | Codex |
|---------|---|---|
| **Language** | Python-based | Node.js/Rust-based |
| **Sandboxing** | Standard | ✅ OS-level (Seatbelt/Docker) |
| **Approval Modes** | One (ExitPlanMode) | ✅ Four granular options |
| **Context Window** | ~200k tokens | Depends on model (GPT-5.2) |
| **AGENTS.md Support** | Via CLAUDE.md | ✅ Native, auto-discovery |
| **Agent Skills** | No | ✅ Yes (`$skill-name`) |
| **Multi-file Refactor** | Good | ✅ Excellent (cascade agent) |
| **Auto-testing** | Manual | ✅ Automatic on every change |

## Error Handling & Troubleshooting

**Problem:** "AGENTS.md not found"
**Solution:** Ensure AGENTS.md exists in project root:
```bash
ls -la AGENTS.md
# If missing: codex will use home directory AGENTS.md instead
```

**Problem:** "Approval mode not working as expected"
**Solution:** Verify config:
```bash
cat ~/.codex/config.yaml | grep approvalMode
# Should be: approvalMode: suggest
```

**Problem:** "Need to cancel/rollback changes"
**Solution:** Codex creates clean git commits:
```bash
git log --oneline
git revert <commit-hash>  # Revert specific commit
```

## Verification Status



- ✅ CLI Tool exists and is actively maintained

- ✅ Native `AGENTS.md` discovery with fallback chain

- ✅ GPT-5.2 optimization for long-horizon tasks

- ✅ Agent Skills for reusable task bundles

- ✅ Sandboxed execution (macOS/Linux)

- ✅ Workflow compatible with AGENTS.md
