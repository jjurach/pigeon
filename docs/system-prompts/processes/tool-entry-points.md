# Tool Entry Points Process

**Purpose:** Understand the design and maintenance of anemic tool entry point files (`.aider.md`, `.claude/CLAUDE.md`, `.clinerules`, `.gemini/GEMINI.md`).

**Status:** Documented and validated via bootstrap.py and docscan.py

---

## Overview

Tool entry point files are **minimal, referential files** that serve as discovery and navigation starting points for AI tool users. They redirect readers to comprehensive guides elsewhere in the documentation.

### What Are Anemic Entry Points?

\"Anemic\" refers to the architecture pattern of keeping these files simple and lightweight:
- **Not** a place for tool-specific content (that belongs in tool guides)
- **Not** for configuration instructions (that belongs in tool guides)
- **Not** for development environment details (that belongs in README.md)
- **Is** a simple index with four critical links

### The User Journey

1. **User enters project with tool X**
2. **Looks for entry point** (e.g., `.claude/CLAUDE.md`, `.clinerules`, `.aider.md`)
3. **Finds quick links** to:
   - AGENTS.md (core workflow - mandatory)
   - definition-of-done.md (completion criteria)
   - docs/system-prompts/tools/{tool}.md (comprehensive guide)
   - `docs/workflows.md` (optional structured planning)
4. **Clicks through** to full documentation

---

## Design Specification

### Entry Point Format (Standard)

Every tool entry point follows this exact structure (20 lines maximum):

```markdown
# [Tool Name] Instructions

This project follows the **AGENTS.md** workflow for all development.

## Quick Links

- **Read First:** [AGENTS.md](AGENTS.md) - Core workflow (mandatory)
- **Completion Criteria:** [docs/definition-of-done.md](docs/definition-of-done.md) - Definition of done
- **Tool Guide:** [docs/system-prompts/tools/{tool}.md](docs/system-prompts/tools/{tool}.md) - Complete guide
- **Workflows:** [docs/workflows.md](docs/workflows.md) - Optional structured planning

## For [Tool] Users

The **[docs/system-prompts/tools/{tool}.md](docs/system-prompts/tools/{tool}.md)** guide covers:
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]
```

### Required Elements

- **Header (Line 1):** `# [Tool Name] Instructions`
- **Workflow reference (Line 3):** Statement about following AGENTS.md
- **Quick Links section:** Exactly 4 mandatory links:
  1. AGENTS.md - Core workflow
  2. definition-of-done.md - Completion criteria
  3. Tool guide (docs/system-prompts/tools/{tool}.md)
  4. Workflows (`docs/workflows.md`)
- **For [Tool] Users section:** Brief description of what the full guide covers

### Line Count Constraint

- **Target:** 25 lines maximum
- **Checked by:** bootstrap.py `validate_tool_entry_point()`
- **Enforced by:** docscan.py `--check tool-entries`
- **Rationale:** Keeps files truly anemic; more content belongs in tool guides

### Links Must Be Hyperlinked

- **Format:** `[text](path)` - markdown hyperlinks only
- **Not:** Plain text references or backticks
- **Why:** Improves discoverability in markdown viewers
- **Validation:** docscan.py reference-formatting check includes entry points

---

## What Content Goes Where

### Tool Entry Points (20 lines max)
- Navigation only
- Four quick links
- Brief guide description
- Tool name and workflow reference

### Tool Guides (docs/system-prompts/tools/{tool}.md)
- Quick start & installation
- How tool discovers instructions
- Workflow mapping to AGENTS.md
- Complete tool capabilities
- Configuration & setup
- Code examples & patterns
- Troubleshooting
- Limitations & gotchas
- Quick reference cards

### Project README.md
- Project overview
- Development environment setup
- Getting started guide
- Project structure
- Links to comprehensive guides

### AGENTS.md
- Core workflow (Steps A-E)
- Unbreakable rules
- Fundamental principles

