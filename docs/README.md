# Documentation Index

Complete documentation for Pigeon - Google Drive polling service for voice recordings.

## Quick Start

**For AI Agents:**
- Start with **[AGENTS.md](../AGENTS.md)** - Mandatory workflow and unbreakable rules
- Check **[Definition of Done](definition-of-done.md)** - Quality standards

**For Developers:**
- Read **[README.md](../README.md)** - Project overview
- See **[Architecture](architecture.md)** - System design
- Review **[Implementation Reference](implementation-reference.md)** - Code patterns

## For AI Agents

### Core Workflow
- **[AGENTS.md](../AGENTS.md)** - Mandatory A-E workflow and project-specific rules
- **[Definition of Done](definition-of-done.md)** - Complete quality checklist
- **[Workflows](workflows.md)** - Project-specific development workflows
- **[Templates](templates.md)** - Planning document templates

### Tool-Specific Guides
- **[Claude Code Tool](../.claude/CLAUDE.md)** - Claude Code setup and usage
- **[Aider Tool](../.aider.md)** - Aider integration (if applicable)

## Architecture & Design

- **[Architecture](architecture.md)** - System architecture and design decisions
- **[Implementation Reference](implementation-reference.md)** - Implementation patterns and code examples

## For Developers

### Getting Started
- **[Project README](../README.md)** - Project overview, installation, and usage
- **[Contributing](contributing.md)** - How to contribute (if exists)

### Development Guide
- **[Workflows](workflows.md)** - Development workflows and common commands
- **[Definition of Done](definition-of-done.md)** - Quality standards and verification steps
- **[Architecture](architecture.md)** - System design for developers

### Reference
- **[Implementation Reference](implementation-reference.md)** - Code patterns and examples
- **[Templates](templates.md)** - Document templates for planning

## System Prompts (Agent Kernel)

The Agent Kernel provides reusable workflows and standards:

- **[Agent Kernel README](system-prompts/README.md)** - Complete Agent Kernel documentation
- **[Universal Definition of Done](system-prompts/principles/definition-of-done.md)** - Universal quality standards
- **[Python Definition of Done](system-prompts/languages/python/definition-of-done.md)** - Python-specific standards
- **[Templates](system-prompts/templates/structure.md)** - Document structure templates
- **[Workflows](system-prompts/workflows/README.md)** - Workflow documentation
- **[Tools](system-prompts/tools/README.md)** - Tool-specific guides

## Navigation Tips

### Finding Information

**"How do I get started?"**
→ Start with [../README.md](../README.md)

**"What are the quality standards?"**
→ See [Definition of Done](definition-of-done.md)

**"What is the system architecture?"**
→ Read [Architecture](architecture.md)

**"How do I implement a feature?"**
→ Follow [Workflows](workflows.md) and use patterns from [Implementation Reference](implementation-reference.md)

**"What's the mandatory workflow?"**
→ Read [../AGENTS.md](../AGENTS.md)

**"How do I debug an issue?"**
→ See debugging workflow in [Workflows](workflows.md)

### For First-Time Contributors

1. Read [../README.md](../README.md) - Project overview
2. Review [Architecture](architecture.md) - Understand the system
3. Check [Workflows](workflows.md) - Development process
4. Review [Definition of Done](definition-of-done.md) - Quality checklist

### For AI Agents Starting Work

1. Read [../AGENTS.md](../AGENTS.md) - Mandatory workflow
2. Check [Definition of Done](definition-of-done.md) - Quality standards
3. Review [Workflows](workflows.md) - Development processes
4. Use [Templates](templates.md) - For planning documents

### Troubleshooting

**"My configuration isn't working"**
→ Check `Configuration` section in [Workflows](workflows.md)

**"Tests are failing"**
→ See `Testing Workflow` in [Workflows](workflows.md)

**"I can't connect to Google Drive"**
→ Check [../README.md](../README.md) Troubleshooting section and [Architecture](architecture.md) Authentication section

**"Daemon won't start"**
→ See `Daemon Management Workflow` in [Workflows](workflows.md)

## File Structure

```
project-root/
├── AGENTS.md                           # Combined: Agent Kernel + project extensions
├── README.md                           # Main project documentation
├── .claude/CLAUDE.md                   # Claude Code tool entry point
├── docs/
│   ├── README.md                       # This file - Documentation index
│   ├── definition-of-done.md          # Project DoD (extends Agent Kernel)
│   ├── architecture.md                # Project architecture
│   ├── implementation-reference.md    # Implementation patterns and examples
│   ├── workflows.md                   # Project workflows
│   ├── templates.md                   # Planning document templates
│   └── system-prompts/                # Agent Kernel (read-only)
│       ├── README.md                  # Agent Kernel documentation
│       ├── principles/                # Universal principles
│       ├── languages/                 # Language-specific standards
│       ├── templates/                 # Document templates
│       ├── workflows/                 # Workflow documentation
│       └── tools/                     # Tool-specific guides
├── src/pigeon/                        # Source code
│   ├── __init__.py
│   ├── config.py
│   ├── drive_client.py
│   ├── poller.py
│   └── main.py
├── tests/                             # Tests
├── dev_notes/                         # Runtime documentation
│   ├── changes/                       # Change logs
│   ├── specs/                         # Specifications
│   └── inbox/                         # Downloaded files
├── scripts/                           # Helper scripts
├── tmp/                               # Runtime files (not git)
├── venv/                              # Virtual environment
├── .env.example                       # Configuration template
├── pyproject.toml                     # Package metadata
└── requirements-dev.txt               # Dev dependencies
```

## Key Cross-References

### Between Project Docs and Agent Kernel

**Project Documentation References Agent Kernel for:**
- Core workflow: [AGENTS.md](../AGENTS.md) → [system-prompts/workflows/](system-prompts/workflows/)
- Universal DoD: [Definition of Done](definition-of-done.md) → [system-prompts/principles/definition-of-done.md](system-prompts/principles/definition-of-done.md)
- Python DoD: [Definition of Done](definition-of-done.md) → [system-prompts/languages/python/definition-of-done.md](system-prompts/languages/python/definition-of-done.md)
- Templates: [Templates](templates.md) → [system-prompts/templates/](system-prompts/templates/)

**Agent Kernel References Project:**
- Project Integration: [system-prompts/README.md](system-prompts/README.md) → Project-specific extensions section

## See Also

- **[Project README](../README.md)** - Main project documentation
- **[AGENTS.md](../AGENTS.md)** - Agent workflow and rules

---

Last Updated: 2026-02-01
