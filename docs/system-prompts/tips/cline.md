# Cline: Workflow Optimization Tips

This document provides practical tips and configurations for optimizing your workflow when using Cline (VS Code extension + CLI) with the Agent Kernel system-prompts infrastructure.

**Note:** This is an optional reference document. The core workflows in AGENTS.md do not require reading this file.

---

## Overview

Cline is an autonomous coding agent that operates right in your IDE (VS Code/JetBrains) and terminal. It can create/edit files, execute commands, use the browser, and more with your permission every step of the way.

**Key platforms:**
- **VS Code Extension** (primary) - GUI-based interaction
- **Cline CLI** - Terminal-first development
- **JetBrains Plugin** - Support for IntelliJ-based IDEs

---

## Quick Reference: CLI Commands

### Installation & Setup

```bash
# Install Cline CLI (if separate from VS Code extension)
npm install -g cline-cli

# Or use the VS Code extension
# Search "Cline" in VS Code Extensions marketplace
```

### Task Management

```bash
# List previous tasks
cline task list

# Resume a specific task by ID
cline task open 1760501486669

# View conversation history
cline task view

# Start interactive chat
cline task chat

# Create new task
cline task new
```

### Configuration

```bash
# Set configuration variable
cline config set key value

# Read configuration variable
cline config get key

# List all configuration variables
cline config list
```

### Task Aliases (for convenience)

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick task management
alias cline-list='cline task list'
alias cline-resume='cline task open'
alias cline-view='cline task view'

# Development tasks (auto-approved)
alias cline-dev='cline --yolo --mode act'
alias cline-quick='cline --yolo --mode act'

# System-prompts processes
alias cline-sys='cline --yolo --mode act'

# One-shot commands
alias cline-ask='cline --yolo --mode act'
```

**Flag explanations:**
- `--yolo`: Auto-approve all actions (skip permission prompts)
- `--mode act`: Use Act Mode for execution
- Direct description/command follows flags (no `task new` needed)

**Usage examples:**
```bash
# Create development task
cline-dev 'implement OAuth authentication'

# Quick task
cline-quick 'refactor auth module'

# System-prompts process
cline-sys 'apply document-integrity-scan process'

# One-shot command
cline-ask 'explain this error'

# Task management (without flags)
cline-list                      # List recent tasks
cline-resume 1760501486669     # Resume specific task
```

---

## VS Code Extension Usage

### Opening Cline

**Keyboard shortcuts:**

```
Ctrl+Shift+P → "Cline: Open in New Tab"
```

**Or map a custom keyboard shortcut:**

1. Open VS Code keyboard shortcuts (Ctrl+K Ctrl+S)
2. Search for `workbench.view.extension.claude-dev-ActivityBar`
3. Assign your preferred keybinding

### Common Workflows

```bash
# Open Cline sidebar
Click Cline icon in Activity Bar (left sidebar)

# Start new task
Click "New Task" button or use keyboard shortcut

# Resume previous task
Click task in History panel
Or use CLI: cline task open <TASK_ID>

# View task history
Click "History" in Cline sidebar
```

---

## Model Selection & Configuration

### Supported Providers

Cline supports 35+ AI providers:
- **Anthropic** (Claude models)
- **OpenAI** (GPT models)
- **OpenRouter** (access to many models)
- **Google Gemini**
- **AWS Bedrock**
- **Azure OpenAI**
- **GCP Vertex AI**
- **Cerebras**
- **Groq**
- **Local models** (via LM Studio/Ollama)

### Model Selection Guide

| Model | Provider | Use Case | Cost |
|-------|----------|----------|------|
| **Claude Sonnet 4.5** | Anthropic | Most development work | Medium |
| **Claude Opus 4** | Anthropic | Complex reasoning, architecture | Highest |
| **GPT-5-Codex** | OpenAI | Code-focused tasks | Medium |
| **Gemini 2.0 Flash** | Google | Fast, affordable tasks | Low |
| **Local models** | Ollama | Privacy, offline work | Free (compute) |

### Configuring API Keys

**Via VS Code settings:**

1. Open Cline extension
2. Click gear icon (settings)
3. Select your provider
4. Enter API key
5. Select default model

**Via CLI:**

```bash
# Set API key
cline config set anthropic.apiKey YOUR_API_KEY
cline config set openai.apiKey YOUR_API_KEY

# Set default model
cline config set model claude-sonnet-4-5
```

### Command Line Flags

Key flags for CLI usage:
- `--yolo`: Auto-approve all actions (no confirmation prompts)
- `--mode <plan|act>`: Set workflow mode (default: plan)
- `--no-interactive`: Run without additional prompts
- `--oneshot`: Execute a single command and exit

### Plan and Act Modes

Cline has two-phase workflow modes:

**Plan Mode:**
- Use for strategic planning
- Typically uses reasoning-focused models (Claude Opus, o1)
- Higher cost but better architecture decisions

**Act Mode:**
- Use for task execution
- Typically uses faster models (Claude Sonnet, GPT-5-Codex)
- Balance of speed and capability

**Configuration:**

```bash
# Set different models for Plan and Act
cline config set planMode.model claude-opus-4
cline config set actMode.model claude-sonnet-4-5
```

---

## Working with System-Prompts Processes

### Process Invocation

When using Cline with system-prompts processes:

**Via CLI:**

```bash
# Apply document integrity scan
cline task new 'apply document-integrity-scan process and fix issues'