### definition-of-done.md
- Completion criteria
- Verification requirements
- Configuration integrity rules

### `workflows.md`
- Optional logs-first workflow
- When to use structured planning
- How structured planning works

---

## Maintenance & Validation

### Bootstrap Tool Support

**Validate all entry points:**
```bash
python3 docs/system-prompts/bootstrap.py --validate-tool-entries
```

**Regenerate from templates:**
```bash
python3 docs/system-prompts/bootstrap.py --regenerate-tool-entries --commit
```

**Capabilities:**
- Validates all 4 files (`.claude/CLAUDE.md`, `.aider.md`, `.clinerules`, `.gemini/GEMINI.md`)
- Checks: file exists, line count ≤25, all 4 links present, no forbidden patterns
- Can regenerate from canonical templates if needed
- Preserves dry-run mode by default

### Document Integrity Scanning

**Validate entry points in integrity scan:**
```bash
python3 docs/system-prompts/docscan.py --check tool-entries
```

**Full scan (includes tool entry points):**
```bash
python3 docs/system-prompts/docscan.py
```

**Automated checks:**
1. File exists (all 4)
2. Line count ≤20 (anemic format)
3. Required links present (4 mandatory links)
4. Tool guide link correct (maps to right file: claude→claude-code, etc.)
5. No forbidden patterns (Available Tools, Development Environment, Key Commands, etc.)

---

## Canonical Templates

Entry points are generated from templates in bootstrap.py:

### CLAUDE.md Template
```markdown
# Claude Code Instructions

This project follows the **AGENTS.md** workflow for all development.

## Quick Links

- **Read First:** [AGENTS.md](AGENTS.md) - Core workflow (mandatory)
- **Completion Criteria:** [docs/definition-of-done.md](docs/definition-of-done.md) - Definition of done
- **Tool Guide:** [docs/system-prompts/tools/claude-code.md](docs/system-prompts/tools/claude-code.md) - Complete guide
- **Workflows:** [docs/workflows.md](docs/workflows.md) - Optional structured planning

## For Claude Code Users

The **[docs/system-prompts/tools/claude-code.md](docs/system-prompts/tools/claude-code.md)** guide covers:
- Quick start and installation
- How Claude Code discovers project instructions
- Workflow mapping to AGENTS.md
- All tools and task tracking
- Approval gates and common patterns
- Troubleshooting
```

### Tool Name Mapping

When templates are generated, tool entry point names map to tool guide files:
- `.claude/CLAUDE.md` → `docs/system-prompts/tools/claude-code.md`
- `.aider.md` → `docs/system-prompts/tools/aider.md`
- `.clinerules` → `docs/system-prompts/tools/cline.md`
- `.gemini/GEMINI.md` → `docs/system-prompts/tools/gemini.md`

---

## Adding a New Tool

To add support for a new tool (e.g., Tool X):

### 1. Create Tool Guide
- Add `docs/system-prompts/tools/tool-x.md` (600+ lines recommended)
- Include all sections: quick start, workflow mapping, capabilities, patterns, troubleshooting

### 2. Add Entry Point Template
- Update bootstrap.py `get_tool_entry_point_template()` method
- Add template for \"tool-x\" following the standard 20-line format
- Include tool-specific guide descriptions

### 3. Update Tool Name Mapping
- Add mapping in bootstrap.py: `\"tool-x\": \".path/to/TOOL-X.md\"` (or custom name)
- Add mapping in docscan.py: same mapping for validation

### 4. Update Validation
- Add \".path/to/TOOL-X.md\" to tools dict in docscan.py `_check_tool_entry_points()`
- Add \"tool-x\" to tools list in bootstrap.py `validate_all_tool_entries()`

### 5. Generate Entry Point
```bash
python3 docs/system-prompts/bootstrap.py --regenerate-tool-entries --commit
```

### 6. Verify
```bash
python3 docs/system-prompts/bootstrap.py --validate-tool-entries
python3 docs/system-prompts/docscan.py --check tool-entries
```

