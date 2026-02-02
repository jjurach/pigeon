# Bootstrap Project: Agent Kernel Integration Process

**Process Owner:** Agent Kernel
**Purpose:** Integrate Agent Kernel documentation into a project, eliminate duplication, fix broken links, and establish clear content ownership.
**Audience:** AI agents performing project documentation integration
**Prerequisites:** Agent Kernel (docs/system-prompts/) is present in project

---

## Overview

This process guides you through bootstrapping the Agent Kernel integration into a project. The process works in two scenarios:

### Scenario 1: Initial Bootstrap (New Project)
You're setting up a project for the first time with Agent Kernel.
- Goal: Generate AGENTS.md, create missing documentation, establish structure
- Focus: Phases 1, 3 (create missing files), 4 (light consolidation), 5-7
- Duration: 15-20 file operations

### Scenario 2: Bootstrap After System-Prompts Updates
Agent Kernel documentation in docs/system-prompts/ has changed (new sections, updated workflows, etc.). You need to re-validate and re-connect the project.
- Goal: Re-sync AGENTS.md, verify links, remove redundant project documentation
- Focus: Phases 1 (re-sync), 2 (scan for breakage), 4 (aggressive redundancy cleanup), 5-7
- Duration: 5-15 file operations

**Both scenarios follow the same 7-phase process; the emphasis just shifts.**

---

## Process Stability: Preventing Flip-Flopping

**Critical for Scenario 2 (Updates):** When re-running bootstrap after system-prompts updates, follow these stability guidelines to prevent unnecessary changes that cause flip-flopping.

### What NOT to Change

**Cosmetic variations that should be left alone:**
- Whitespace differences (extra blank lines, indentation variations)
- Timestamp formatting ("Last Updated: YYYY-MM-DD" vs "Last Updated: Month Day, Year")
- Comment placement or slight wording differences that preserve meaning
- Cross-reference header phrasing (if links are correct and content is clear)
- Minor formatting variations in lists, tables, or code blocks
- Order of "See Also" links (if all links are valid)

### What SHOULD Be Changed

**Only modify when you find:**
- **Broken links** - Links that 404 or point to moved/renamed files
- **Missing files** - Referenced documentation that doesn't exist
- **Factual errors** - Incorrect statements, outdated API references, wrong file paths
- **Structural problems** - Missing sections, malformed navigation, duplicated content
- **Maintenance burden** - Significant duplication between project docs and Agent Kernel

### Stability Test: Will It Survive?

Before making ANY change during Scenario 2 (Updates):

1. **Ask:** Will this change survive the next `bootstrap.py --commit` run?
2. **If NO:** Either modify `bootstrap.py` to preserve it, or skip the change
3. **If UNSURE:** It's probably cosmetic - leave it alone

**Example: Cross-reference headers**
- ❌ **Bad:** Manually add cross-reference header to AGENTS.md (bootstrap.py will strip it)
- ✅ **Good:** Modify bootstrap.py to auto-inject cross-references (now idempotent)

### Philosophy: Idempotency Over Perfection

**The goal of bootstrap is idempotency, not perfection.**

- Running bootstrap twice should produce identical results
- Small formatting variations are acceptable if they prevent churn
- Agent Kernel and project docs may have different styles - that's OK
- Focus on **broken functionality**, not **aesthetic consistency**

**Rationale:** Flip-flopping wastes time and creates noisy commit history. A stable, slightly imperfect system is better than an unstable, perfect one.

---

## Process Steps

You will:

1. Verify current state and identify issues
2. Run bootstrap.py to generate/update AGENTS.md
3. Analyze documentation for gaps and broken links
4. Fix issues and establish proper structure
5. Consolidate duplication and remove redundancy
6. Verify cross-references and integrity
7. Validate and document completion

**Success Criteria (Both Scenarios):**
- 0 critical TODOs remaining
- 0 broken links in documentation
- Clear separation: generic content in system-prompts/, project-specific in docs/
- Bidirectional cross-references working
- All documentation discoverable from README.md
- Document integrity scan passes

---

## Critical Boundary: What This Process Does and Doesn't Do

**✅ THIS PROCESS MODIFIES:**
- `AGENTS.md` - Project's main agent instructions
- `README.md` - Project's main documentation
- `[TOOL].md` - Tool-specific entry files (`CLAUDE.md`, `.aider.md`, etc.)
- `docs/*.md` - Project-specific documentation files
- `dev_notes/` - Change logs and planning documents

**❌ THIS PROCESS DOES NOT MODIFY:**
- `docs/system-prompts/` - The Agent Kernel (read-only)
- Any files within system-prompts/ directory

**Why:** `docs/system-prompts/` is the Agent Kernel, a separate, portable system. The bootstrap process reads FROM it, never writes TO it. If you need to change system-prompts files, do so explicitly in a separate operation (not as part of bootstrap).

---

## Phase 0: Pre-Bootstrap Analysis

**Applies to:** Both scenarios
**Goal:** Understand current state before running bootstrap

**For Initial Bootstrap:** Establishes baseline of what exists
**For Updates:** Identifies what changed and what might be broken

### Step 0.1: Verify Agent Kernel is Present

```bash
# Check that system-prompts directory exists
ls -la docs/system-prompts/

# Expected: Directory with principles/, languages/, templates/, workflows/, tools/
```

**If missing:** The Agent Kernel must be copied to `docs/system-prompts/` before proceeding.

### Step 0.2: Survey Existing Documentation

```bash
# List all markdown files in project
find . -name "*.md" -type f ! -path "./venv/*" ! -path "./node_modules/*" | sort
```

**Make note of:**
- Does AGENTS.md already exist? (will be overwritten by bootstrap)
- What files exist in docs/? (potential duplication targets)
- Are there tool-specific entry files? (`CLAUDE.md`, `.aider.md`, etc.)
- Is there a definition-of-done.md? (likely needs consolidation)

### Step 0.3: Check for Obvious Issues

```bash
# Look for placeholder TODOs
grep -r "TODO:" --include="*.md" . | grep -v "node_modules" | grep -v "venv"

# Count lines in key files (check for duplication)
wc -l docs/definition-of-done.md 2>/dev/null || echo "File doesn't exist yet"
wc -l AGENTS.md 2>/dev/null || echo "File doesn't exist yet"
```

**Record findings:** You'll use this baseline to measure success.

---

## Phase 1: Run Bootstrap

**Applies to:** Both scenarios
**Goal:** Generate/update AGENTS.md and identify what needs integration