# Bootstrap project
cline task new 'apply bootstrap-project process'

# Close project
cline task new 'apply close-project process'
```

**Via VS Code Extension:**

1. Open Cline sidebar
2. Click "New Task"
3. Type: `apply document-integrity-scan process`
4. Cline will read `docs/system-prompts/processes/` and execute

### Available Processes

| Process | Command | Description |
|---------|---------|-------------|
| **document-integrity-scan** | `apply document-integrity-scan` | Validate documentation correctness |
| **bootstrap-project** | `apply bootstrap-project` | Initialize/update Agent Kernel |
| **close-project** | `apply close-project process` | Properly complete and land work |

---

## Workflow Optimization Patterns

### Pattern 1: GUI + CLI Workflow

```bash
# Start in VS Code (visual feedback, file navigation)
# Open Cline sidebar
# Create task: "implement OAuth authentication"

# Switch to CLI for quick checks
cline task list
cline task view

# Resume in VS Code when ready to review
```

### Pattern 2: CLI-First Development

```bash
# Create task from command line
cline task new 'implement user authentication with OAuth2'

# Let Cline work autonomously
# Review output in ~/.cline/x/tasks/<task-id>/

# Resume if interrupted
cline task open <TASK_ID>
```

### Pattern 3: Development → Close Project

```bash
# Step 1: Implement feature
cline task new 'implement OAuth authentication'

# Step 2: Verify and test
# (Cline runs tests automatically if configured)

# Step 3: Close project properly
cline task new 'apply close-project process'
```

**What close-project does:**
1. ✅ Verifies Definition of Done criteria
2. ✅ Runs tests (aborts if non-trivial failures)
3. ✅ Checks/creates change documentation
4. ✅ Commits changes with proper attribution
5. ✅ Reports final status

### Pattern 4: Resuming Tasks

**Via CLI:**

```bash
# List recent tasks
cline task list

# Resume by ID
cline task open 1760501486669

# Or in VS Code, click task in History panel
```

**Task storage location:**
- `~/.cline/x/tasks/<task-id>/`
- Contains: `api_conversation_history.json`, `ui_messages.json`, `task_metadata.json`
- Checkpoints saved in `checkpoints/` directory

**Why resumption works:**
- Full conversation history persisted
- Task settings automatically restored
- Context maintained across sessions
- No need to manually reconstruct state

---

## Permission Management

### Approval Workflow

Cline asks for permission before:
- Creating or editing files
- Executing terminal commands
- Using browser automation
- Making API calls

**Permission modes:**
- **Manual approval** (default) - Approve each action
- **Auto-approve for task** - Approve all actions in current task
- **Auto-approve for session** - Approve all actions until restart

**Safety tips:**
- ✅ Review file changes before approving
- ✅ Check terminal commands for destructive operations
- ✅ Use manual approval for production work
- ✅ Enable auto-approve only for trusted, well-scoped tasks

---

## Context Management

### Adding Context to Tasks

**Files and directories:**

```bash
# Reference specific files in prompt
cline task new 'refactor src/auth.py to use async/await'

# Reference documentation
cline task new 'follow patterns in docs/implementation-reference.md'
```

**Large projects:**

Cline can explore large projects using its file navigation tools. It will:
- Read relevant files based on task context
- Search codebase for patterns
- Navigate directory structure
- Track linter/compiler errors

**MCP (Model Context Protocol):**

Cline supports MCP to extend capabilities:
- Custom tools
- External data sources
- API integrations

---

## Best Practices

### DO:

✅ Use Plan mode for architecture decisions
✅ Use Act mode for implementation
✅ Review changes before approving
✅ Use task history to resume work
✅ Configure appropriate models for task types
✅ Enable browser tools for web development
✅ Use terminal integration for testing
✅ Reference system-prompts processes explicitly

### DON'T:

❌ Auto-approve without reviewing on production
❌ Use expensive models (Opus) for simple tasks
❌ Ignore linter/compiler errors during development
❌ Forget to configure API keys for your provider
❌ Skip reading process documentation
❌ Delete task history (stored in ~/.cline/)

---

## Troubleshooting

### "API key not configured"

```bash
# Set API key via CLI
cline config set anthropic.apiKey YOUR_API_KEY

# Or via VS Code extension settings
Open Cline → Settings → Select provider → Enter API key
```

### "Task history disappeared"

**Check storage location:**

```bash
# Task history stored at:
ls -la ~/.cline/x/tasks/