---

## Common Mistakes to Avoid

### ❌ Don't put in entry points:
- **Tool capability lists** - Goes in tool guide
- **Configuration instructions** - Goes in tool guide
- **Development environment details** - Goes in README.md
- **Key commands/examples** - Goes in tool guide
- **Full workflow explanations** - Goes in AGENTS.md
- **"Key Concepts"** - References AGENTS.md instead

### ❌ Don't violate constraints:
- **More than 20 lines** - Keep anemic (use docscan to enforce)
- **Missing any of 4 quick links** - All 4 are mandatory
- **Plain text references** - Use hyperlinks only
- **Outdated content** - Use canonical templates from bootstrap.py

### ✅ Do:
- **Keep files minimal** - Think "guide index" not "guide content"
- **Use canonical templates** - Let bootstrap.py generate/regenerate
- **Run validation** - Use bootstrap.py and docscan.py regularly
- **Point to real guides** - All links must be correct and working
- **Stay consistent** - All entry points follow same format

---

## Verification Checklist

### Before Modifying Entry Points

- [ ] File is 20 lines or fewer
- [ ] Has proper header: `# [Tool] Instructions`
- [ ] Contains AGENTS.md link: `[AGENTS.md](AGENTS.md)`
- [ ] Contains definition-of-done link: `definition-of-done.md`
- [ ] Contains tool guide link: `docs/system-prompts/tools/{tool}.md`
- [ ] Contains workflows link: `docs/workflows.md`
- [ ] No "## Available Tools" section
- [ ] No "## Development Environment" section
- [ ] No "## Key Commands" section
- [ ] No "## Key Concepts" section (should reference AGENTS.md)

### Before Committing Changes

- [ ] Run: `python3 docs/system-prompts/bootstrap.py --validate-tool-entries`
- [ ] Result: All 4 files show "Valid anemic format"
- [ ] Run: `python3 docs/system-prompts/docscan.py --check tool-entries`
- [ ] Result: All checks passed
- [ ] No warnings or errors

### After Adding New Entry Point

- [ ] Added template to bootstrap.py
- [ ] Added to tools dict in docscan.py
- [ ] Added to tools list in bootstrap.py
- [ ] Ran: `python3 docs/system-prompts/bootstrap.py --regenerate-tool-entries --commit`
- [ ] Ran validation checks
- [ ] Updated this document with new tool details

---

## Integration with Other Systems

### Bootstrap.py Integration
- Entry point validation: `--validate-tool-entries`
- Entry point generation: `--regenerate-tool-entries`
- Canonical source for file content
- Manages tool name mappings

### docscan.py Integration
- Layer 4 check: Tool entry point validation
- Part of full integrity scan
- Accessible via: `--check tool-entries`
- Validates: existence, format, links, content constraints

### CI/CD Integration Example
```bash
#!/bin/bash
# Pre-commit hook to validate tool entries

python3 docs/system-prompts/bootstrap.py --validate-tool-entries
if [ $? -ne 0 ]; then
  echo "❌ Tool entry points validation failed"
  exit 1
fi

python3 docs/system-prompts/docscan.py --check tool-entries --strict
if [ $? -ne 0 ]; then
  echo "❌ Document integrity scan failed"
  exit 1
fi
```

---

## Summary

Tool entry points are **anemic, minimal files** that serve as navigation hubs for AI tool users:

- **20 lines max** - Anemic architecture (enforced)
- **4 mandatory links** - AGENTS.md, definition-of-done.md, tool guide, workflows
- **Canonical templates** - Generated/validated by bootstrap.py
- **Automated enforcement** - Validated by docscan.py
- **Single source of truth** - bootstrap.py templates are canonical
- **Clear content separation** - Entry points = navigation only; guides = content

All content lives in the right place:
- Entry points → Quick navigation
- Tool guides → Comprehensive reference
- AGENTS.md → Core workflow
- definition-of-done.md → Completion criteria
- README.md → Project overview