**For Initial Bootstrap:** Creates AGENTS.md from scratch
**For Updates:** Re-syncs AGENTS.md with updated system-prompts sections

### Step 1.1: Analyze Mode (Dry Run)

```bash
cd /path/to/project
python3 docs/system-prompts/bootstrap.py --analyze
```

**Expected Output:**
```
Project language: python  # or detected language
Project root: /path/to/project
AGENTS.md path: /path/to/project/AGENTS.md

Sections to sync (3):
  - CORE-WORKFLOW: ✗ Not found in AGENTS.md, ✓ Exists in system-prompts
  - PRINCIPLES: ✗ Not found in AGENTS.md, ✓ Exists in system-prompts
  - PYTHON-DOD: ✗ Not found in AGENTS.md, ✓ Exists in system-prompts
```

**Interpretation:**
- If AGENTS.md doesn't exist: All sections will be added
- If AGENTS.md exists: Sections marked with `<!-- SECTION: NAME -->` tags will be synchronized

### Step 1.2: Generate AGENTS.md

```bash
python3 docs/system-prompts/bootstrap.py --commit
```

**Expected Output:**
```
Sections synchronized:
  ✓ CORE-WORKFLOW written to AGENTS.md
  ✓ PRINCIPLES written to AGENTS.md
  ✓ PYTHON-DOD written to AGENTS.md

AGENTS.md has been updated successfully.
```

**Verify:**
```bash
# Check AGENTS.md was created/updated
ls -lh AGENTS.md

# Verify sections are marked
grep -c "<!-- SECTION:" AGENTS.md
# Expected: 3 or more (depending on language)

# Preview structure
head -50 AGENTS.md
```

### Step 1.3: Survey Generated Content

Read the generated AGENTS.md:

```bash
# Read the full file
cat AGENTS.md
```

**Check for:**
- **Line 1-10:** Does it have a project title/introduction, or just "TODO: describe whatever here"?
- **Navigation links:** Are there links to docs/ that don't exist yet?
- **Section markers:** `<!-- SECTION: NAME -->` and `<!-- END-SECTION -->` tags present?
- **Content duplication:** Is content from system-prompts repeated verbatim?

**Common Issues Found:**
1. Generic title: "# Project Agents" without project name
2. TODO placeholders in introduction
3. Broken links to docs/architecture.md, docs/templates.md, docs/workflows.md
4. No cross-references to system-prompts source

---

## Phase 2: Comprehensive Documentation Scan

**Applies to:** Both scenarios (but different focus)
**Goal:** Identify integration gaps, broken links, and duplication

**For Initial Bootstrap:** Establishes baseline of documentation quality
**For Updates:** Identifies what broke due to system-prompts changes (new section names, moved files, etc.)

### Step 2.1: Find All Markdown Files

```bash
# Create inventory of all .md files
find . -name "*.md" -type f \
  ! -path "./venv/*" \
  ! -path "./node_modules/*" \
  ! -path "./.git/*" \
  ! -path "./build/*" \
  ! -path "./dist/*" \
  > /tmp/md_files.txt

# Count total files
wc -l /tmp/md_files.txt
```