# Global storage for VS Code extension:
ls -la "$(code --locate-extension saoudrizwan.claude-dev)/globalStorage/"
```

**If missing:**
- Task data may be in different profile (VS Code profiles)
- Extension may have been reinstalled
- Check `.vscode/globalStorage/` in project root

### "Permission denied for terminal commands"

**Solution:**
- Approve terminal access in Cline
- Check VS Code terminal permissions
- Ensure shell integration is enabled

### "Model not responding"

**Check:**
1. API key is valid
2. Model is available (check provider status)
3. Network connection is stable
4. Token limits not exceeded

**Debug:**

```bash
# Check configuration
cline config list

# View task logs
cline task view

# Check API usage/costs in task metadata
cat ~/.cline/x/tasks/<TASK_ID>/task_metadata.json
```

---

## Cost Optimization

### Model Selection Strategy

1. **Plan with reasoning models** - Use Opus/o1 for planning (higher cost, better decisions)
2. **Act with balanced models** - Use Sonnet for execution (lower cost, good performance)
3. **Explore with fast models** - Use Gemini Flash/GPT-5-mini for quick tasks

### Cost Tracking

```bash
# View cost in task metadata
cat ~/.cline/x/tasks/<TASK_ID>/task_metadata.json | jq '.cost'

# Cline tracks:
# - Total tokens used
# - API usage cost per task
# - Individual request costs
```

### Cost-Saving Tips

1. Use OpenRouter for access to cheaper models
2. Configure local models (Ollama) for offline work
3. Use Gemini Flash for exploration (fast + cheap)
4. Monitor costs in task metadata
5. Set spending limits in provider dashboards

---

## Enabling and Customizing MCP Services for One-Shot Invocations

Cline relies on configuration files for MCP, but you can target them in one-shot commands.

### 1. Pre-Configuration

MCP servers must be defined in your `~/.cline/mcp_settings.json` (or via the extension settings). They are loaded automatically when Cline starts.

### 2. Targeted Invocations

Instruct Cline to use specific tools in your prompt.

```bash
# Explicitly request the tool
cline task new \
  "Use the 'postgres-mcp' server to inspect the 'users' table schema"
```

### 3. Guardrails for Autonomous Tasks

Since Cline is autonomous, it will stop and ask for permission for MCP tool use unless you have enabled "Auto-approve".

*   **For One-Shot Safety:** Stick to the default **Manual Approval** mode for any task involving external side effects (database writes, API POSTs).
*   **For Trusted Read-Only:** You can configure auto-approval for specific read-only tools if the CLI supports granular permissions, otherwise, keep it interactive or monitor the output.

---

## Integration with Git

### Git Operations

Cline can:
- Create commits with appropriate messages
- Review git diffs
- Create branches
- Stage files
- Push to remote (with permission)

**Safe practices:**

```bash
# Let Cline review changes
"show me git diff and explain the changes"

# Let Cline create commit message
"create an appropriate commit message following conventional commits"

# Always review before pushing
"create commit but do not push"
```

---

## VS Code Extension Features

### Sidebar Tools

**Available in Cline sidebar:**
- New Task button
- Task History
- Settings (API keys, models)
- Browser preview (for web development)
- Terminal output viewer
- File change diff viewer

### Browser Automation

For web development, Cline can:
- Launch site in headless browser
- Click, type, scroll
- Capture screenshots
- Monitor console logs
- Debug frontend issues

**Enable browser tools:**

1. Open Cline settings
2. Enable "Browser Tools"
3. Configure browser path (if needed)

---

## CLI vs Extension: When to Use Which

### Use CLI When:

- ✅ Terminal-first workflow
- ✅ Scripting/automation
- ✅ SSH/remote development
- ✅ Quick task resumption
- ✅ Headless environments

### Use VS Code Extension When:

- ✅ Visual file navigation needed
- ✅ Reviewing large diffs
- ✅ Web development (browser tools)
- ✅ Learning/exploration
- ✅ Multi-file changes with preview

### Use Both:

Start in CLI, switch to VS Code for review:

```bash
# CLI: Create and work on task
cline task new 'implement feature'

# VS Code: Review changes in sidebar
# Open Cline → History → Select task → Review diffs
```

---

## See Also

- [docs/system-prompts/tools/cline.md](../tools/cline.md) - Comprehensive Cline guide for AGENTS.md workflow
- [docs/system-prompts/processes/README.md](../processes/README.md) - Available processes
- [docs/system-prompts/workflows/README.md](../workflows/README.md) - Available workflows
- [AGENTS.md](../../../AGENTS.md) - Core workflow for AI agents

---

## Sources

This document was created based on official Cline documentation and community resources:

- [Cline Official Website](https://cline.bot/)
- [Cline - VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
- [GitHub - cline/cline](https://github.com/cline/cline)
- [Cline Wiki](https://github.com/cline/cline/wiki)
- [Cline CLI Reference](https://docs.cline.bot/cline-cli/cli-reference)
- [API Configuration Guide](https://deepwiki.com/cline/cline/3.1-api-configuration-and-provider-management)
- [Plan and Act Modes](https://deepwiki.com/cline/cline/3.4-plan-and-act-modes)
- [Cline Configuration Guide - APIpie](https://apipie.ai/docs/Integrations/Coding/Cline)

---

Last Updated: 2026-01-29