**Categorize files:**
- **Root entry points:** AGENTS.md, README.md, `CONTRIBUTING.md`, CLAUDE.md, etc.
- **docs/ files:** Project documentation
- **docs/system-prompts/:** Agent Kernel (don't modify these)
- **dev_notes/:** Runtime documentation (ok as-is)

### Step 2.2: Scan for Critical TODOs

```bash
# Find all TODO placeholders in documentation
grep -rn "TODO:" --include="*.md" \
  --exclude-dir=venv \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  . | grep -v "# TODO" | grep -v "- TODO"
```

**Focus on:**
- TODOs in AGENTS.md (line 1-50, likely in introduction)
- TODOs in docs/workflows.md
- TODOs in docs/definition-of-done.md
- TODOs marking missing content sections

**Record each TODO with:**
- File path
- Line number
- Context (what needs to be done)

### Step 2.3: Scan for Broken Links

```bash
# Run document integrity scan
python3 docs/system-prompts/docscan.py
```

**Expected Output:**
```
================================================================================
DOCUMENT INTEGRITY SCAN
================================================================================

### Checking for Broken Links...
### Checking for Problematic Back-References...
### Checking Reference Formatting...
...

### VIOLATIONS FOUND

❌ Errors (X):
  file.md
    → Broken link: target.md
       Target: path/to/target.md

⚠️  Warnings (Y):
  ...
```

**Focus on Errors (❌), ignore most Warnings (⚠️):**
- **Critical:** Broken links in AGENTS.md, README.md, docs/definition-of-done.md
- **Critical:** Missing referenced files (docs/architecture.md, docs/templates.md, etc.)
- **Non-critical:** Style warnings about formatting, naming conventions

**Record broken links:**
- Source file
- Target file referenced
- Whether target exists (create vs fix link)

### Step 2.4: Identify Duplication

**Check for duplicated content between project docs and Agent Kernel:**

```bash
# Check if definition-of-done.md duplicates Agent Kernel
if [ -f docs/definition-of-done.md ]; then
  echo "docs/definition-of-done.md exists ($(wc -l < docs/definition-of-done.md) lines)"

  # Check for duplication markers
  grep -q "Agent Kernel" docs/definition-of-done.md && echo "✓ References Agent Kernel" || echo "✗ No Agent Kernel reference (likely duplicated)"
fi

# Check for other common duplication targets
for file in docs/workflows.md docs/contributing.md docs/development.md; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    echo "$file: $lines lines"
    [ $lines -gt 500 ] && echo "  ⚠️  Large file, check for duplication"
  fi
done
```

**Common duplication patterns:**
- **docs/definition-of-done.md:** 400+ lines duplicating system-prompts/principles/definition-of-done.md and system-prompts/languages/{lang}/definition-of-done.md
- **docs/workflows.md:** Generic workflow content already in system-prompts/workflows/
- **docs/contributing.md:** Generic Python/language style already in system-prompts/languages/{lang}/
- **Tool-specific guides:** Content already in system-prompts/tools/

**Record duplication:**
- File path
- Line count
- What content is duplicated (generic vs project-specific)
- Whether it should become a "thin wrapper" referencing Agent Kernel

### Step 2.5: Create Integration Gap Summary

Consolidate findings into a structured summary:

```markdown
# Integration Gap Summary

## Critical TODOs (X found)
1. AGENTS.md:3 - "TODO: describe whatever here"
2. docs/workflows.md:3 - Entire file is placeholder
...

## Broken Links (Y found)
1. AGENTS.md → docs/architecture.md (file doesn't exist)
2. AGENTS.md → docs/templates.md (file doesn't exist)
...

## Major Duplication (Z files)
1. docs/definition-of-done.md (569 lines) - duplicates Agent Kernel DoD
2. docs/workflows.md (400 lines) - duplicates Agent Kernel workflows
...

## Missing Core Files (files referenced but don't exist)
1. docs/architecture.md - Referenced 10 times
2. docs/templates.md - Referenced 14 times
...
```

**Decision Point:** If you find 10+ critical issues, create a project plan before proceeding. If fewer than 10, continue with inline fixes.

---

## Phase 3: Fix Critical TODOs and Create Missing Core Files

**Applies to:** Primarily Initial Bootstrap (light work for Updates)
**Goal:** Resolve placeholders and establish proper document architecture

**For Initial Bootstrap:** Create all missing files (architecture.md, implementation-reference.md, templates.md, etc.)
**For Updates:** Files likely exist; just verify they still make sense and aren't out of date

### Step 3.1: Fix AGENTS.md Introduction

**Location:** AGENTS.md, typically line 1-10

**Find:**
```markdown
# Project Agents

TODO: describe whatever here
```

**Replace with:**
```markdown
# Project Agents - [PROJECT NAME]

This file defines the mandatory workflow for AI agents working on the [PROJECT NAME] project.

**Quick Navigation:**
- [Definition of Done](docs/definition-of-done.md) - Quality standards
- [Architecture](docs/architecture.md) - System design
- [Implementation Reference](docs/implementation-reference.md) - Patterns
- [Workflows](docs/workflows.md) - Development process
- [Templates](docs/templates.md) - Planning documents
```

**Variables to fill:**
- `[PROJECT NAME]`: Get from README.md or pyproject.toml/package.json

### Step 3.2: Create docs/templates.md

**Create new file:** `docs/templates.md`

**Template content:**

```markdown
# Planning Document Templates

This document provides templates for planning documents used in the [PROJECT NAME] project.

## Agent Kernel Templates

The project follows the Agent Kernel template system. For complete template documentation, see:

- **[Template Structure Guide](system-prompts/templates/structure.md)** - Standard templates for project plans, architecture decisions, and investigation reports

## Project-Specific Conventions

### Development Notes Directory

Development notes and session transcripts are stored in `dev_notes/` using the format:

\```
`dev_notes/subdir/YYYY-MM-DD_HH-MM-SS_description.md`
\```

### Planning Documents

When creating project plans, follow the structure from the Agent Kernel:

1. **Executive Summary** - Overview and objectives
2. **Issues Summary** - Problems being addressed
3. **Implementation Phases** - Step-by-step breakdown
4. **Critical Files Summary** - Files to create, modify, or delete
5. **Verification Steps** - Testing and validation
6. **Success Criteria** - Measurable outcomes
7. **Risk Mitigation** - Known risks and mitigation strategies

### [PROJECT-SPECIFIC SECTIONS]

Add project-specific template sections here. Examples:
- Tool development plans
- API integration plans
- Architecture decision records

## See Also

- [AGENTS.md](../AGENTS.md) - Core workflow for AI agents
- [Definition of Done](definition-of-done.md) - Quality standards
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Implementation patterns

---
Last Updated: YYYY-MM-DD
```

**Fill in:**
- `[PROJECT NAME]`
- `[PROJECT-SPECIFIC SECTIONS]` based on project type
- Date timestamp

### Step 3.3: Create docs/architecture.md

**Create new file:** `docs/architecture.md`

**Approach:**
1. **If existing architecture docs exist** (e.g., docs/development.md with architecture section):
   - Extract architecture content from existing files
   - Consolidate into single architecture.md
   - Add proper structure and cross-references

2. **If no architecture docs exist:**
   - Create skeleton architecture document
   - Document high-level system design
   - Add placeholders for project-specific sections

**Skeleton template:**

```markdown
# System Architecture

This document describes the architecture of [PROJECT NAME].

## High-Level Architecture

[Describe system architecture - components, layers, data flow]

\```
┌─────────────────────────────────────┐
│         Component Layer 1           │
├─────────────────────────────────────┤
│         Component Layer 2           │
├─────────────────────────────────────┤
│         Component Layer 3           │
└─────────────────────────────────────┘
\```

## Project Structure

\```
project-root/
├── src/
│   └── [main code]
├── tests/
│   └── [tests]
├── docs/
│   └── [documentation]
└── [other directories]
\```

## [PROJECT-SPECIFIC SECTIONS]

Add project-specific architecture documentation:
- Key design patterns
- Technology stack
- External integrations
- Security architecture
- Performance considerations

## Agent Kernel Integration

This architecture extends the Agent Kernel reference architecture. See:

- [Agent Kernel Reference Architecture](system-prompts/reference-architecture.md) (if exists)

## See Also

- [AGENTS.md](../AGENTS.md) - Core workflow
- [Definition of Done](definition-of-done.md) - Quality standards
- [Implementation Reference](implementation-reference.md) - Implementation patterns
- [Workflows](workflows.md) - Development workflows

---
Last Updated: YYYY-MM-DD
```

**Content sources:**
- Existing docs/development.md, `docs/overview.md`
- README.md (often has architecture section)
- Source code comments
- Project structure analysis

### Step 3.4: Create docs/implementation-reference.md

**Create new file:** `docs/implementation-reference.md`

**Purpose:** Practical implementation patterns and reference implementations

**Template content:**

```markdown
# Implementation Reference

This document provides practical implementation patterns and reference implementations for [PROJECT NAME].

## Quick Reference

- **[Common Pattern 1]**: See [Section](#pattern-1)
- **[Common Pattern 2]**: See [Section](#pattern-2)
- **[Common Pattern 3]**: See [Section](#pattern-3)

## [PROJECT-SPECIFIC PATTERNS]

Add project-specific implementation patterns. Examples:

### Pattern 1: [Pattern Name]

**Use Case:** When to use this pattern

**Implementation:**

\```[language]
# Code example showing the pattern
\```

**Key Points:**
- Important detail 1
- Important detail 2

### Pattern 2: [Pattern Name]

[Similar structure]

## Testing Patterns

### Unit Test Pattern

\```[language]
# Unit test example
\```

### Integration Test Pattern

\```[language]
# Integration test example
\```

## Configuration Patterns

[Project-specific configuration patterns]

## Error Handling Patterns

[Project-specific error handling]

## See Also

- [Architecture](architecture.md) - System design
- [Workflows](workflows.md) - Development workflows
- [Definition of Done](definition-of-done.md) - Quality standards

---
Last Updated: YYYY-MM-DD
```

**Content sources:**
- Existing docs/development.md, `docs/mcp-development-guide.md`, etc.
- Extract common patterns from codebase
- Test files (for testing patterns)

### Step 3.5: Fix or Create docs/workflows.md

**Check current state:**
```bash
cat docs/workflows.md
```

**If file is just "TODO" placeholder:**

**Replace with:**

```markdown
# Project Workflows

This document describes development workflows specific to [PROJECT NAME].

## Core Agent Workflow

All AI agents working on this project must follow the **A-E workflow** defined in [AGENTS.md](../AGENTS.md):

- **A: Analyze** - Understand the request and declare intent
- **B: Build** - Create project plan
- **C: Code** - Implement the plan
- **D: Document** - Update documentation
- **E: Evaluate** - Verify against Definition of Done

For complete workflow documentation, see the [Agent Kernel Workflows](system-prompts/workflows/).

## [PROJECT-SPECIFIC WORKFLOWS]

Add project-specific development workflows. Examples:

### Workflow 1: [Workflow Name]

**When to use:** [Description]

**Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Testing Workflow

\```bash
# Run tests
[test command]
\```

### Deployment Workflow

\```bash
# Deploy steps
[deploy commands]
\```

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Definition of Done](definition-of-done.md) - Quality checklist
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Code patterns
- [Agent Kernel Workflows](system-prompts/workflows/) - Complete workflow documentation

---
Last Updated: YYYY-MM-DD
```

**Fill in project-specific workflows based on:**
- Project type (web app, API, CLI tool, library, etc.)
- Technology stack
- Development practices
- Testing approach

### Step 3.6: Commit Phase 3 Changes

```bash
git add AGENTS.md docs/templates.md docs/architecture.md docs/implementation-reference.md docs/workflows.md

git commit -m "docs: Phase 3 - fix critical TODOs and create missing core files

- Fixed AGENTS.md introduction with project name and navigation
- Created docs/templates.md with template guidelines
- Created docs/architecture.md with system architecture
- Created docs/implementation-reference.md with implementation patterns
- Fixed docs/workflows.md with workflow documentation

All critical TODOs resolved and broken link targets created.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 4: Consolidate Duplicated Content & Remove Redundancy

**Applies to:** Both scenarios (but different focus)
**Goal:** Reduce duplication by establishing clear content ownership and removing redundant content

**SCOPE: Project-specific documentation ONLY** (docs/*.md, definition-of-done.md, contributing.md, etc.)
**DO NOT modify docs/system-prompts/** - The Agent Kernel is read-only to this process.

**For Initial Bootstrap:** Light consolidation (project docs are usually minimal)
**For Updates:** AGGRESSIVE - System-prompts has evolved, so project-specific docs likely have content now covered by system-prompts. Remove redundancy aggressively from project docs only.

### Step 4.1: Analyze docs/definition-of-done.md

**Check if file exists and size:**

```bash
if [ -f docs/definition-of-done.md ]; then
  lines=$(wc -l < docs/definition-of-done.md)
  echo "docs/definition-of-done.md: $lines lines"

  # Check if it references Agent Kernel
  if grep -q "system-prompts" docs/definition-of-done.md; then
    echo "✓ Already references Agent Kernel (probably ok)"
  else
    echo "✗ Doesn't reference Agent Kernel (needs transformation)"
  fi
fi
```

**If file is 300+ lines and doesn't reference Agent Kernel:**

This is the most common duplication issue. The file likely duplicates content from:
- `docs/system-prompts/principles/definition-of-done.md` (universal requirements)
- `docs/system-prompts/languages/[lang]/definition-of-done.md` (language-specific requirements)

**Approach: Transform to Thin Wrapper**

1. **Read the existing file completely** to identify project-specific content
2. **Extract truly project-specific sections** (not covered by Agent Kernel)
3. **Create new version as thin wrapper:**

```markdown
# Definition of Done - [PROJECT NAME]

**Referenced from:** [AGENTS.md](../AGENTS.md)

This document defines the "Done" criteria for [PROJECT NAME]. It extends the universal Agent Kernel Definition of Done with project-specific requirements.

## Agent Kernel Definition of Done

This project follows the Agent Kernel Definition of Done. **You MUST review these documents first:**

### Universal Requirements

See **[Universal Definition of Done](system-prompts/principles/definition-of-done.md)** for:
- Plan vs Reality Protocol
- Verification as Data
- Codebase State Integrity
- Agent Handoff
- Status tracking in project plans
- dev_notes/ change documentation requirements

### [Language] Requirements

See **[[Language] Definition of Done](system-prompts/languages/[lang]/definition-of-done.md)** for:
- [Language] environment & dependencies
- Testing requirements ([test framework])
- Code quality standards
- File organization
- Coverage requirements

## Project-Specific Extensions

The following requirements are specific to [PROJECT NAME] and extend the Agent Kernel DoD:

### 1. [Project-Specific Requirement Category 1]

**Mandatory Checks:**
- [ ] [Specific check]
- [ ] [Specific check]

**Example verification:**
\```bash
# Verification command
\```

### 2. [Project-Specific Requirement Category 2]

[Similar structure]

## Pre-Commit Checklist

Before committing, verify:

**Code Quality:**
- [ ] [Language] formatting applied: `[format command]`
- [ ] Linting passes: `[lint command]`
- [ ] Type hints present (if applicable)
- [ ] Docstrings present

**Testing:**
- [ ] All unit tests pass: `[test command]`
- [ ] Integration tests pass (or documented why skipped)
- [ ] Coverage ≥ [X]%: `[coverage command]`

**[Project-Specific Checks]:**
- [ ] [Specific check 1]
- [ ] [Specific check 2]

**Documentation:**
- [ ] README updated for new features
- [ ] Architecture docs updated for design changes
- [ ] Implementation reference updated for new patterns

**Commit:**
- [ ] Commit message follows format: `type: description`
- [ ] Co-Authored-By trailer included
- [ ] Changes reviewed
- [ ] Human approval received (for interactive workflows)

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Universal DoD](system-prompts/principles/definition-of-done.md) - Agent Kernel universal requirements
- [[Lang] DoD](system-prompts/languages/[lang]/definition-of-done.md) - Agent Kernel language requirements
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Code patterns
- [Workflows](workflows.md) - Development workflows

---
Last Updated: YYYY-MM-DD
```

**How to extract project-specific content:**
- Look for references to project-specific tools, frameworks, or technologies
- Look for project-specific file paths, commands, or configurations
- Look for domain-specific quality requirements
- Keep only what's NOT already covered by Agent Kernel

**Target reduction:** 50-80% fewer lines

### Step 4.2: Review docs/contributing.md

**Check for generic content that should reference Agent Kernel:**

```bash
# Look for generic Python/language style guidelines
grep -A 10 "Code Style" docs/contributing.md
grep -A 10 "PEP 8" docs/contributing.md
```

**If file contains generic language style guide (20+ lines):**

**Refactor to reference Agent Kernel:**

Find sections like:
```markdown
### Code Style

We use:
- black for formatting
- flake8 for linting
- Follow PEP 8
- Use type hints
- etc.
```

Replace with:
```markdown
### Code Style

This project follows the **Agent Kernel** code quality standards. See:

- **[[Language] Definition of Done](system-prompts/languages/[lang]/definition-of-done.md)** - Code quality standards
- **[Definition of Done](definition-of-done.md)** - Project-specific requirements

**Automated Tools:**

- **[formatter]** - Code formatting
- **[linter]** - Linting and quick fixes

Run code quality checks before committing:

\```bash
# Check code
[check commands]

# Auto-fix issues
[fix commands]
\```

**Project-Specific Patterns:**

[Only project-specific coding patterns, not generic language style]
```

**Keep:**
- Project-specific contribution workflow
- PR process
- Development setup
- Project-specific patterns

**Remove/Reference:**
- Generic language style (defer to Agent Kernel)
- Generic testing guidelines (defer to Agent Kernel)
- Generic commit message format (defer to Agent Kernel)

### Step 4.3: Scan for Other Large Files

```bash
# Find large markdown files in docs/ (excluding system-prompts)
find docs -name "*.md" -type f ! -path "*/system-prompts/*" -exec wc -l {} \; | sort -rn | head -10
```

**Review any files over 500 lines:**
- Does it contain content already in Agent Kernel?
- Can it reference Agent Kernel instead of duplicating?
- Is it tool-specific content that's already in system-prompts/tools/?

**Common duplication targets:**
- Tool-specific workflow files (e.g., `docs/claude-code-workflows.md`) - often duplicates `system-prompts/tools/claude-code.md`
- Generic development guides - may duplicate language-specific DoD
- Generic testing guides - may duplicate language-specific DoD

**For duplicated tool guides:**
1. Extract project-specific examples only
2. Move to `docs/examples/[tool]-examples.md`
3. Reference `system-prompts/tools/[tool].md` for generic content
4. Delete the duplicated file

### Step 4.4: Commit Phase 4 Changes

```bash
git add docs/definition-of-done.md docs/contributing.md [other modified files]

git commit -m "docs: Phase 4 - consolidate duplicated content

- Transformed docs/definition-of-done.md from [OLD_LINES] lines to [NEW_LINES] line wrapper ([PERCENT]% reduction)
- Refactored docs/contributing.md to reference Agent Kernel for generic style
- [Other changes]

Files transformed to use Agent Kernel as single source of truth.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 5: Establish Clear Cross-References

**Applies to:** Both scenarios (but different focus)
**Goal:** Create bidirectional links between AGENTS.md, docs/, and system-prompts/

**For Initial Bootstrap:** Establish all cross-references from scratch
**For Updates:** Verify existing cross-references still work; update any broken ones due to system-prompts structure changes

### Step 5.1: Verify Cross-References in AGENTS.md

**Cross-references are automatically injected by bootstrap.py** as of 2026-01-29. You should verify they are present, but NOT manually add them.

**Verify the Definition of Done section has cross-references:**

```bash
# Find where DoD section starts
grep -n "<!-- SECTION: PRINCIPLES -->" AGENTS.md

# Check that cross-reference header exists
grep -A 10 "<!-- SECTION: PRINCIPLES -->" AGENTS.md | grep -q "Agent Kernel" && echo "✓ Cross-references present" || echo "❌ Missing cross-references"
```

**Expected format (automatically injected by bootstrap.py):**

```markdown
<!-- SECTION: PRINCIPLES -->
# Definition of Done: Universal Principles

This section is maintained by the Agent Kernel. For the complete, authoritative version, see:
- [Universal DoD](docs/system-prompts/principles/definition-of-done.md) - Agent Kernel universal requirements
- [[Language] DoD](docs/system-prompts/languages/[lang]/definition-of-done.md) - Agent Kernel language requirements

**Project-specific extensions:** See [docs/definition-of-done.md](docs/definition-of-done.md)

---

**MANDATORY:** No task is considered "Done" until all applicable criteria in this document are met...
[rest of Agent Kernel content]
```

**If cross-references are missing:**
- Re-run `python3 docs/system-prompts/bootstrap.py --commit` to regenerate with cross-references
- DO NOT manually add them - they will be stripped on next bootstrap run

**This establishes:**
- Clear source attribution (Agent Kernel)
- Link to authoritative versions
- Link to project-specific extensions
- **Idempotent process** - same input always produces same output

### Step 5.2: Enhance Tool Entry Files

**If project has tool-specific entry files** (`CLAUDE.md`, `.aider.md`, etc.):

**Add System Architecture section:**

```markdown
## System Architecture

- **Agent Kernel:** [docs/system-prompts/README.md](docs/system-prompts/README.md)
- **Project Architecture:** [docs/architecture.md](docs/architecture.md)
- **Implementation Patterns:** [docs/implementation-reference.md](docs/implementation-reference.md)
- **Development Workflows:** [docs/workflows.md](docs/workflows.md)
- **Code Examples:** [docs/examples/](docs/examples/) (if exists)
```

**Add timestamp to bottom:**
```markdown
---
Last Updated: YYYY-MM-DD
```

### Step 5.3: Update docs/system-prompts/README.md

**Add Project Integration section at the end (before ## Version):**

```markdown
## Project Integration

This Agent Kernel is integrated into the **[PROJECT NAME]** project with the following extensions:

### Entry Points

- **[AGENTS.md](../../AGENTS.md)** - Main agent instructions combining Agent Kernel workflows with project-specific requirements
- **[docs/definition-of-done.md](../definition-of-done.md)** - Project-specific DoD extending Agent Kernel universal and language DoD
- **[docs/workflows.md](../workflows.md)** - Project-specific development workflows

### Project-Specific Extensions

The project adds domain-specific requirements for:

**[Project Type]:**
- [Key extension area 1]
- [Key extension area 2]
- [Key extension area 3]

**[Technology Stack]:**
- [Key extension area 1]
- [Key extension area 2]

See [docs/definition-of-done.md](../definition-of-done.md) for complete project-specific requirements.

### Sync Status

- **Bootstrap sync:** Completed YYYY-MM-DD
- **Last integration update:** YYYY-MM-DD
- **Sections synchronized:** CORE-WORKFLOW, PRINCIPLES, [LANGUAGE]-DOD

### Documentation Structure

\```
project-root/
├── AGENTS.md                           # Combined: Agent Kernel + project extensions
├── [TOOL].md                           # Tool-specific instructions (if exists)
├── docs/
│   ├── definition-of-done.md          # Project DoD (extends Agent Kernel)
│   ├── architecture.md                # Project architecture
│   ├── implementation-reference.md    # Implementation patterns
│   ├── workflows.md                   # Project workflows (extends Agent Kernel)
│   ├── examples/                      # Project-specific examples (if exists)
│   └── system-prompts/                # Agent Kernel (this directory)
│       ├── README.md                  # This file
│       ├── principles/                # Universal principles
│       ├── languages/                 # Language-specific standards
│       ├── templates/                 # Document templates
│       ├── workflows/                 # Workflow documentation
│       └── tools/                     # Tool-specific guides
└── dev_notes/                         # Runtime documentation
    ├── specs/                         # Specifications
    ├── project_plans/                 # Project plans
    └── changes/                       # Change documentation
\```
```

**Fill in:**
- `[PROJECT NAME]`
- `[Project Type]` and extension areas
- `[LANGUAGE]`
- Sync dates

### Step 5.4: Create docs/README.md (Documentation Hub)

**Create comprehensive navigation document:**

```markdown
# Documentation Index

Complete documentation for [PROJECT NAME].

## Quick Start

**For AI Agents:**
- Start with **[AGENTS.md](../AGENTS.md)** - Mandatory workflow and unbreakable rules
- Check **[Definition of Done](definition-of-done.md)** - Quality standards

**For Developers:**
- Read **[README.md](../README.md)** - Project overview
- See **[Contributing](contributing.md)** - How to contribute
- Review **[Architecture](architecture.md)** - System design

## For AI Agents

### Core Workflow
- **[AGENTS.md](../AGENTS.md)** - Mandatory A-E workflow
- **[Definition of Done](definition-of-done.md)** - Complete quality checklist
- **[Workflows](workflows.md)** - Development workflows
- **[Templates](templates.md)** - Planning document templates

### Tool-Specific Guides
- **[Tool 1 Guide](system-prompts/tools/[tool1].md)** - [Tool 1] documentation
- **[Tool 2 Guide](system-prompts/tools/[tool2].md)** - [Tool 2] documentation

## Architecture & Design

- **[Architecture](architecture.md)** - System architecture
- **[Implementation Reference](implementation-reference.md)** - Implementation patterns
- **[Development Guide](development.md)** - Development practices (if exists)

## [PROJECT-SPECIFIC SECTIONS]

Add project-specific documentation categories. Examples:

### API Documentation
- API reference
- Integration guides

### Examples
- Example 1
- Example 2

## System Prompts (Agent Kernel)

The Agent Kernel provides reusable workflows and standards:

- **[Agent Kernel README](system-prompts/README.md)** - Complete Agent Kernel documentation
- **[Universal DoD](system-prompts/principles/definition-of-done.md)** - Universal Definition of Done
- **[[Language] DoD](system-prompts/languages/[lang]/definition-of-done.md)** - Language-specific standards
- **[Templates](system-prompts/templates/structure.md)** - Document structure templates
- **[Workflows](system-prompts/workflows/README.md)** - Workflow documentation

## Navigation Tips

### Finding Information

**"How do I [common task 1]?"**
→ [Link to relevant doc]

**"How do I [common task 2]?"**
→ [Link to relevant doc]

**"What are the quality standards?"**
→ [Definition of Done](definition-of-done.md)

**"What is the system architecture?"**
→ [Architecture](architecture.md)

### For First-Time Contributors

1. Read [README.md](../README.md) - Project overview
2. Review [Architecture](architecture.md) - Understand the system
3. Read [Contributing](contributing.md) - Code standards
4. Check project examples (if exist)
5. Review [Definition of Done](definition-of-done.md) - Quality checklist

### For AI Agents Starting Work

1. Read [AGENTS.md](../AGENTS.md) - Mandatory workflow
2. Check [Definition of Done](definition-of-done.md) - Quality standards
3. Review [Workflows](workflows.md) - Development processes
4. Use [Templates](templates.md) - For planning documents

## See Also

- **[Project README](../README.md)** - Main project documentation
- **[AGENTS.md](../AGENTS.md)** - Agent workflow and rules

---
Last Updated: YYYY-MM-DD
```

**Fill in:**
- `[PROJECT NAME]`
- `[PROJECT-SPECIFIC SECTIONS]`
- Common task navigation links
- Tool-specific guides

### Step 5.5: Update Main README.md

**Add Documentation section near the end (before ## License or at very end):**

```markdown
## Documentation

### For AI Agents
- **[AGENTS.md](AGENTS.md)** - Mandatory workflow for AI agents
- **[Definition of Done](docs/definition-of-done.md)** - Quality standards
- **[Workflows](docs/workflows.md)** - Development workflows

### For Developers
- **[Documentation Index](docs/README.md)** - Complete documentation navigation
- **[Architecture](docs/architecture.md)** - System architecture
- **[Implementation Reference](docs/implementation-reference.md)** - Code patterns
- **[Contributing](docs/contributing.md)** - Contribution guidelines

### Examples (if exist)
- **[Example 1](docs/examples/example1.md)** - Description
- **[Example 2](docs/examples/example2.md)** - Description

### Guides
- **[Development Guide](docs/development.md)** - Development practices (if exists)
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues (if exists)
```

### Step 5.6: Commit Phase 5 Changes

```bash
git add AGENTS.md [TOOL].md docs/README.md docs/system-prompts/README.md README.md

git commit -m "docs: Phase 5 - establish clear cross-references

- Updated AGENTS.md with cross-references to Agent Kernel DoD
- Enhanced [TOOL].md with System Architecture section
- Updated docs/system-prompts/README.md with Project Integration section
- Created docs/README.md as comprehensive documentation navigation hub
- Updated README.md with Documentation section

All documentation now has bidirectional links:
AGENTS.md ↔ docs/ ↔ system-prompts/

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 6: Run Integrity Processes

**Applies to:** Both scenarios
**Goal:** Ensure all documentation is consistent and discoverable

**For Initial Bootstrap:** First full integrity check of complete documentation
**For Updates:** Verify no breakage from system-prompts changes

### Step 6.1: Run Document Integrity Scan

```bash
python3 docs/system-prompts/docscan.py
```

**Expected Output:**
```
### VIOLATIONS FOUND

❌ Errors (0):
  [none]

⚠️  Warnings (X):
  [various style warnings - usually safe to ignore]
```

**Focus on Errors (❌):**
- **Broken links** - Fix immediately
- **Missing referenced files** - Create or fix reference

**Warnings (⚠️) you can usually ignore:**
- "Back-reference to project file without conditional marking" - This is expected for project integration
- "Plain-text file reference should use backticks" - Style issue, non-critical
- "Entry file exceeds 20 lines" - Fine if file is well-organized
- "File doesn't follow `lowercase-kebab.md` convention" - Entry files like AGENTS.md intentionally use UPPERCASE

**If errors found:**

1. **Broken link to missing file:**
   ```bash
   # Create the missing file with minimal content
   touch docs/missing-file.md
   echo "# [Title]" > docs/missing-file.md
   echo "[Add content]" >> docs/missing-file.md
   ```

2. **Broken link with wrong path:**
   ```bash
   # Fix the link in the source file
   # Use Edit tool to correct the path
   ```

3. **Fix and re-run:**
   ```bash
   # After fixes
   python3 docs/system-prompts/docscan.py
   # Expected: 0 errors
   ```

### Step 6.2: Run Bootstrap Analysis

```bash
python3 docs/system-prompts/bootstrap.py --analyze
```

**Expected Output:**
```
Sections to sync (3):
  - CORE-WORKFLOW: ✓ Found in AGENTS.md, ✓ Exists in system-prompts
  - PRINCIPLES: ✓ Found in AGENTS.md, ✓ Exists in system-prompts
  - [LANGUAGE]-DOD: ✓ Found in AGENTS.md, ✓ Exists in system-prompts
```

**All sections should show ✓:**
- If any show ✗, the section tags may be malformed
- Check `<!-- SECTION: NAME -->` and `<!-- END-SECTION -->` tags are present

### Step 6.3: Validate Cross-References (Manual Test)

**Test navigation paths:**

1. **From AGENTS.md to docs/:**
   ```bash
   # Extract links from AGENTS.md quick navigation
   grep -A 10 "Quick Navigation:" AGENTS.md

   # Verify each linked file exists
   # Example: docs/definition-of-done.md, docs/architecture.md, etc.
   ```

2. **From docs/ to system-prompts/:**
   ```bash
   # Check definition-of-done.md references Agent Kernel
   grep "system-prompts" docs/definition-of-done.md

   # Should find links to:
   # - system-prompts/principles/definition-of-done.md
   # - system-prompts/languages/[lang]/definition-of-done.md
   ```

3. **From system-prompts back to docs/:**
   ```bash
   # Check system-prompts/README.md references project docs
   grep "docs/definition-of-done.md" docs/system-prompts/README.md
   ```

**All paths should be followable bidirectionally.**

### Step 6.4: Check Naming Conventions

```bash
# Check root entry files use UPPERCASE.md
ls -1 *.md | grep -v "^[A-Z]" && echo "❌ Root files should be UPPERCASE.md" || echo "✓ Root files ok"

# Check docs/ files use lowercase-kebab.md
find docs -maxdepth 1 -name "*.md" ! -name "*-*" ! -name "README.md" | while read f; do
  basename="$(basename "$f")"
  if [[ "$basename" =~ [A-Z] ]]; then
    echo "⚠️  $f should use `lowercase-kebab.md` format"
  fi
done

# Check dev_notes use timestamp format
find dev_notes -name "*.md" ! -name "20*" 2>/dev/null | while read f; do
  echo "⚠️  $f should use `YYYY-MM-DD_HH-MM-SS_description.md` format"
done
```

**Fix any violations found.**

### Step 6.5: Commit Phase 6 Fixes

```bash
# If you fixed broken links or other issues
git add [modified files]

git commit -m "docs: Phase 6 - fix integrity scan issues

- Fixed broken links in [files]
- [Other fixes]

Document integrity scan now passes with 0 errors.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Phase 7: Final Validation and Summary

**Applies to:** Both scenarios
**Goal:** Verify all success criteria met and create completion summary

**For Initial Bootstrap:** Document successful first-time bootstrap
**For Updates:** Document what changed and verify no regressions

### Step 7.1: Final Integrity Scan

```bash
python3 docs/system-prompts/docscan.py 2>&1 | grep -A 20 "VIOLATIONS FOUND"
```

**Expected:**
```
### VIOLATIONS FOUND

⚠️  Warnings (X):
  [non-critical style warnings]
```

**Success:** 0 errors (❌)

### Step 7.2: Verify Success Criteria

Create a checklist:

```markdown
# Bootstrap Integration - Success Criteria

## TODOs Resolved
- [ ] AGENTS.md introduction has project name (not "TODO")
- [ ] docs/workflows.md has content (not "TODO" placeholder)
- [ ] No other critical TODO placeholders in documentation

## Broken Links Fixed
- [ ] All links in AGENTS.md resolve
- [ ] All links in docs/*.md resolve
- [ ] Document integrity scan: 0 errors

## Core Files Created
- [ ] docs/templates.md exists
- [ ] docs/architecture.md exists
- [ ] docs/implementation-reference.md exists
- [ ] docs/README.md exists (documentation hub)

## Duplication Resolved
- [ ] docs/definition-of-done.md is thin wrapper (or doesn't exist)
- [ ] docs/contributing.md references Agent Kernel for generic style
- [ ] No tool-specific guides duplicating system-prompts/tools/

## Cross-References Established
- [ ] AGENTS.md references Agent Kernel sources
- [ ] docs/definition-of-done.md references Agent Kernel
- [ ] docs/system-prompts/README.md has Project Integration section
- [ ] README.md has Documentation section
- [ ] Bidirectional navigation works: AGENTS.md ↔ docs/ ↔ system-prompts/

## Integrity Validated
- [ ] Bootstrap analysis: all sections synchronized
- [ ] Document scan: 0 broken links
- [ ] Cross-references manually tested
- [ ] Naming conventions followed

## Documentation Discoverable
- [ ] All new docs linked from README.md
- [ ] docs/README.md provides navigation
- [ ] AGENTS.md has quick navigation section
```

**Check each item.** If any fail, return to relevant phase and fix.

### Step 7.3: Add Timestamps

```bash
# Add timestamp to all modified files without one
for file in AGENTS.md CLAUDE.md README.md docs/*.md; do
  if [ -f "$file" ]; then
    if ! grep -q "Last Updated:" "$file"; then
      echo -e "\n---\nLast Updated: $(date +%Y-%m-%d)" >> "$file"
      echo "✓ Added timestamp to $file"
    fi
  fi
done
```

### Step 7.4: Create Integration Summary

**Create summary document:** `dev_notes/changes/YYYY-MM-DD_HH-MM-SS_bootstrap-integration-complete.md`

```markdown
# Bootstrap Integration Complete

**Date:** YYYY-MM-DD
**Agent:** [Agent Name]
**Project:** [Project Name]

## Summary

Successfully integrated Agent Kernel (docs/system-prompts/) into project with:

- **TODOs resolved:** X
- **Broken links fixed:** Y
- **Files created:** Z
- **Duplication reduction:** [BEFORE] lines → [AFTER] lines ([PERCENT]%)

## Files Created

1. AGENTS.md - Generated by bootstrap.py
2. docs/templates.md - Template guidelines
3. docs/architecture.md - System architecture
4. docs/implementation-reference.md - Implementation patterns
5. docs/README.md - Documentation navigation hub
[... list all]

## Files Modified

1. docs/definition-of-done.md - Transformed to thin wrapper
2. docs/contributing.md - References Agent Kernel
3. README.md - Added documentation section
[... list all]

## Files Deleted

1. [Any duplicated files removed]

## Verification Results

### Document Integrity Scan
\```
### VIOLATIONS FOUND
❌ Errors (0)
⚠️  Warnings (X)
\```

### Bootstrap Analysis
\```
Sections to sync (3):
  - CORE-WORKFLOW: ✓ Found in AGENTS.md, ✓ Exists in system-prompts
  - PRINCIPLES: ✓ Found in AGENTS.md, ✓ Exists in system-prompts
  - [LANG]-DOD: ✓ Found in AGENTS.md, ✓ Exists in system-prompts
\```

## Success Criteria - All Met ✓

- ✓ All critical TODOs resolved
- ✓ All broken links fixed
- ✓ Core documentation files created
- ✓ Duplication reduced by [X]%
- ✓ Clear content ownership established
- ✓ Cross-references bidirectional
- ✓ Document integrity: 0 errors
- ✓ Bootstrap synchronized
- ✓ All documentation discoverable

## Next Steps

1. Continue development using AGENTS.md workflow
2. Follow definition-of-done.md for quality standards
3. Use templates from docs/templates.md for planning
4. Reference docs/README.md for documentation navigation

Integration complete. Project ready for development.
```

### Step 7.5: Final Commit

```bash
git add dev_notes/changes/[timestamp]_bootstrap-integration-complete.md [any other final changes]

git commit -m "docs: complete Agent Kernel bootstrap integration

All 7 phases completed:
✓ Phase 0: Pre-bootstrap analysis
✓ Phase 1: Run bootstrap
✓ Phase 2: Comprehensive documentation scan
✓ Phase 3: Fix critical TODOs and create core files
✓ Phase 4: Consolidate duplicated content
✓ Phase 5: Establish cross-references
✓ Phase 6: Run integrity processes
✓ Phase 7: Final validation

Final Status:
- TODOs resolved: X
- Broken links fixed: Y
- Files created: Z
- Duplication reduced: [PERCENT]%
- Document integrity: 0 errors
- Bootstrap status: All sections synchronized

Project documentation fully integrated with Agent Kernel.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Common Issues and Solutions

### Issue: Bootstrap fails with "Language not detected"

**Solution:**
```bash
# Manually specify language
python3 docs/system-prompts/bootstrap.py --commit --language python
```

### Issue: AGENTS.md has merge conflicts

**Cause:** AGENTS.md existed before with different content

**Solution:**
1. Backup existing AGENTS.md: `cp AGENTS.md AGENTS.md.backup`
2. Extract project-specific content from backup
3. Run bootstrap: `python3 docs/system-prompts/bootstrap.py --commit`
4. Add project-specific content back to AGENTS.md introduction

### Issue: Too many broken links (>20)

**Strategy:**
1. Focus on critical files first: AGENTS.md, README.md, docs/definition-of-done.md
2. Create missing files in phases (use minimal content initially)
3. Run docscan after each batch of fixes

### Issue: definition-of-done.md is 800+ lines

**Approach:**
1. Use diff to compare with Agent Kernel versions
2. Extract sections NOT in Agent Kernel (project-specific only)
3. Create thin wrapper with extracted sections
4. Target: 200-400 lines (50-80% reduction)

### Issue: Circular references between docs

**Solution:**
- This is usually intentional and ok
- Verify links are helpful and not redundant
- Ensure no infinite loops in navigation

---

## Checklist: Ready to Bootstrap?

Before starting this process, verify:

- [ ] Agent Kernel present in `docs/system-prompts/`
- [ ] Git repository initialized and clean working tree
- [ ] Python 3.8+ available
- [ ] Have 1-2 hours (initial) or 30-60 minutes (updates)
- [ ] Understand project domain (to identify project-specific content)
- [ ] Can commit changes incrementally (7 commits recommended)

**For Initial Bootstrap additionally:**
- [ ] Understand whether core files (architecture.md, etc.) exist
- [ ] Know what project-specific documentation exists

**For Updates additionally:**
- [ ] Review what changed in docs/system-prompts/
- [ ] Prepared to remove redundant content from project docs

**After completion, the project will have:**
- ✓ Clear documentation hierarchy
- ✓ No duplication between project docs and Agent Kernel (or only intentional project-specific extensions)
- ✓ Bidirectional navigation
- ✓ All documentation discoverable
- ✓ Quality standards established
- ✓ AI agents can immediately start following AGENTS.md workflow
- ✓ System-prompts changes successfully integrated (for updates)

---

## Process Metadata

**Version:** 1.1
**Last Updated:** 2026-01-28
**Maintained By:** Agent Kernel
**Used In:** Google Personal MCP Server (reference implementation)

**Process Type:** Flexible integration (initial setup or post-update validation)
**Scenarios:**
- Initial Bootstrap - First-time Agent Kernel integration into new project
- Bootstrap After System-Prompts Updates - Re-validate after system-prompts changes

**Repeatable:** Yes, run after any Agent Kernel update
**Approvals Required:** Human approval before Phase 3 (file creation) recommended for initial bootstrap

---

For questions or issues with this process, refer to the reference implementation commit history in the Google Personal MCP Server project.
